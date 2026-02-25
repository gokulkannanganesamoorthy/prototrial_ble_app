import hid
import time

devices = [d for d in hid.enumerate() if 'headset' in d.get('product_string', '').lower() or 'btm' in d.get('product_string', '').lower() or 'unknown' in d.get('product_string', '').lower()]

handles = []
for d in devices:
    try:
        h = hid.device()
        h.open_path(d['path'])
        h.set_nonblocking(True)
        handles.append((h, d['path'], d.get('product_string', 'Unknown')))
        print(f"Opened {d.get('product_string', 'Unknown')} at {d['path']}")
    except Exception as e:
        print(f"Failed to open {d['path']}: {e}")

print("Listening for 10 seconds. PRESS PAUSE ON HEADSET NOW!")
start = time.time()
while time.time() - start < 15:
    for h, path, name in handles:
        try:
            data = h.read(64)
            if data:
                print(f"GOT DATA from {name} ({path}): {data}")
        except:
            pass
    time.sleep(0.05)

for h, _, _ in handles:
    h.close()
