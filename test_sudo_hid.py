import hid

devices = hid.enumerate()
for d in devices:
    if 'headset' in d.get('product_string', '').lower() or 'btm' in d.get('product_string', '').lower():
        try:
            h = hid.device()
            h.open_path(d['path'])
            print(f"SUCCESS: Opened {d['product_string']} at {d['path']}")
            h.close()
        except Exception as e:
            print(f"FAILED: Could not open {d['product_string']} at {d['path']} - {e}")
