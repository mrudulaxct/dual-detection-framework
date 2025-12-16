"""
System Simulator
Coordinates all components and executes simulation steps
"""

import numpy as np
import time
import traceback

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
        
        # Store last valid control for fallback
        self.last_u = np.zeros(2)
        
    def step(self):
        """Execute one simulation step"""
        try:
            # Get current measurement from plant
            y = float((self.plant.C @ self.plant.get_state())[0])
            
            # Send measurement through network (may be attacked)
            y_transmitted = self.network.send_measurement(y)
            
            # Encrypt measurement for transmission
            try:
                y_encrypted = self.network.encrypt_data(y_transmitted)
                y_received = self.network.decrypt_data(y_encrypted)
            except:
                y_received = y_transmitted
            
            # Compute control signal first
            u = self.controller.compute_control(y_received)
            
            # Ensure u is valid
            if not isinstance(u, np.ndarray) or u.shape != (2,):
                u = self.last_u
            else:
                self.last_u = u.copy()
            
            # Update controller observer and get residual
            try:
                y_hat, residual = self.controller.update_observer(y_received, u)
            except Exception as e:
                y_hat = y_received
                residual = 0.0
            
            # Send control through network (may be attacked)
            u_transmitted = self.network.send_control_signal(u)
            
            # Encrypt control signal
            try:
                u_encrypted = self.network.encrypt_data(u_transmitted)
                u_received = self.network.decrypt_data(u_encrypted)
            except:
                u_received = u_transmitted
            
            # Apply control to plant
            y_next = self.plant.step(u_received)
            
            # Fault detection (controller side)
            try:
                fault_detected, fault_stat = self.fault_detector.check(residual)
            except Exception as e:
                fault_detected, fault_stat = False, 0.0
            
            # Attack detection (plant side)
            try:
                attack_detected, attack_stat = self.attack_detector.check(u_received, y_received, 0.0)
            except Exception as e:
                attack_detected, attack_stat = False, 0.0
            
            # Determine anomaly type
            anomaly_type = self._classify_anomaly(fault_detected, attack_detected)
            
            # Save data to database
            try:
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
            except Exception as e:
                pass  # Continue even if database save fails
            
            # Periodically save network stats
            if self.step_count % 100 == 0:
                try:
                    self.db.save_network_stats(self.time, self.network.get_statistics())
                except:
                    pass
            
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
            
        except Exception as e:
            # If step fails completely, return safe defaults
            print(f"ERROR in simulation step: {e}")
            traceback.print_exc()
            
            return {
                'time': float(self.time),
                'state': [0.0, 0.0],
                'output': 0.0,
                'control': [0.0, 0.0],
                'reference': 0.0,
                'fault_detector': {
                    'residual': 0.0,
                    'statistic': 0.0,
                    'detected': False,
                    'threshold': 6.63
                },
                'attack_detector': {
                    'statistic': 0.0,
                    'detected': False,
                    'threshold': 9.21
                },
                'anomaly_type': 'Normal',
                'network': {'packets_sent': 0, 'packets_encrypted': 0, 'packets_attacked': 0},
                'active_fault': False,
                'active_attack': False
            }
    
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
        try:
            self.db.save_anomaly_event(
                self.time,
                'fault',
                magnitude,
                f'{fault_type} fault injected with magnitude {magnitude}'
            )
        except:
            pass
    
    def inject_attack(self, attack_type, magnitude):
        """Inject cyber attack"""
        self.network.set_attack(attack_type, magnitude)
        try:
            self.db.save_anomaly_event(
                self.time,
                'attack',
                magnitude,
                f'{attack_type} attack injected with magnitude {magnitude}'
            )
        except:
            pass
    
    def clear_anomalies(self):
        """Clear all active anomalies"""
        self.plant.clear_fault()
        self.network.clear_attack()
        try:
            self.db.save_anomaly_event(
                self.time,
                'clear',
                0.0,
                'All anomalies cleared'
            )
        except:
            pass
    
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