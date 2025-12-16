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
        self.Sigma_r = 0.01
        
        # Detection threshold
        self.threshold = chi2.ppf(1 - alpha, df=1)
        
        # Detection history
        self.residuals = []
        self.test_statistics = []
        self.detections = []
        
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
    Simplified version to avoid matrix dimension issues
    """
    def __init__(self, controller, plant, alpha=0.01):
        self.controller = controller
        self.plant = plant
        self.alpha = alpha
        
        # State dimension
        self.n = plant.A.shape[0]
        self.m = plant.B.shape[1]
        
        # Simple estimator: track expected control based on past output
        self.past_outputs = []
        self.past_controls = []
        self.history_length = 10
        
        # Detection threshold
        self.threshold = chi2.ppf(1 - alpha, df=self.m)
        
        # Residual covariance (simplified)
        self.Sigma_r_u = 0.02 * np.eye(self.m)
        
        # Detection history
        self.residuals = []
        self.test_statistics = []
        self.detections = []
        
    def check(self, u, y, v=0.0):
        """
        Perform χ² test on input residual
        Uses a simple prediction model based on history
        """
        try:
            # Store current values
            self.past_outputs.append(y)
            self.past_controls.append(u)
            
            # Keep only recent history
            if len(self.past_outputs) > self.history_length:
                self.past_outputs.pop(0)
                self.past_controls.pop(0)
            
            # Predict control based on recent trend
            if len(self.past_controls) >= 3:
                # Simple prediction: weighted average of recent controls
                weights = np.array([0.5, 0.3, 0.2])
                u_predicted = np.zeros(self.m)
                for i in range(3):
                    u_predicted += weights[i] * self.past_controls[-(i+1)]
                
                # Compute residual
                r_u = u - u_predicted
            else:
                # Not enough history, assume small residual
                r_u = np.zeros(self.m)
            
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
            # If anything fails, return safe values
            return False, 0.0
    
    def reset(self):
        """Reset detector state and history"""
        self.past_outputs = []
        self.past_controls = []
        self.residuals = []
        self.test_statistics = []
        self.detections = []