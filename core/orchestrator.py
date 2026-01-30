import logging
import threading
from .audio_router import AudioChannel, AudioChannel
from .input_monitor import HIDListener, GlobalListener, list_hid_devices, InputEvent

class Orchestrator:
    """
    binds inputs to audio outputs.
    """
    def __init__(self):
        self.channels = {} # {id: AudioChannel}
        self.input_listeners = [] # [HIDListener]
        self.mappings = {} # {input_device_path_str: audio_channel_id}
        self.global_listener = None
        self.logger = logging.getLogger("Orchestrator")
        
        # Start Global Fallback by default
        self.global_listener = GlobalListener(self._handle_input)
        self.global_listener.start()

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
        """Attempts to find and map a HID device matching the audio device name."""
        if not audio_device_name:
            return

        devices = list_hid_devices()
        normalized_audio = audio_device_name.lower()
        
        best_match = None
        for d in devices:
            raw_name = d.get('product_string', '')
            if not raw_name:
                continue
                
            hid_name = raw_name.lower()
            
            # Simple containment match
            if hid_name in normalized_audio or normalized_audio in hid_name:
                best_match = d
                break
        
        if best_match:
            path = best_match['path']
            self.map_input(path, channel_id)
            self.logger.info(f"Auto-bound HID '{best_match.get('product_string')}' to Channel {channel_id}")
        else:
            self.logger.warning(f"No matching HID device found for '{audio_device_name}'")

    def map_input(self, input_path, channel_id):
        """Maps an input device path to a channel ID."""
        self.mappings[input_path] = channel_id
        self.logger.info(f"Mapped Input {input_path} -> Channel {channel_id}")

    def get_input_devices(self):
        """Returns a list of available HID devices for input binding."""
        return list_hid_devices()

    def start_hid_monitoring(self):
        """Scans and starts listeners for all capable HID devices."""
        # Clean up old
        for l in self.input_listeners:
            l.stop()
        self.input_listeners = []

        devices = list_hid_devices()
        for d in devices:
            path = d['path']
            # Only listen if we have a mapping or just listen to all?
            # Listening to all allows dynamic mapping later.
            l = HIDListener(d, self._handle_input)
            l.start()
            self.input_listeners.append(l)

    def _handle_input(self, event: InputEvent):
        """Callback for all input events."""
        from datetime import datetime
        now = datetime.now()
        
        # Enforce 8AM - 8PM rule
        if not (8 <= now.hour < 20):
            # Outside working hours, ignore inputs or maybe stop playback?
            # User requirement: "Live until 8pm". Assuming inputs ignored.
            self.logger.info(f"Input ignored/blocked outside allowed hours (8AM-8PM): {now.time()}")
            return

        self.logger.info(f"Input received: {event.command} from {event.device_id}")
        
        target_channel_id = None
        
        if event.device_id == 'GLOBAL':
            # Global listener affects ALL channels or a specific 'focused' one?
            # Requirement: "Play File 1 -> Stop -> Wait" logic per headset.
            # If global, maybe we just trigger the 'active' one. 
            # For now, let's say Global triggers ALL (or first) for debugging fallback.
            # Or better, we don't handle global if invalid.
            pass
        
        elif event.device_id in self.mappings:
            target_channel_id = self.mappings[event.device_id]
        
        if target_channel_id is not None and target_channel_id in self.channels:
            channel = self.channels[target_channel_id]
            if event.command == 'PLAY_PAUSE':
                channel.toggle_pause()
            elif event.command == 'NEXT':
                # User Requirement: "It can't be skipped".
                # User Requirement: "Able to ... replay".
                # Mapping NEXT button to REPLAY (Restart) satisfies 'Replay' and 'No Skip'.
                channel.restart_track()

    def load_track(self, channel_id, file_path):
        if channel_id in self.channels:
            self.channels[channel_id].add_to_queue(file_path)

    def stop_all(self):
        for c in self.channels.values():
            c.stop()
        for l in self.input_listeners:
            l.stop()
        if self.global_listener:
            self.global_listener.stop()
