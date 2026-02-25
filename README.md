# prototrial_ble_app

# Assembly Line Audio Manager

A Python desktop application designed for managing independent audio instruction streams for assembly line workers using multiple Bluetooth headsets.

## Core Features

1. **Multi-Device Routing**: Route specific audio files to specific speakers or headsets using `sounddevice`.
2. **Independent Streams**: 9 simultaneous, non-blocking audio queues.
3. **Hardware Input Triggers**: Uses `pynput` to detect global keyboard and media events. Built-in Mac speakers are mapped to the Spacebar, while Bluetooth Headsets are mapped to the media Play/Pause and Next keys.
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
   cd prototrial_ble_app
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

   _(Note: `pynput`, `sounddevice` and `soundfile` are critical)_

3. **Run the Application**:
   ```powershell
   python3 main.py
   ```
   _(Mac Users: The Terminal must be granted Accessibility & Input Monitoring permissions in System Settings > Privacy & Security)._

## Usage Guide

### 1. Configure Audio Output

In the Dashboard, you will see 9 Station panels.

- Use the **"Output"** dropdown to select the specific audio device for that worker (e.g. MacBook Pro Speakers, Headphones).

### 2. Hardware Mappings (macOS)

Due to macOS security stripping hardware IDs from Bluetooth media keys, inputs are hard-routed based on the selected audio output device:

- **Mac Speakers (Station 1):** Press the **Spacebar** on the MacBook keyboard to Play/Pause.
- **Bluetooth Headset (Station 2):** Press the physical **Play/Pause** or **Next** button on the headset to control its audio stream.

### 3. Load Instructions

- Click **"+ Add File"** to add playback instructions (MP3/WAV) to the queue.
- Use **Play/Resume** or the hardware triggers to advance the queue.

## Troubleshooting

- **"Input Not Detected"**: Ensure your Terminal is added to Accessibility and Input Monitoring in macOS System Settings.
- **Windows Implementation**: A `windows_test.py` script is included in the root directory to test Raw Input API hardware extraction if true 1-to-1 Bluetooth mapping is desired off macOS.
