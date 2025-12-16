"""
Plant System Model
Implements the physical plant dynamics from the paper
"""

import numpy as np

class Plant:
    def __init__(self):
        # UAV longitudinal model from paper (Section V)
        self.A = np.array([[0.8825, 0.0987],
                          [-0.8458, 0.9122]])
        self.B = np.array([[-0.0194, -0.0036],
                          [-1.9290, -0.3808]])
        self.C = np.array([[1, 0]])
        self.D = np.zeros((1, 2))
        
        # State initialization
        self.x = np.array([0.0, 0.0])
        
        # Noise parameters
        self.process_noise_cov = 0.001 * np.eye(2)
        self.sensor_noise_cov = 0.01
        
        # Fault parameters
        self.fault_active = False
        self.fault_type = None
        self.fault_magnitude = 0.0
        
    def step(self, u):
        """
        Execute one time step of plant dynamics
        x(k+1) = Ax(k) + Bu(k) + ω(k) + f_p(k)
        y(k) = Cx(k) + Du(k) + η(k) + f_y(k)
        """
        # Process noise
        w = np.random.multivariate_normal(np.zeros(2), self.process_noise_cov)
        
        # Add fault if active
        fault_process = np.zeros(2)
        fault_sensor = 0.0
        
        if self.fault_active:
            if self.fault_type == 'plant':
                fault_process = self.fault_magnitude * np.ones(2)
            elif self.fault_type == 'sensor':
                fault_sensor = self.fault_magnitude
            elif self.fault_type == 'actuator':
                u = u + self.fault_magnitude * np.ones(2)
        
        # State update
        self.x = self.A @ self.x + self.B @ u + w + fault_process
        
        # Measurement noise
        eta = np.random.normal(0, np.sqrt(self.sensor_noise_cov))
        
        # Output
        y = (self.C @ self.x + self.D @ u)[0] + eta + fault_sensor
        
        return y
    
    def set_fault(self, fault_type, magnitude):
        """Inject fault into system"""
        self.fault_active = True
        self.fault_type = fault_type
        self.fault_magnitude = magnitude
    
    def clear_fault(self):
        """Clear active fault"""
        self.fault_active = False
        self.fault_type = None
        self.fault_magnitude = 0.0
    
    def get_state(self):
        """Get current state"""
        return self.x.copy()
    
    def reset(self):
        """Reset plant to initial state"""
        self.x = np.array([0.0, 0.0])
        self.clear_fault()