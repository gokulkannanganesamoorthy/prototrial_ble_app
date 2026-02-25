import logging
import threading
from .audio_router import AudioChannel, AudioChannel
from .input_monitor import MediaKeyListener, list_hid_devices, InputEvent

class Orchestrator:
    """
    binds inputs to audio outputs.
    """
    def __init__(self):
        self.channels = {} # {id: AudioChannel}
        self.last_active_channel_id = None
        self.media_listener = MediaKeyListener(self._handle_input)
        self.logger = logging.getLogger("Orchestrator")
        
        # Start Keyboard Hook
        self.media_listener.start()

    def add_channel(self, channel_id, device_index):
        """Creates a new audio channel mapped to a sound device."""
        try:
            channel = AudioChannel(device_index, channel_name=f"Channel-{channel_id}")
            self.channels[channel_id] = channel
            self.logger.info(f"Created Channel {channel_id} on Device {device_index}")
            
            # Attempt to auto-bind input
            self._auto_bind_input(channel_id, channel.device_name)
            
            return channel
        except Exception as e:
            self.logger.error(f"Failed to create channel: {e}")
            return None

    def _auto_bind_input(self, channel_id, audio_device_name):
        pass

    def map_input(self, input_path, channel_id):
        pass

    def get_input_devices(self):
        return []

    def start_hid_monitoring(self):
        pass

    def _handle_input(self, event: InputEvent):
        """Callback for global input events."""
        self.logger.info(f"Input received: {event.command}")
        
        # Hard route based on device matching instead of UI focus
        for channel in self.channels.values():
            if channel.is_playing or channel.is_paused:
                dev_name = channel.device_name.lower()
                
                # Route Mac Keyboard Spacebar to Built-in Speakers
                if event.command == 'SPACE_PLAY_PAUSE' and ('speaker' in dev_name or 'built-in' in dev_name or 'macbook' in dev_name):
                    channel.toggle_pause()
                
                # Route Bluetooth Media Keys to Headset
                elif event.command == 'MEDIA_PLAY_PAUSE' and ('speaker' not in dev_name and 'built-in' not in dev_name and 'macbook' not in dev_name):
                    channel.toggle_pause()
                    
                # NEXT command applies to headset/bluetooth
                elif event.command == 'NEXT' and ('speaker' not in dev_name and 'built-in' not in dev_name and 'macbook' not in dev_name):
                    channel.play_next()

    def load_track(self, channel_id, file_path):
        if channel_id in self.channels:
            self.channels[channel_id].add_to_queue(file_path)

    def stop_all(self):
        for c in self.channels.values():
            c.stop()
        self.media_listener.stop()
