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
        
        # Get dimensions
        self.n = self.A.shape[0]  # State dimension
        self.m = self.B.shape[1]  # Input dimension
        self.p = self.C.shape[0]  # Output dimension
        
        # State estimate
        self.x_hat = np.zeros(self.n)
        
        # Design observer (Kalman filter)
        self._design_observer()
        
        # Design controller (LQR)
        self._design_controller()
        
        # Q parameter for residual (set to zero for simplicity)
        self.Q = np.zeros((self.m, self.p))
        
        # Reference input
        self.reference = 0.0
        
    def _design_observer(self):
        """Design Kalman filter observer gain L"""
        try:
            Q = 0.001 * np.eye(self.n)  # Process noise covariance
            R = np.array([[0.01]])  # Measurement noise covariance
            
            # Solve discrete-time algebraic Riccati equation
            P = solve_discrete_are(self.A.T, self.C.T, Q, R)
            
            # Kalman gain - ensure correct shape (n, p)
            self.L = P @ self.C.T @ np.linalg.inv(self.C @ P @ self.C.T + R)
            self.L = self.L.reshape(self.n, self.p)  # Shape: (2, 1)
            
        except Exception as e:
            # Fallback to simple observer
            self.L = np.array([[0.5], [0.5]])
        
    def _design_controller(self):
        """Design LQR controller gain F"""
        try:
            Q = np.eye(self.n)  # State weighting
            R = np.eye(self.m)  # Input weighting
            
            # Solve discrete-time algebraic Riccati equation
            P = solve_discrete_are(self.A, self.B, Q, R)
            
            # LQR gain - shape should be (m, n) = (2, 2)
            self.F = -np.linalg.inv(self.B.T @ P @ self.B + R) @ (self.B.T @ P @ self.A)
            
        except Exception as e:
            # Fallback to simple controller
            self.F = -np.array([[0.3, -0.4], 
                               [0.1, -0.1]])
        
    def update_observer(self, y, u):
        """
        Update observer state estimate
        x̂(k+1) = Ax̂(k) + Bu(k) + L(y(k) - ŷ(k))
        """
        try:
            # Predicted output (scalar)
            y_hat = float(self.C @ self.x_hat + self.D @ u)
            
            # Innovation (residual) - scalar
            innovation = y - y_hat
            
            # State update
            # L is (2, 1), innovation is scalar
            L_times_innov = (self.L * innovation).flatten()
            
            self.x_hat = self.A @ self.x_hat + self.B @ u + L_times_innov
            
            return y_hat, innovation
            
        except Exception as e:
            # Return zeros if update fails
            return y, 0.0
    
    def compute_control(self, y):
        """
        Compute control input
        u(k) = Fx̂(k) + Qr(k) + v̄(k)
        """
        try:
            # Feedback control
            u = self.F @ self.x_hat
            
            # Add reference tracking (simplified)
            u = u + np.array([self.reference, 0])
            
            return u
            
        except Exception as e:
            # Return zero control if computation fails
            return np.zeros(self.m)
    
    def set_reference(self, ref):
        """Set reference input"""
        self.reference = float(ref)
    
    def reset(self):
        """Reset controller state"""
        self.x_hat = np.zeros(self.n)
        self.reference = 0.0