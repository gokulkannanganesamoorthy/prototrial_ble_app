import ctypes
from ctypes import wintypes
import sys
import os

# Check if running on Windows
if os.name != 'nt':
    print("This script must be run on a Windows machine.")
    sys.exit(1)

# --- Windows API Definitions ---
user32 = ctypes.WinDLL('user32', use_last_error=True)

# Window Messages
WM_INPUT = 0x00FF

# Raw Input Data Types
RIM_TYPEKEYBOARD = 1
RIM_TYPEMOUSE = 0
RIM_TYPEHID = 2

# Flags for registering device
RIDEV_INPUTSINK = 0x00000100

class RAWINPUTDEVICE(ctypes.Structure):
    _fields_ = [
        ("usUsagePage", wintypes.USHORT),
        ("usUsage", wintypes.USHORT),
        ("dwFlags", wintypes.DWORD),
        ("hwndTarget", wintypes.HWND)
    ]

# Raw Input Data Structures
class RAWINPUTHEADER(ctypes.Structure):
    _fields_ = [
        ("dwType", wintypes.DWORD),
        ("dwSize", wintypes.DWORD),
        ("hDevice", wintypes.HANDLE),
        ("wParam", wintypes.WPARAM)
    ]

class RAWHID(ctypes.Structure):
    _fields_ = [
        ("dwSizeHid", wintypes.DWORD),
        ("dwCount", wintypes.DWORD),
        ("bRawData", wintypes.BYTE * 1) # Variable length
    ]

class RAWKEYBOARD(ctypes.Structure):
    _fields_ = [
        ("MakeCode", wintypes.USHORT),
        ("Flags", wintypes.USHORT),
        ("Reserved", wintypes.USHORT),
        ("VKey", wintypes.USHORT),
        ("Message", wintypes.UINT),
        ("ExtraInformation", wintypes.ULONG)
    ]

class RAWINPUT(ctypes.Structure):
    class _U(ctypes.Union):
        _fields_ = [
            ("mouse", ctypes.c_byte * 24), # Dummy placeholder for mouse
            ("keyboard", RAWKEYBOARD),
            ("hid", RAWHID)
        ]
    _fields_ = [
        ("header", RAWINPUTHEADER),
        ("data", _U)
    ]

# --- Main Window Loop ---
def wnd_proc(hwnd, msg, wparam, lparam):
    if msg == WM_INPUT:
        # Get the size of the RAWINPUT structure
        size = wintypes.UINT(0)
        user32.GetRawInputData(
            ctypes.cast(lparam, wintypes.HANDLE),
            0x10000003, # RID_INPUT
            None,
            ctypes.byref(size),
            ctypes.sizeof(RAWINPUTHEADER)
        )

        if size.value > 0:
            # Allocate memory and get the actual data
            raw_input = RAWINPUT()
            
            res = user32.GetRawInputData(
                ctypes.cast(lparam, wintypes.HANDLE),
                0x10000003, # RID_INPUT
                ctypes.byref(raw_input),
                ctypes.byref(size),
                ctypes.sizeof(RAWINPUTHEADER)
            )
            
            if res > 0:
                header = raw_input.header
                print(f"--- Raw Input Received ---")
                print(f"Device Handle (hDevice): {header.hDevice}")
                print(f"Input Type: {header.dwType} (1=Keyboard, 2=Generic HID)")
                
                # Try to get the device name from the handle
                name_size = wintypes.UINT(0)
                user32.GetRawInputDeviceInfoW(header.hDevice, 0x20000007, None, ctypes.byref(name_size))
                
                if name_size.value > 0:
                    name_buf = ctypes.create_unicode_buffer(name_size.value)
                    user32.GetRawInputDeviceInfoW(header.hDevice, 0x20000007, name_buf, ctypes.byref(name_size))
                    print(f"Device Path: {name_buf.value}")
                
                if header.dwType == RIM_TYPEKEYBOARD:
                    kb = raw_input.data.keyboard
                    print(f"Keyboard MakeCode: {kb.MakeCode}, VKey: {kb.VKey}, Flags: {kb.Flags}")
                    if kb.VKey == 0xB3: # VK_MEDIA_PLAY_PAUSE
                        print(">> PLAY/PAUSE Media Key detected from this device! <<")
                        
                elif header.dwType == RIM_TYPEHID:
                    print(f"Generic HID Event Detected.")
                    # Parsing raw HID data is more complex, but we can see the handle
                    
                print("-" * 30 + "\n")
                
    return user32.DefWindowProcW(hwnd, msg, wparam, lparam)

def register_raw_input(hwnd):
    # Register for Keyboard (Page 1, Usage 6)
    rid_kb = RAWINPUTDEVICE()
    rid_kb.usUsagePage = 0x01
    rid_kb.usUsage = 0x06
    rid_kb.dwFlags = RIDEV_INPUTSINK
    rid_kb.hwndTarget = hwnd

    # Register for Consumer Control (Media Keys) (Page 12, Usage 1)
    rid_media = RAWINPUTDEVICE()
    rid_media.usUsagePage = 0x0C
    rid_media.usUsage = 0x01
    rid_media.dwFlags = RIDEV_INPUTSINK
    rid_media.hwndTarget = hwnd

    devices = (RAWINPUTDEVICE * 2)(rid_kb, rid_media)
    
    if not user32.RegisterRawInputDevices(devices, 2, ctypes.sizeof(RAWINPUTDEVICE)):
        print(f"Failed to register raw input devices. Error code: {ctypes.GetLastError()}")
        return False
    return True

def create_window():
    # Window Class registration
    WNDPROC = ctypes.WINFUNCTYPE(ctypes.c_long, wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM)
    wndproc = WNDPROC(wnd_proc)

    class WNDCLASSEX(ctypes.Structure):
        _fields_ = [
            ("cbSize", wintypes.UINT),
            ("style", wintypes.UINT),
            ("lpfnWndProc", WNDPROC),
            ("cbClsExtra", wintypes.INT),
            ("cbWndExtra", wintypes.INT),
            ("hInstance", wintypes.HANDLE),
            ("hIcon", wintypes.HANDLE),
            ("hCursor", wintypes.HANDLE),
            ("hbrBackground", wintypes.HANDLE),
            ("lpszMenuName", wintypes.LPCWSTR),
            ("lpszClassName", wintypes.LPCWSTR),
            ("hIconSm", wintypes.HANDLE),
        ]

    wndclass = WNDCLASSEX()
    wndclass.cbSize = ctypes.sizeof(WNDCLASSEX)
    wndclass.lpfnWndProc = wndproc
    wndclass.lpszClassName = "RawInputTestClass"
    wndclass.hInstance = kernel32.GetModuleHandleW(None)

    if not user32.RegisterClassExW(ctypes.byref(wndclass)):
        print("Failed to register window class")
        return None

    # Create a message-only window
    hwnd = user32.CreateWindowExW(
        0,
        "RawInputTestClass",
        "RawInput Test",
        0, 0, 0, 0, 0,
        0, # HWND_MESSAGE
        0, wndclass.hInstance, 0
    )
    
    return hwnd

if __name__ == "__main__":
    kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)
    
    print("Initializing Windows Raw Input API listener...")
    hwnd = create_window()
    if not hwnd:
        sys.exit(1)
        
    if not register_raw_input(hwnd):
        sys.exit(1)
        
    print("\n" + "="*50)
    print("Listening for Bluetooth/USB Keyboard inputs.")
    print("Please press PLAY/PAUSE on multiple connected headsets.")
    print("Check if the 'Device Handle (hDevice)' changes for each one.")
    print("Press Ctrl+C in the terminal to stop.")
    print("="*50 + "\n")
    
    # Message loop
    msg = wintypes.MSG()
    try:
        while user32.GetMessageW(ctypes.byref(msg), 0, 0, 0) != 0:
            user32.TranslateMessage(ctypes.byref(msg))
            user32.DispatchMessageW(ctypes.byref(msg))
    except KeyboardInterrupt:
        print("\nExiting...")
        sys.exit(0)
