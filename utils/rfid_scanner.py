"""
rfid_scanner.py
---------------
Universal RFID scanner utility for Lab Management System.
Supports any serial-based RFID scanner including ESP32/RC522 setups.

Configuration:
- Default COM port: COM17
- Default baud rate: 9600
- Configurable timeout and retry settings
"""

import serial
import time
import threading
from typing import Callable, Optional
from dataclasses import dataclass


@dataclass
class RFIDScannerConfig:
    """Configuration for RFID scanner connection."""
    port: str = "COM17"
    baud_rate: int = 9600
    timeout: float = 1.0
    retry_attempts: int = 3
    retry_delay: float = 1.0
    read_timeout: float = 0.1


class RFIDScanner:
    """Universal RFID scanner interface for serial-based scanners."""
    
    def __init__(self, config: RFIDScannerConfig = None):
        self.config = config or RFIDScannerConfig()
        self.serial_connection: Optional[serial.Serial] = None
        self.is_scanning = False
        self.scan_thread: Optional[threading.Thread] = None
        self.on_scan_callback: Optional[Callable[[str], None]] = None
        self._stop_scanning = threading.Event()
        
    def connect(self) -> bool:
        """Establish connection to RFID scanner."""
        for attempt in range(self.config.retry_attempts):
            try:
                self.serial_connection = serial.Serial(
                    port=self.config.port,
                    baudrate=self.config.baud_rate,
                    timeout=self.config.timeout
                )
                
                # Test connection by checking if port is open
                if self.serial_connection.is_open:
                    print(f"✅ RFID Scanner connected on {self.config.port}")
                    return True
                    
            except serial.SerialException as e:
                print(f"⚠ Connection attempt {attempt + 1}/{self.config.retry_attempts} failed: {e}")
                if attempt < self.config.retry_attempts - 1:
                    time.sleep(self.config.retry_delay)
                    
        print(f"❌ Failed to connect to RFID scanner on {self.config.port}")
        return False
    
    def disconnect(self):
        """Close connection to RFID scanner."""
        self.stop_scanning()
        if self.serial_connection and self.serial_connection.is_open:
            try:
                self.serial_connection.close()
                print("🔌 RFID Scanner disconnected")
            except Exception as e:
                print(f"⚠ Warning during disconnect: {e}")
        
        # Reset connection state
        self.serial_connection = None
    
    def is_connected(self) -> bool:
        """Check if scanner is connected and ready."""
        return (self.serial_connection is not None and 
                self.serial_connection.is_open)
    
    def read_single_scan(self) -> Optional[str]:
        """Read a single RFID scan synchronously."""
        if not self.is_connected():
            return None
            
        try:
            # Clear any existing data in buffer
            self.serial_connection.reset_input_buffer()
            
            # Wait for data with timeout
            start_time = time.time()
            while time.time() - start_time < self.config.timeout:
                if self.serial_connection.in_waiting > 0:
                    data = self.serial_connection.readline()
                    if data:
                        rfid_uid = data.decode('utf-8').strip()
                        if rfid_uid:  # Ensure we got actual data
                            print(f"📱 RFID Scanned: {rfid_uid}")
                            return rfid_uid
                time.sleep(self.config.read_timeout)
                
        except Exception as e:
            print(f"⚠ Error reading RFID: {e}")
            
        return None
    
    def start_continuous_scanning(self, callback: Callable[[str], None]):
        """Start continuous scanning in background thread."""
        if self.is_scanning:
            print("⚠ Scanner is already running")
            return False
            
        if not self.is_connected():
            if not self.connect():
                return False
                
        self.on_scan_callback = callback
        self.is_scanning = True
        self._stop_scanning.clear()
        
        self.scan_thread = threading.Thread(target=self._scan_loop, daemon=True)
        self.scan_thread.start()
        
        print("🔄 Continuous RFID scanning started")
        return True
    
    def stop_scanning(self):
        """Stop continuous scanning."""
        if self.is_scanning:
            self._stop_scanning.set()
            self.is_scanning = False
            
            if self.scan_thread and self.scan_thread.is_alive():
                self.scan_thread.join(timeout=2.0)
                
            # Small delay to ensure clean shutdown
            time.sleep(0.1)
            print("⏹ RFID scanning stopped")
    
    def _scan_loop(self):
        """Background scanning loop."""
        while not self._stop_scanning.is_set() and self.is_connected():
            try:
                rfid_uid = self.read_single_scan()
                if rfid_uid and self.on_scan_callback:
                    # Call callback in main thread safe way
                    self.on_scan_callback(rfid_uid)
                    
            except Exception as e:
                print(f"⚠ Error in scan loop: {e}")
                time.sleep(0.5)  # Brief pause on error
                
        print("🔄 Scan loop ended")


class RFIDScannerManager:
    """Singleton manager for RFID scanner instance."""
    
    _instance: Optional[RFIDScanner] = None
    _config: Optional[RFIDScannerConfig] = None
    
    @classmethod
    def get_scanner(cls, config: RFIDScannerConfig = None) -> RFIDScanner:
        """Get or create the global RFID scanner instance."""
        if cls._instance is None or config != cls._config:
            if cls._instance:
                cls._instance.disconnect()
            cls._config = config or RFIDScannerConfig()
            cls._instance = RFIDScanner(cls._config)
        return cls._instance
    
    @classmethod
    def cleanup(cls):
        """Clean up the scanner instance."""
        if cls._instance:
            cls._instance.disconnect()
            cls._instance = None
            cls._config = None


# Convenience functions for easy integration
def quick_scan(port: str = "COM17", timeout: float = 5.0) -> Optional[str]:
    """Quick single RFID scan with default settings."""
    config = RFIDScannerConfig(port=port, timeout=timeout)
    scanner = RFIDScanner(config)
    
    if scanner.connect():
        result = scanner.read_single_scan()
        scanner.disconnect()
        return result
    return None


def test_scanner_connection(port: str = "COM17") -> bool:
    """Test if RFID scanner is available on specified port."""
    config = RFIDScannerConfig(port=port)
    scanner = RFIDScanner(config)
    
    connected = scanner.connect()
    if connected:
        scanner.disconnect()
    return connected


# Example usage and testing
if __name__ == "__main__":
    def on_rfid_scan(rfid_uid: str):
        print(f"🎯 RFID Detected: {rfid_uid}")
    
    # Test connection
    print("Testing RFID scanner connection...")
    if test_scanner_connection():
        print("✅ Scanner connection test passed")
        
        # Test single scan
        print("\nTesting single scan (5 second timeout)...")
        result = quick_scan(timeout=5.0)
        if result:
            print(f"✅ Single scan successful: {result}")
        else:
            print("⚠ No RFID detected in timeout period")
            
        # Test continuous scanning
        print("\nTesting continuous scanning (press Ctrl+C to stop)...")
        scanner = RFIDScannerManager.get_scanner()
        if scanner.start_continuous_scanning(on_rfid_scan):
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                print("\n🛑 Stopping scanner...")
                scanner.stop_scanning()
                
    else:
        print("❌ Scanner connection test failed")
        print("Check that your RFID scanner is connected to COM17")
