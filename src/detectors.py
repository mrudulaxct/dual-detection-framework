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
        C = self.controller.C
        L = self.controller.L
        A = self.controller.A
        
        # Simplified residual covariance (assuming steady-state)
        P = 0.01 * np.eye(2)  # Steady-state error covariance
        self.Sigma_r = (C @ P @ C.T + 0.01)[0, 0]
        
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
        
        # Controller model for input estimation
        self.A_bar = controller.A + controller.B @ controller.F - controller.B @ controller.Q @ controller.C - controller.L @ controller.C
        self.B_bar = np.hstack([controller.L + controller.B @ controller.Q, controller.B])
        self.C_bar = controller.F - controller.Q @ controller.C
        self.D_bar = np.hstack([controller.Q, np.eye(2)])
        
        # Input estimator state
        self.x_u_hat = np.array([0.0, 0.0])
        
        # Design estimator gain (simplified)
        self._design_estimator()
        
        # Detection threshold
        self.threshold = chi2.ppf(1 - alpha, df=2)
        
        # Detection history
        self.residuals = []
        self.test_statistics = []
        self.detections = []
        
    def _design_estimator(self):
        """Design input estimator gain L_u"""
        # Simplified design - could use Kalman filter approach
        Q = 0.001 * np.eye(2)
        R = 0.01 * np.eye(2)
        
        # For simplicity, use static gain
        self.L_u = np.array([[0.5, 0], [0, 0.5]])
        
        # Residual covariance
        self.Sigma_r_u = 0.01 * np.eye(2)
        
    def update_estimator(self, y, u, v):
        """
        Update input estimator
        x̂_u(k+1) = Ā x̂_u(k) + B̄[y(k), v(k)]ᵀ + L_u(u(k) - û(k))
        """
        # Predicted input
        y_bar = np.array([y, v])
        u_hat = self.C_bar @ self.x_u_hat + (self.D_bar @ y_bar)
        
        # Residual
        r_u = u - u_hat
        
        # State update
        self.x_u_hat = self.A_bar @ self.x_u_hat + self.B_bar @ y_bar + (self.L_u @ r_u).flatten()
        
        return r_u
    
    def check(self, u, y, v=0.0):
        """
        Perform χ² test on input residual
        J_u(k) = r_u(k)ᵀ Σ_r_u⁻¹ r_u(k)
        """
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
    
    def reset(self):
        """Reset detector state and history"""
        self.x_u_hat = np.array([0.0, 0.0])
        self.residuals = []
        self.test_statistics = []
        self.detections = []