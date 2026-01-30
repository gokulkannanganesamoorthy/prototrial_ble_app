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
        self.playback_queue = [] # List for random access [(id, path)]
        self.queue_lock = threading.Lock()
        self.job_counter = 0
        
        self.current_stream = None
        self.stop_event = threading.Event()
        self.is_playing = False
        self.is_paused = False
        self.logger = logging.getLogger(f"AudioChannel-{self.name}")
        
        # Verify device exists
        try:
            device_info = sd.query_devices(device_id, 'output')
            self.device_name = device_info['name']
            self.logger.info(f"Initialized on device: {self.device_name}")
        except Exception as e:
            self.logger.error(f"Failed to initialize device {device_id}: {e}")
            raise

    def add_to_queue(self, file_path):
        """Adds a file to the playback queue."""
        with self.queue_lock:
            self.job_counter += 1
            job_id = self.job_counter
            self.playback_queue.append((job_id, file_path))
            self.logger.info(f"Added {file_path} (ID: {job_id}) to queue.")
            return job_id

    def remove_from_queue(self, job_id):
        """Removes a file from queue by job ID."""
        with self.queue_lock:
            for i, (jid, path) in enumerate(self.playback_queue):
                if jid == job_id:
                    del self.playback_queue[i]
                    self.logger.info(f"Removed job {job_id} from queue.")
                    return True
            return False

    def play_next(self):
        """
        Advances to the next track in the queue. 
        If currently playing, stops current track first.
        """
        self.stop() # Ensure previous is stopped
        
        next_file = None
        with self.queue_lock:
            if not self.playback_queue:
                self.logger.info("Queue empty, nothing to play.")
                return
            # Pop the first item (FIFO)
            _, next_file = self.playback_queue.pop(0)

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
            self.is_paused = False # reset pause state
            data, fs = sf.read(file_path, always_2d=True)
            self.current_data = data # Store for restart
            self.current_fs = fs

            self.logger.info(f"Starting playback: {file_path} on device {self.device_id}")
            
            # Callback is more robust for stopping than blocking write
            self.current_frame = 0 # Instance var so we can modify it externally (restart)
            
            def callback(outdata, frames, time_info, status):
                if status:
                    self.logger.warning(status)
                
                if self.stop_event.is_set():
                    raise sd.CallbackStop()
                
                if self.is_paused:
                    outdata.fill(0) # access to 'outdata' allows silence
                    return 

                chunk_end = self.current_frame + frames
                if chunk_end > len(data):
                    # End of file
                    outdata[:len(data)-self.current_frame] = data[self.current_frame:]
                    outdata[len(data)-self.current_frame:] = 0
                    raise sd.CallbackStop()
                else:
                    outdata[:] = data[self.current_frame:chunk_end]
                    self.current_frame += frames

            with sd.OutputStream(samplerate=fs, device=self.device_id, channels=data.shape[1], callback=callback):
                # Wait until the stream is finished or stopped
                while not self.stop_event.is_set() and self.current_frame < len(data):
                    sd.sleep(100) # Check every 100ms
            
            self.logger.info("Playback finished or stopped.")
            
        except Exception as e:
            self.logger.error(f"Playback error: {e}")
        finally:
            self.is_playing = False
            self.current_data = None
    
    def toggle_pause(self):
        """Toggles the pause state of playback."""
        if self.is_playing:
            self.is_paused = not self.is_paused
            self.logger.info(f"Pause state toggled: {self.is_paused}")

    def restart_track(self):
        """Restarts the current track from the beginning."""
        if self.is_playing:
            self.current_frame = 0
            self.logger.info("Track restarted.")

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
