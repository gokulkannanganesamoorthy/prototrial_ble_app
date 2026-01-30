import hid
import json

def list_hid_devices():
    devices = []
    try:
        all_devs = hid.enumerate()
        for d in all_devs:
            # print(d)
            if d['usage_page'] == 12 or d['usage_page'] == 0: 
                print(f"Device: {d['product_string']}, Path: {d['path']}, Usage Page: {d['usage_page']}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    list_hid_devices()
