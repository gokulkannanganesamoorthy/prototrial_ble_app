import hid
import threading
import time
import logging
from pynput import keyboard

# Constants for Consumer Control Usage Page (0x0C)
USAGE_PAGE_CONSUMER = 0x0C
USAGE_PLAY_PAUSE = 0xCD # Play/Pause
USAGE_SCAN_NEXT = 0xB5  # Scan Next Track
USAGE_SCAN_PREV = 0xB6  # Scan Previous Track

class InputEvent:
    """Standardized event object."""
    def __init__(self, device_id, command):
        self.device_id = device_id
        self.command = command # 'NEXT', 'PLAY_PAUSE', 'PREV'

class HIDListener:
    """
    Monitors a specific HID device for media keys.
    Requires device_path/info from hid.enumerate().
    """
    def __init__(self, device_info, callback):
        self.device_info = device_info
        self.callback = callback
        self.stop_event = threading.Event()
        self.device = None
        self.logger = logging.getLogger(f"HIDListener-{device_info['product_string']}")
        
    def start(self):
        self.thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.thread.start()

    def stop(self):
        self.stop_event.set()

    def _monitor_loop(self):
        try:
            self.device = hid.device()
            self.device.open_path(self.device_info['path'])
            self.device.set_nonblocking(True)
            self.logger.info(f"Opened HID device: {self.device_info['product_string']}")
            
            while not self.stop_event.is_set():
                # Read 64 bytes (standard report size often)
                data = self.device.read(64)
                if data:
                    self._parse_report(data)
                time.sleep(0.05)
                
        except Exception as e:
            self.logger.error(f"HID Monitor Error: {e}")
        finally:
            if self.device:
                self.device.close()

    def _parse_report(self, data):
        # NOTE: HID parsing for Consumer usage page is complex and varies by device.
        # This is a simplified check for common patterns. 
        # Often the usage ID is sent in the report.
        # Data often looks like [ReportID, Usage_Byte_1, Usage_Byte_2...]
        # We'll look for our target play/next codes content in the raw bytes.
        
        # Simple heuristic search for values
        if USAGE_SCAN_NEXT in data:
            self.callback(InputEvent(self.device_info['path'], 'NEXT'))
        elif USAGE_PLAY_PAUSE in data:
            self.callback(InputEvent(self.device_info['path'], 'PLAY_PAUSE'))

class GlobalListener:
    """
    Fallback: Listens to global system media keys.
    Cannot differentiate devices, so maps to a 'GLOBAL' device_id.
    """
    def __init__(self, callback):
        self.callback = callback
        self.listener = None
        
    def start(self):
        self.listener = keyboard.Listener(on_press=self._on_press)
        self.listener.start()
        
    def stop(self):
        if self.listener:
            self.listener.stop()

    def _on_press(self, key):
        try:
            if key == keyboard.Key.media_next:
                self.callback(InputEvent('GLOBAL', 'NEXT'))
            elif key == keyboard.Key.media_play_pause:
                self.callback(InputEvent('GLOBAL', 'PLAY_PAUSE'))
        except AttributeError:
            pass

def list_hid_devices():
    """Returns list of potential media control devices."""
    devices = []
    try:
        all_devs = hid.enumerate()
        for d in all_devs:
            # Usage Page 0xC (12) is Consumer, often used for headsets
            if d['usage_page'] == 12 or d['usage_page'] == 0: 
                # (0 usage page is sometimes reported on Windows for composite devs)
                devices.append(d)
    except Exception as e:
        logging.error(f"Failed to enumerate HID: {e}")
    return devices
