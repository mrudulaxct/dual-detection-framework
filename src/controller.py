"""
Controller System
Implements observer-based feedback control from paper (Section II)
"""

import numpy as np
from scipy.linalg import solve_discrete_are

class Controller:
    def __init__(self, plant):
        self.plant = plant
        
        # System matrices
        self.A = plant.A
        self.B = plant.B
        self.C = plant.C
        self.D = plant.D
        
        # State estimate
        self.x_hat = np.array([0.0, 0.0])
        
        # Design observer (Kalman filter)
        self._design_observer()
        
        # Design controller (LQR)
        self._design_controller()
        
        # Reference input
        self.reference = 0.0
        
    def _design_observer(self):
        """Design Kalman filter observer gain L"""
        Q = 0.001 * np.eye(2)  # Process noise covariance
        R = np.array([[0.01]])  # Measurement noise covariance
        
        # Solve discrete-time algebraic Riccati equation
        P = solve_discrete_are(self.A.T, self.C.T, Q, R)
        
        # Kalman gain
        self.L = P @ self.C.T @ np.linalg.inv(self.C @ P @ self.C.T + R)
        
    def _design_controller(self):
        """Design LQR controller gain F"""
        Q = np.eye(2)  # State weighting
        R = np.eye(2)  # Input weighting
        
        # Solve discrete-time algebraic Riccati equation
        P = solve_discrete_are(self.A, self.B, Q, R)
        
        # LQR gain
        self.F = -np.linalg.inv(self.B.T @ P @ self.B + R) @ (self.B.T @ P @ self.A)
        
        # Q parameter for residual (set to zero for simplicity)
        self.Q = np.zeros((2, 1))
        
    def update_observer(self, y, u):
        """
        Update observer state estimate
        x̂(k+1) = Ax̂(k) + Bu(k) + L(y(k) - ŷ(k))
        """
        # Predicted output
        y_hat = (self.C @ self.x_hat + self.D @ u)[0]
        
        # Innovation (residual)
        innovation = y - y_hat
        
        # State update
        self.x_hat = self.A @ self.x_hat + self.B @ u + (self.L * innovation).flatten()
        
        return y_hat, innovation
    
    def compute_control(self, y):
        """
        Compute control input
        u(k) = Fx̂(k) + Qr(k) + v̄(k)
        """
        # Feedback control
        u = self.F @ self.x_hat
        
        # Add reference tracking (simplified)
        u = u + np.array([self.reference, 0])
        
        return u
    
    def set_reference(self, ref):
        """Set reference input"""
        self.reference = ref
    
    def reset(self):
        """Reset controller state"""
        self.x_hat = np.array([0.0, 0.0])
        self.reference = 0.0