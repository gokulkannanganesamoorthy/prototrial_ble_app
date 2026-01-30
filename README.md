# prototrial_ble_app

# Assembly Line Audio Manager

A Python desktop application designed for managing independent audio instruction streams for assembly line workers using multiple Bluetooth headsets.

## Core Features
1. **Multi-Device Routing**: Route specific audio files to specific Bluetooth headset IDs using `sounddevice`.
2. **Independent Streams**: 3 simultaneous, non-blocking audio queues.
3. **Hardware Input Triggers**: Uses `hidapi` to detect specific "Next" media key presses from specific headsets to advance only that user's queue.
4. **Queue Management**: "Play -> Stop -> Wait for Trigger" logic to pace instructions.

## Installation

### Prerequisites
- Windows 10/11
- Python 3.10+
- 3x Bluetooth Headsets (paired)

### Setup
The project uses a local virtual environment.

1. **Clone/Download** the repository.
2. **Install Dependencies**:
   ```powershell
   cd "c:\Users\24i463\Desktop\a\prototrial"
   .\venv\Scripts\pip install -r requirements.txt
   ```
   *(Note: `pynput` and `hidapi` are critical)*

3. **Run the Application**:
   ```powershell
   .\venv\Scripts\python main.py
   ```

## Usage Guide

### 1. Configure Audio Output
In the Dashboard, you will see 3 "Headset" columns.
- Use the **"Audio Output"** dropdown to select the specific Bluetooth device for that worker.
- If devices are missing, restart the app to refresh the list.

### 2. Bind Input Controls
To ensure Headset A's button only controls Headset A's audio:
- Press the "Next" or "Play/Pause" button on the headset.
- Check the application logs (console) for the **Device Path** (e.g., `\\?\HID#...`).
- Copy this ID into the **"Input Trigger"** box for the correct column.
- Click **"Bind Input"**.

### 3. Load Instructions
- Click **"Add File"** to add playback instructions (MP3/WAV) to the queue.
- The queue executes sequentially.

## Troubleshooting
- **"Device Not Found"**: Ensure headsets are connected *before* launching the app.
- **"Input Not Detected"**: Some headsets do not expose standard HID interfaces over Bluetooth. In this case, use the on-screen "Force Next" button or map a keyboard key.
