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
        super().__init__(master, fg_color=("gray85", "gray20"), corner_radius=10, border_width=1, border_color=("gray70", "gray30"), **kwargs)
        self.channel_id = channel_id
        self.orchestrator = orchestrator
        self.channel = None
        
        self.setup_ui()
    
    def setup_ui(self):
        # Header
        self.header = ctk.CTkFrame(self, fg_color="transparent")
        self.header.pack(fill="x", padx=10, pady=(10, 5))
        
        self.lbl_title = ctk.CTkLabel(self.header, text=f"Station {self.channel_id}", font=ctk.CTkFont(size=16, weight="bold"))
        self.lbl_title.pack(side="left")
        
        self.lbl_status = ctk.CTkLabel(self.header, text="Inactive", text_color="gray")
        self.lbl_status.pack(side="right")

        # Controls Area
        self.controls = ctk.CTkFrame(self, fg_color="transparent")
        self.controls.pack(fill="x", padx=10, pady=5)

        # Output Selection
        self.lbl_out = ctk.CTkLabel(self.controls, text="Output:", font=ctk.CTkFont(size=12))
        self.lbl_out.pack(side="left", padx=5)
        
        self.combo_out = ctk.CTkComboBox(self.controls, values=["Select Device"], command=self.on_device_select, width=200)
        self.combo_out.pack(side="left", padx=5, fill="x", expand=True)
        
        # Queue Area
        self.queue_frame = ctk.CTkFrame(self, fg_color=("gray90", "gray17"))
        self.queue_frame.pack(fill="x", expand=False, padx=10, pady=5)
        
        self.lbl_queue = ctk.CTkLabel(self.queue_frame, text="Playlist", font=ctk.CTkFont(size=12, weight="bold"))
        self.lbl_queue.pack(anchor="w", padx=5, pady=(5,0))
        
        # Container for list items (Scrollable if needed, but here simple Frame inside parent)
        # Note: If many items, user wanted to scroll the MAIN page. 
        # So we keep this list short or let it grow and rely on main scroll.
        # But user reported "unable to scroll". 
        # FIXED: Using a container that doesn't capture scroll events like Textbox did.
        self.queue_container = ctk.CTkFrame(self.queue_frame, fg_color="transparent")
        self.queue_container.pack(fill="both", expand=True, padx=5, pady=5)

        # Action Buttons
        self.actions = ctk.CTkFrame(self, fg_color="transparent")
        self.actions.pack(fill="x", padx=10, pady=10)
        
        self.btn_add = ctk.CTkButton(self.actions, text="+ Add File", command=self.add_file, height=25, width=80)
        self.btn_add.pack(side="left", padx=(0, 5))
        
        self.btn_pause = ctk.CTkButton(self.actions, text="Pause/Resume", command=self.toggle_pause, height=25, width=80, fg_color="orange")
        self.btn_pause.pack(side="left", padx=5)
        
        self.btn_play_next = ctk.CTkButton(self.actions, text="▶ Simulate Next", command=self.manual_play_next, fg_color="green", height=25, width=100)
        self.btn_play_next.pack(side="right", fill="x", expand=True, padx=(5, 0))

    def load_devices(self, output_devices):
        out_names = [f"{d['id']}: {d['name']}" for d in output_devices]
        self.combo_out.configure(values=out_names)

    def on_device_select(self, choice):
        try:
            dev_id = int(choice.split(':')[0])
            self.channel = self.orchestrator.add_channel(self.channel_id, dev_id)
            self.lbl_status.configure(text="Active", text_color="green")
            # Note: Input binding happens automatically in orchestrator.add_channel
        except Exception as e:
            print(f"Error selecting device: {e}")
            self.lbl_status.configure(text="Error", text_color="red")
    
    def add_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("Audio", "*.mp3 *.wav *.ogg *.flac")])
        if file_path:
            if self.channel:
                job_id = self.channel.add_to_queue(file_path)
                self.create_queue_row(job_id, file_path)
            else:
                print("No channel initialized yet.")
    
    def create_queue_row(self, job_id, file_path):
        row = ctk.CTkFrame(self.queue_container, fg_color="transparent", height=25)
        row.pack(fill="x", pady=2)
        
        lbl = ctk.CTkLabel(row, text=os.path.basename(file_path), font=("Arial", 11), width=150, anchor="w")
        lbl.pack(side="left", padx=5, fill="x", expand=True)
        
        btn_del = ctk.CTkButton(row, text="X", width=25, height=25, fg_color="red", 
                                command=lambda id=job_id, w=row: self.remove_file(id, w))
        btn_del.pack(side="right", padx=2)

    def remove_file(self, job_id, widget):
        if self.channel:
            success = self.channel.remove_from_queue(job_id)
            if success:
                widget.destroy()

    def toggle_pause(self):
        if self.channel:
            self.channel.toggle_pause()

    def manual_play_next(self):
        if self.channel:
            self.channel.play_next()

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title("Assembly Line Audio Manager")
        self.geometry("1100x700")
        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("blue")
        
        self.orchestrator = Orchestrator()
        
        # Main Layout
        self.header = ctk.CTkLabel(self, text="Audio Station Control Dashboard", font=ctk.CTkFont(size=24, weight="bold"))
        self.header.pack(pady=10)

        # Scrollable Area for 9 Channels
        self.scroll_area = ctk.CTkScrollableFrame(self, label_text="Stations")
        self.scroll_area.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        self.scroll_area.grid_columnconfigure(0, weight=1)
        self.scroll_area.grid_columnconfigure(1, weight=1)
        self.scroll_area.grid_columnconfigure(2, weight=1)

        self.frames = []
        for i in range(9):
            f = ChannelFrame(self.scroll_area, i+1, self.orchestrator)
            row = i // 3
            col = i % 3
            f.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")
            self.frames.append(f)
            
        self.refresh_devices()

    def refresh_devices(self):
        out_devs = AudioChannel.get_output_devices()
        for f in self.frames:
            f.load_devices(out_devs)

    def on_closing(self):
        self.orchestrator.stop_all()
        self.destroy()

if __name__ == "__main__":
    app = App()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()
