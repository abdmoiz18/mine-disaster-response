"""
LoRa RA-02 SX1278 Receiver for Mine Disaster Response
Receives miner data via LoRa and forwards to main_final. py via UDP
"""
import time
import json
import socket
import RPi.GPIO as GPIO
import spidev

# Pin Configuration (BCM numbering)
PIN_NSS = 8      # SPI CS
PIN_RST = 22     # Reset
PIN_DIO0 = 4     # Interrupt

# LoRa Configuration
FREQUENCY = 433E6  # 433 MHz (check your module's frequency)
BANDWIDTH = 125E3
SPREADING_FACTOR = 7
CODING_RATE = 5

# UDP Configuration (forward to main_final. py)
UDP_IP = "127.0.0. 1"
UDP_PORT = 5000

# SX1278 Registers
REG_FIFO = 0x00
REG_OP_MODE = 0x01
REG_FRF_MSB = 0x06
REG_FRF_MID = 0x07
REG_FRF_LSB = 0x08
REG_PA_CONFIG = 0x09
REG_FIFO_ADDR_PTR = 0x0D
REG_FIFO_RX_BASE_ADDR = 0x0F
REG_IRQ_FLAGS = 0x12
REG_RX_NB_BYTES = 0x13
REG_MODEM_CONFIG_1 = 0x1D
REG_MODEM_CONFIG_2 = 0x1E
REG_PAYLOAD_LENGTH = 0x22
REG_DIO_MAPPING_1 = 0x40
REG_VERSION = 0x42

# Modes
MODE_SLEEP = 0x00
MODE_STDBY = 0x01
MODE_TX = 0x03
MODE_RX_CONTINUOUS = 0x05
MODE_LORA = 0x80

class LoRaReceiver:
    def __init__(self):
        # Setup GPIO
        GPIO. setmode(GPIO. BCM)
        GPIO.setwarnings(False)
        GPIO.setup(PIN_NSS, GPIO. OUT)
        GPIO.setup(PIN_RST, GPIO. OUT)
        GPIO.setup(PIN_DIO0, GPIO.IN)
        
        # Setup SPI
        self.spi = spidev.SpiDev()
        self.spi.open(0, 0)
        self.spi.max_speed_hz = 5000000
        
        # Setup UDP socket
        self.sock = socket.socket(socket.AF_INET, socket. SOCK_DGRAM)
        
        # Initialize LoRa
        self._reset()
        self._init_lora()
        
    def _reset(self):
        """Hardware reset the module."""
        GPIO.output(PIN_RST, GPIO.LOW)
        time. sleep(0.01)
        GPIO. output(PIN_RST, GPIO.HIGH)
        time. sleep(0.01)
        
    def _write_register(self, address, value):
        """Write to a register."""
        GPIO.output(PIN_NSS, GPIO. LOW)
        self.spi.xfer2([address | 0x80, value])
        GPIO. output(PIN_NSS, GPIO.HIGH)
        
    def _read_register(self, address):
        """Read from a register."""
        GPIO.output(PIN_NSS, GPIO.LOW)
        response = self.spi.xfer2([address & 0x7F, 0x00])
        GPIO.output(PIN_NSS, GPIO.HIGH)
        return response[1]
    
    def _init_lora(self):
        """Initialize LoRa module."""
        # Check version
        version = self._read_register(REG_VERSION)
        if version != 0x12:
            raise Exception(f"Invalid LoRa version: {version}. Check wiring!")
        print(f"  LoRa chip version: 0x{version:02X}")
        
        # Set sleep mode
        self._write_register(REG_OP_MODE, MODE_SLEEP | MODE_LORA)
        time.sleep(0.01)
        
        # Set frequency (433 MHz)
        frf = int((FREQUENCY / 32000000) * 524288)
        self._write_register(REG_FRF_MSB, (frf >> 16) & 0xFF)
        self._write_register(REG_FRF_MID, (frf >> 8) & 0xFF)
        self._write_register(REG_FRF_LSB, frf & 0xFF)
        
        # Set modem config
        self._write_register(REG_MODEM_CONFIG_1, 0x72)  # BW=125kHz, CR=4/5
        self._write_register(REG_MODEM_CONFIG_2, (SPREADING_FACTOR << 4) | 0x04)
        
        # Set PA config (max power)
        self._write_register(REG_PA_CONFIG, 0x8F)
        
        # Set FIFO base addresses
        self._write_register(REG_FIFO_RX_BASE_ADDR, 0x00)
        
        # Set DIO0 to RxDone
        self._write_register(REG_DIO_MAPPING_1, 0x00)
        
        print("  LoRa module initialized")
        
    def start_receive(self):
        """Start continuous receive mode."""
        self._write_register(REG_OP_MODE, MODE_LORA | MODE_RX_CONTINUOUS)
        print("  LoRa listening...")
        
    def check_for_packet(self):
        """Check if a packet has been received."""
        irq_flags = self._read_register(REG_IRQ_FLAGS)
        
        # RxDone flag
        if irq_flags & 0x40:
            # Clear IRQ flags
            self._write_register(REG_IRQ_FLAGS, 0xFF)
            
            # Check for CRC error
            if irq_flags & 0x20:
                print("  CRC error, packet discarded")
                return None
            
            # Read packet
            packet_length = self._read_register(REG_RX_NB_BYTES)
            self._write_register(REG_FIFO_ADDR_PTR, 0x00)
            
            packet = []
            for _ in range(packet_length):
                packet.append(self._read_register(REG_FIFO))
            
            return bytes(packet)
        
        return None
    
    def forward_to_gateway(self, data):
        """Forward received data to main_final.py via UDP."""
        try:
            self.sock.sendto(data, (UDP_IP, UDP_PORT))
            print(f"  Forwarded to gateway: {len(data)} bytes")
        except Exception as e:
            print(f"  UDP forward error: {e}")
    
    def run(self):
        """Main receive loop."""
        print("=" * 60)
        print("LoRa Receiver - Mine Disaster Response")
        print("=" * 60)
        print(f"  Frequency: {FREQUENCY/1E6} MHz")
        print(f"  Forwarding to: {UDP_IP}:{UDP_PORT}")
        print("=" * 60)
        
        self.start_receive()
        
        try:
            while True:
                packet = self.check_for_packet()
                
                if packet:
                    try:
                        # Decode and parse JSON
                        message = packet.decode('utf-8')
                        print(f"\n[RECEIVED] {message[:50]}...")
                        
                        # Validate JSON
                        data = json.loads(message)
                        
                        # Forward to main_final. py
                        self.forward_to_gateway(packet)
                        
                    except json.JSONDecodeError:
                        print(f"  Invalid JSON: {packet}")
                    except UnicodeDecodeError:
                        print(f"  Invalid UTF-8: {packet. hex()}")
                
                time.sleep(0.01)  # Small delay to prevent CPU overload
                
        except KeyboardInterrupt:
            print("\nShutting down...")
        finally:
            self. cleanup()
    
    def cleanup(self):
        """Cleanup GPIO and SPI."""
        self._write_register(REG_OP_MODE, MODE_SLEEP | MODE_LORA)
        self.spi.close()
        GPIO.cleanup()
        self.sock.close()
        print("LoRa receiver stopped.")

if __name__ == "__main__":
    receiver = LoRaReceiver()
    receiver.run()
