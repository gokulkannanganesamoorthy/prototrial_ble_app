import threading
import logging
from pynput import keyboard

class InputEvent:
    """Standardized event object."""
    def __init__(self, device_id, command):
        self.device_id = device_id
        self.command = command # 'NEXT', 'PLAY_PAUSE', 'PREV'

class MediaKeyListener:
    """
    Listens to global system media keys using pynput.
    This works around macOS HID blocks by letting the OS process the Bluetooth signal
    and catching the resulting media key event.
    """
    def __init__(self, callback):
        self.callback = callback
        self.listener = None
        self.logger = logging.getLogger("MediaKeyListener")
        
    def start(self):
        self.listener = keyboard.Listener(on_press=self._on_press)
        self.listener.start()
        self.logger.info("Started global media key listener.")
        
    def stop(self):
        if self.listener:
            self.listener.stop()

    def _on_press(self, key):
        try:
            if hasattr(key, 'value') and getattr(key, 'value') is not None:
                # pynput media keys often have values depending on platform
                pass
                
            if key == keyboard.Key.space:
                self.callback(InputEvent('GLOBAL', 'SPACE_PLAY_PAUSE'))
            elif key == keyboard.Key.media_next:
                self.callback(InputEvent('GLOBAL', 'NEXT'))
            elif key == keyboard.Key.media_play_pause:
                self.callback(InputEvent('GLOBAL', 'MEDIA_PLAY_PAUSE'))
        except AttributeError:
            pass

def list_hid_devices():
    """Returns an empty list as explicit HID mapping is disabled."""
    return []
