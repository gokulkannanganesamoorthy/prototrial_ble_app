from pynput import keyboard

def on_press(key):
    try:
        print(f"Key pressed: {key}")
    except AttributeError:
        pass

def on_release(key):
    if key == keyboard.Key.esc:
        return False

with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
    print("Press media keys (Play/Pause/Next). Press ESC to stop.")
    listener.join()
