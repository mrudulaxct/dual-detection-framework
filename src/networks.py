"""
Secure Network Communication Layer
Implements encryption for plant-controller communication
"""

import numpy as np
from cryptography.fernet import Fernet
import json
import base64

class SecureNetwork:
    """
    Secure communication channel between plant and controller
    Implements encryption/decryption for data transmission
    """
    def __init__(self):
        # Generate encryption key
        self.key = Fernet.generate_key()
        self.cipher = Fernet(self.key)
        
        # Attack parameters
        self.attack_active = False
        self.attack_type = None
        self.attack_magnitude = 0.0
        self.attack_history = []
        
        # Network statistics
        self.packets_sent = 0
        self.packets_encrypted = 0
        self.packets_attacked = 0
        
    def encrypt_data(self, data):
        """Encrypt data for transmission"""
        # Convert numpy arrays to JSON-serializable format
        if isinstance(data, np.ndarray):
            data = data.tolist()
        
        # Serialize to JSON
        json_data = json.dumps(data).encode()
        
        # Encrypt
        encrypted = self.cipher.encrypt(json_data)
        self.packets_encrypted += 1
        
        return encrypted
    
    def decrypt_data(self, encrypted_data):
        """Decrypt received data"""
        # Decrypt
        decrypted = self.cipher.decrypt(encrypted_data)
        
        # Deserialize from JSON
        data = json.loads(decrypted.decode())
        
        # Convert back to numpy array if it was an array
        if isinstance(data, list):
            data = np.array(data)
        
        return data
    
    def send_control_signal(self, u):
        """
        Send control signal from controller to plant
        Applies attack if active
        """
        self.packets_sent += 1
        
        # Apply attack if active
        if self.attack_active:
            u_attacked = self._apply_attack(u)
            self.packets_attacked += 1
            return u_attacked
        
        return u
    
    def send_measurement(self, y):
        """
        Send measurement from plant to controller
        Applies attack if active (for sensor attacks)
        """
        self.packets_sent += 1
        
        # Apply attack if active (covert attack on sensor)
        if self.attack_active and self.attack_type == 'covert':
            y_attacked = self._apply_measurement_attack(y)
            self.packets_attacked += 1
            return y_attacked
        
        return y
    
    def _apply_attack(self, u):
        """Apply attack to control signal"""
        u_attacked = u.copy()
        
        if self.attack_type == 'zero_dynamics':
            # Zero-dynamics attack: inject signal in null space
            u_attacked = u + self.attack_magnitude * np.ones(2)
            
        elif self.attack_type == 'covert':
            # Covert attack: inject coordinated signals
            u_attacked = u + self.attack_magnitude * np.ones(2)
            
        elif self.attack_type == 'replay':
            # Replay attack: use stored historical data
            if len(self.attack_history) > 10:
                u_attacked = self.attack_history[-10]
        
        # Store for replay attacks
        self.attack_history.append(u.copy())
        if len(self.attack_history) > 100:
            self.attack_history.pop(0)
        
        return u_attacked
    
    def _apply_measurement_attack(self, y):
        """Apply attack to measurement signal (for covert attacks)"""
        # Covert attack modifies both control and measurement
        # to satisfy: a_y + G_u * a_u = 0
        # Simplified: just add coordinated noise
        y_attacked = y + self.attack_magnitude * np.random.randn()
        return y_attacked
    
    def set_attack(self, attack_type, magnitude):
        """Activate attack"""
        self.attack_active = True
        self.attack_type = attack_type
        self.attack_magnitude = magnitude
        self.attack_history = []
    
    def clear_attack(self):
        """Clear active attack"""
        self.attack_active = False
        self.attack_type = None
        self.attack_magnitude = 0.0
        self.attack_history = []
    
    def get_statistics(self):
        """Get network statistics"""
        return {
            'packets_sent': self.packets_sent,
            'packets_encrypted': self.packets_encrypted,
            'packets_attacked': self.packets_attacked,
            'encryption_rate': self.packets_encrypted / max(1, self.packets_sent),
            'attack_rate': self.packets_attacked / max(1, self.packets_sent)
        }
    
    def reset_statistics(self):
        """Reset network statistics"""
        self.packets_sent = 0
        self.packets_encrypted = 0
        self.packets_attacked = 0