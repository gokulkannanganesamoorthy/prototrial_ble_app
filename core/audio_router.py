import sounddevice as sd
import soundfile as sf
import threading
import queue
import time
import logging

class AudioChannel:
    """
    Manages a single audio output channel mapped to a specific output device.
    """
    def __init__(self, device_id, channel_name="Channel"):
        self.device_id = device_id
        self.name = channel_name
        self.playback_queue = queue.Queue()
        self.current_stream = None
        self.stop_event = threading.Event()
        self.is_playing = False
        self.logger = logging.getLogger(f"AudioChannel-{self.name}")
        
        # Verify device exists
        try:
            device_info = sd.query_devices(device_id, 'output')
            self.logger.info(f"Initialized on device: {device_info['name']}")
        except Exception as e:
            self.logger.error(f"Failed to initialize device {device_id}: {e}")
            raise

    def add_to_queue(self, file_path):
        """Adds a file to the playback queue."""
        self.playback_queue.put(file_path)
        self.logger.info(f"Added {file_path} to queue.")

    def play_next(self):
        """
        Advances to the next track in the queue. 
        If currently playing, stops current track first.
        """
        self.stop() # Ensure previous is stopped
        
        if self.playback_queue.empty():
            self.logger.info("Queue empty, nothing to play.")
            return

        next_file = self.playback_queue.get()
        self.stop_event.clear()
        
        thread = threading.Thread(target=self._playback_worker, args=(next_file,), daemon=True)
        thread.start()

    def stop(self):
        """Stops the current playback immediately."""
        if self.is_playing:
            self.stop_event.set()
            # Wait briefly for thread to clean up if needed, but don't block UI
            time.sleep(0.1) 
            self.is_playing = False

    def _playback_worker(self, file_path):
        """Internal worker to play audio in a blocking stream on a separate thread."""
        try:
            self.is_playing = True
            data, fs = sf.read(file_path, always_2d=True)
            
            self.logger.info(f"Starting playback: {file_path} on device {self.device_id}")
            
            # Callback is more robust for stopping than blocking write
            current_frame = 0
            
            def callback(outdata, frames, time_info, status):
                nonlocal current_frame
                if status:
                    self.logger.warning(status)
                
                if self.stop_event.is_set():
                    raise sd.CallbackStop()
                
                chunk_end = current_frame + frames
                if chunk_end > len(data):
                    # End of file
                    outdata[:len(data)-current_frame] = data[current_frame:]
                    outdata[len(data)-current_frame:] = 0
                    raise sd.CallbackStop()
                else:
                    outdata[:] = data[current_frame:chunk_end]
                    current_frame += frames

            with sd.OutputStream(samplerate=fs, device=self.device_id, channels=data.shape[1], callback=callback):
                # Wait until the stream is finished or stopped
                while not self.stop_event.is_set() and current_frame < len(data):
                    sd.sleep(100) # Check every 100ms
            
            self.logger.info("Playback finished or stopped.")
            
        except Exception as e:
            self.logger.error(f"Playback error: {e}")
        finally:
            self.is_playing = False

    @staticmethod
    def get_output_devices():
        """Returns a list of dicts with id and name for all output devices."""
        devices = []
        try:
            all_devices = sd.query_devices()
            for idx, dev in enumerate(all_devices):
                if dev['max_output_channels'] > 0:
                    devices.append({'id': idx, 'name': dev['name'], 'hostapi': dev['hostapi']})
        except Exception as e:
            logging.error(f"Error querying devices: {e}")
            # Mock for offline dev if needed
            return [{'id': 1, 'name': 'Mock Device 1', 'hostapi': 0}, {'id': 2, 'name': 'Mock Device 2', 'hostapi': 0}]
        return devices
