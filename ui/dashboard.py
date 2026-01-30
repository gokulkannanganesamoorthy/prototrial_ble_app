import customtkinter as ctk
from tkinter import filedialog
import threading
import os
from core.orchestrator import Orchestrator
from core.audio_router import AudioChannel

class ChannelFrame(ctk.CTkFrame):
    """
    UI Component for a single Audio Channel.
    """
    def __init__(self, master, channel_id, orchestrator, **kwargs):
        super().__init__(master, **kwargs)
        self.channel_id = channel_id
        self.orchestrator = orchestrator
        self.channel = None
        
        self.setup_ui()
    
    def setup_ui(self):
        # Title
        self.lbl_title = ctk.CTkLabel(self, text=f"Headset {self.channel_id}", font=ctk.CTkFont(size=20, weight="bold"))
        self.lbl_title.pack(pady=10)

        # Output Selection
        self.lbl_out = ctk.CTkLabel(self, text="Audio Output:")
        self.lbl_out.pack()
        
        self.combo_out = ctk.CTkComboBox(self, values=["Select Device"], command=self.on_device_select)
        self.combo_out.pack(pady=5)
        
        # Input Mapping (Simplified for now)
        self.lbl_in = ctk.CTkLabel(self, text="Input Trigger:")
        self.lbl_in.pack()
        self.entry_input_id = ctk.CTkEntry(self, placeholder_text="Device Path/ID")
        self.entry_input_id.pack(pady=5)
        self.btn_map = ctk.CTkButton(self, text="Bind Input", command=self.on_bind_input)
        self.btn_map.pack(pady=5)

        # Queue Controls
        self.lbl_queue = ctk.CTkLabel(self, text="Queue (Files):")
        self.lbl_queue.pack(pady=(20, 5))
        
        self.list_queue = ctk.CTkTextbox(self, height=100)
        self.list_queue.pack(fill="x", padx=10)

        self.btn_add = ctk.CTkButton(self, text="Add File", command=self.add_file)
        self.btn_add.pack(pady=10)
        
        self.btn_play_next = ctk.CTkButton(self, text="Force Next (Simulate)", command=self.manual_play_next, fg_color="green")
        self.btn_play_next.pack(pady=10)

    def load_devices(self, devices):
        names = [f"{d['id']}: {d['name']}" for d in devices]
        self.combo_out.configure(values=names)

    def on_device_select(self, choice):
        # Format "ID: Name"
        try:
            dev_id = int(choice.split(':')[0])
            self.channel = self.orchestrator.add_channel(self.channel_id, dev_id)
        except Exception as e:
            print(f"Error selecting device: {e}")

    def on_bind_input(self):
        input_path = self.entry_input_id.get()
        if input_path:
            self.orchestrator.map_input(input_path, self.channel_id)
    
    def add_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("Audio", "*.mp3 *.wav")])
        if file_path:
            self.list_queue.insert("end", f"{os.path.basename(file_path)}\n")
            if self.channel:
                self.channel.add_to_queue(file_path)
            else:
                print("No channel initialized yet.")

    def manual_play_next(self):
        if self.channel:
            self.channel.play_next()

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title("Assembly Line Audio Manager")
        self.geometry("1000x600")
        
        self.orchestrator = Orchestrator()
        
        # Grid layout for 3 channels
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure(2, weight=1)
        
        self.frames = []
        for i in range(3):
            f = ChannelFrame(self, i+1, self.orchestrator)
            f.grid(row=0, column=i, padx=10, pady=10, sticky="nsew")
            self.frames.append(f)
            
        self.refresh_devices()

    def refresh_devices(self):
        devs = AudioChannel.get_output_devices()
        for f in self.frames:
            f.load_devices(devs)

    def on_closing(self):
        self.orchestrator.stop_all()
        self.destroy()

if __name__ == "__main__":
    app = App()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()
