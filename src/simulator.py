"""
System Simulator
Coordinates all components and executes simulation steps
"""

import numpy as np
import time

class SystemSimulator:
    def __init__(self, plant, controller, fault_detector, attack_detector, network, database):
        self.plant = plant
        self.controller = controller
        self.fault_detector = fault_detector
        self.attack_detector = attack_detector
        self.network = network
        self.db = database
        
        self.time = 0
        self.step_count = 0
        self.start_time = time.time()
        
    def step(self):
        """Execute one simulation step"""
        # Get current measurement from plant
        y = self.plant.C @ self.plant.get_state()
        
        # Send measurement through network (may be attacked)
        y_transmitted = self.network.send_measurement(y[0])
        
        # Encrypt measurement for transmission
        y_encrypted = self.network.encrypt_data(y_transmitted)
        
        # Decrypt at controller side
        y_received = self.network.decrypt_data(y_encrypted)
        
        # Update controller observer and get residual
        y_hat, residual = self.controller.update_observer(y_received, 
                                                          self.controller.F @ self.controller.x_hat)
        
        # Compute control signal
        u = self.controller.compute_control(y_received)
        
        # Send control through network (may be attacked)
        u_transmitted = self.network.send_control_signal(u)
        
        # Encrypt control signal
        u_encrypted = self.network.encrypt_data(u_transmitted)
        
        # Decrypt at plant side
        u_received = self.network.decrypt_data(u_encrypted)
        
        # Apply control to plant
        y_next = self.plant.step(u_received)
        
        # Fault detection (controller side)
        fault_detected, fault_stat = self.fault_detector.check(residual)
        
        # Attack detection (plant side)
        attack_detected, attack_stat = self.attack_detector.check(u_received, y_received, 0.0)
        
        # Determine anomaly type
        anomaly_type = self._classify_anomaly(fault_detected, attack_detected)
        
        # Save data to database
        self.db.save_system_data(
            self.time,
            self.plant.get_state(),
            y_received,
            u_received,
            self.controller.reference
        )
        
        self.db.save_detection_results(
            self.time,
            fault_stat,
            fault_detected,
            attack_stat,
            attack_detected,
            anomaly_type
        )
        
        # Periodically save network stats
        if self.step_count % 100 == 0:
            self.db.save_network_stats(self.time, self.network.get_statistics())
        
        # Increment time
        self.time += 0.1  # 0.1s sampling time
        self.step_count += 1
        
        # Prepare results for transmission
        results = {
            'time': float(self.time),
            'state': self.plant.get_state().tolist(),
            'output': float(y_received),
            'control': u_received.tolist(),
            'reference': float(self.controller.reference),
            'fault_detector': {
                'residual': float(residual),
                'statistic': float(fault_stat),
                'detected': bool(fault_detected),
                'threshold': float(self.fault_detector.threshold)
            },
            'attack_detector': {
                'statistic': float(attack_stat),
                'detected': bool(attack_detected),
                'threshold': float(self.attack_detector.threshold)
            },
            'anomaly_type': anomaly_type,
            'network': self.network.get_statistics(),
            'active_fault': self.plant.fault_active,
            'active_attack': self.network.attack_active
        }
        
        return results
    
    def _classify_anomaly(self, fault_detected, attack_detected):
        """
        Classify anomaly type based on dual detector response
        From paper Section IV-A
        """
        if fault_detected and attack_detected:
            return "Fault and Attack"
        elif attack_detected and not fault_detected:
            return "Kernel Attack"
        elif fault_detected and not attack_detected:
            return "System Fault"
        else:
            return "Normal"
    
    def inject_fault(self, fault_type, magnitude):
        """Inject fault into system"""
        self.plant.set_fault(fault_type, magnitude)
        self.db.save_anomaly_event(
            self.time,
            'fault',
            magnitude,
            f'{fault_type} fault injected with magnitude {magnitude}'
        )
    
    def inject_attack(self, attack_type, magnitude):
        """Inject cyber attack"""
        self.network.set_attack(attack_type, magnitude)
        self.db.save_anomaly_event(
            self.time,
            'attack',
            magnitude,
            f'{attack_type} attack injected with magnitude {magnitude}'
        )
    
    def clear_anomalies(self):
        """Clear all active anomalies"""
        self.plant.clear_fault()
        self.network.clear_attack()
        self.db.save_anomaly_event(
            self.time,
            'clear',
            0.0,
            'All anomalies cleared'
        )
    
    def set_reference(self, value):
        """Set reference input"""
        self.controller.set_reference(value)
    
    def reset(self):
        """Reset entire system"""
        self.plant.reset()
        self.controller.reset()
        self.fault_detector.reset()
        self.attack_detector.reset()
        self.network.clear_attack()
        self.time = 0
        self.step_count = 0