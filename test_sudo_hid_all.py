import hid

devices = hid.enumerate()
for d in devices:
    try:
        h = hid.device()
        h.open_path(d['path'])
        h.close()
    except Exception as e:
        print(f"FAILED: Could not open {d.get('product_string', 'Unknown')} at {d['path']} - {e}")
