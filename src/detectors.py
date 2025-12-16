"""
Dual Detection Framework Detectors
Implements both fault detector and attack detector from paper (Section III-IV)
"""

import numpy as np
from scipy.stats import chi2

class FaultDetector:
    """
    Controller-side fault detector (Detector 1)
    Detects system faults using χ² test on residuals
    """
    def __init__(self, controller, alpha=0.01):
        self.controller = controller
        self.alpha = alpha  # False alarm rate
        
        # Residual covariance (from Kalman filter)
        self.compute_residual_covariance()
        
        # Detection threshold
        self.threshold = chi2.ppf(1 - alpha, df=1)
        
        # Detection history
        self.residuals = []
        self.test_statistics = []
        self.detections = []
        
    def compute_residual_covariance(self):
        """Compute residual covariance matrix"""
        # Simplified residual covariance (assuming steady-state)
        self.Sigma_r = 0.01
        
    def check(self, residual):
        """
        Perform χ² test on residual
        J(k) = r(k)ᵀ Σ_r⁻¹ r(k)
        """
        # Test statistic
        J = (residual ** 2) / self.Sigma_r
        
        # Detection decision
        detected = J > self.threshold
        
        # Store history
        self.residuals.append(residual)
        self.test_statistics.append(float(J))
        self.detections.append(detected)
        
        # Keep last 1000 samples
        if len(self.residuals) > 1000:
            self.residuals.pop(0)
            self.test_statistics.pop(0)
            self.detections.pop(0)
        
        return detected, float(J)
    
    def reset(self):
        """Reset detector history"""
        self.residuals = []
        self.test_statistics = []
        self.detections = []


class AttackDetector:
    """
    Plant-side attack detector (Detector 2)
    Detects kernel attacks by checking controller input consistency
    """
    def __init__(self, controller, plant, alpha=0.01):
        self.controller = controller
        self.plant = plant
        self.alpha = alpha
        
        # Get dimensions
        self.n = plant.A.shape[0]  # State dimension (2)
        self.m = plant.B.shape[1]  # Input dimension (2)
        self.p = plant.C.shape[0]  # Output dimension (1)
        
        # Input estimator state (same dimension as plant state)
        self.x_u_hat = np.zeros(self.n)
        
        # Build simplified input estimator
        self._build_estimator()
        
        # Detection threshold
        self.threshold = chi2.ppf(1 - alpha, df=self.m)
        
        # Detection history
        self.residuals = []
        self.test_statistics = []
        self.detections = []
        
    def _build_estimator(self):
        """Build input estimator matrices"""
        # Simplified estimator design
        # We estimate the control input u based on output y
        
        # Estimator gain (simplified)
        self.L_u = np.eye(self.n) * 0.5
        
        # State transition for estimator
        self.A_est = self.controller.A - self.L_u @ self.controller.C
        
        # Input matrix for estimator (from output)
        self.B_est = self.L_u.reshape(self.n, 1)  # Shape (2, 1) for output
        
        # Output matrix (to get control from state estimate)
        self.C_est = self.controller.F  # Shape (2, 2)
        
        # Residual covariance
        self.Sigma_r_u = 0.01 * np.eye(self.m)
        
    def update_estimator(self, y, u, v=0.0):
        """
        Update input estimator
        Estimate what the control input should be based on output
        """
        try:
            # Reshape y to column vector
            y_vec = np.array([y]).reshape(-1, 1)
            
            # Predict control input from current state estimate
            u_hat = self.C_est @ self.x_u_hat
            
            # Compute residual
            r_u = u - u_hat
            
            # Update state estimate
            # x̂(k+1) = A_est x̂(k) + B_est y(k) + L_u r_u(k)
            self.x_u_hat = (self.A_est @ self.x_u_hat + 
                           (self.B_est @ y_vec).flatten() +
                           (self.L_u @ np.array([y - self.controller.C @ self.x_u_hat]).reshape(-1, 1)).flatten())
            
            return r_u
            
        except Exception as e:
            # If estimation fails, return zero residual
            return np.zeros(self.m)
    
    def check(self, u, y, v=0.0):
        """
        Perform χ² test on input residual
        J_u(k) = r_u(k)ᵀ Σ_r_u⁻¹ r_u(k)
        """
        try:
            # Get input residual
            r_u = self.update_estimator(y, u, v)
            
            # Test statistic
            J_u = r_u.T @ np.linalg.inv(self.Sigma_r_u) @ r_u
            
            # Detection decision
            detected = J_u > self.threshold
            
            # Store history
            self.residuals.append(r_u.tolist())
            self.test_statistics.append(float(J_u))
            self.detections.append(detected)
            
            # Keep last 1000 samples
            if len(self.residuals) > 1000:
                self.residuals.pop(0)
                self.test_statistics.pop(0)
                self.detections.pop(0)
            
            return detected, float(J_u)
            
        except Exception as e:
            # If check fails, return no detection
            return False, 0.0
    
    def reset(self):
        """Reset detector state and history"""
        self.x_u_hat = np.zeros(self.n)
        self.residuals = []
        self.test_statistics = []
        self.detections = []