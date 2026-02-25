import Quartz
from AppKit import NSEvent, NSApplication
from PyObjCTools import AppHelper

def test_media_keys():
    print("Listening for Media Keys (Play/Pause, Next). Press Ctrl+C to stop.")
    
    def my_cg_event_callback(proxy, type, event, refcon):
        if type == Quartz.kCGEventKeyDown or type == Quartz.kCGEventKeyUp or type == Quartz.NSSystemDefined:
            try:
                ns_event = NSEvent.eventWithCGEvent_(event)
                if ns_event.type() == Quartz.NSSystemDefined and ns_event.subtype() == 8:
                    data = ns_event.data1()
                    keyCode = (data & 0xFFFF0000) >> 16
                    keyFlags = (data & 0x0000FFFF)
                    keyState = (keyFlags & 0xFF00) >> 8
                    
                    isKeyRepeating = keyFlags & 0x1
                    
                    if keyState == int(Quartz.NX_KEYDOWN):
                        if keyCode == int(Quartz.NX_KEYTYPE_PLAY):
                            print("PLAY/PAUSE Pressed")
                        elif keyCode == int(Quartz.NX_KEYTYPE_FAST):
                            print("NEXT Pressed")
                        elif keyCode == int(Quartz.NX_KEYTYPE_REWIND):
                            print("PREVIOUS Pressed")
            except Exception as e:
                pass
        return event

    event_mask = (Quartz.CGEventMaskBit(Quartz.NSSystemDefined) | 
                  Quartz.CGEventMaskBit(Quartz.kCGEventKeyDown) | 
                  Quartz.CGEventMaskBit(Quartz.kCGEventKeyUp))
                  
    tap = Quartz.CGEventTapCreate(
        Quartz.kCGSessionEventTap,
        Quartz.kCGHeadInsertEventTap,
        0,
        event_mask,
        my_cg_event_callback,
        None
    )
    
    if not tap:
        print("Failed to create event tap! Make sure terminal has Accessibility permissions in System Preferences.")
        return
        
    run_loop_source = Quartz.CFMachPortCreateRunLoopSource(None, tap, 0)
    Quartz.CFRunLoopAddSource(Quartz.CFRunLoopGetCurrent(), run_loop_source, Quartz.kCFRunLoopCommonModes)
    Quartz.CGEventTapEnable(tap, True)
    
    AppHelper.runEventLoop()

if __name__ == '__main__':
    test_media_keys()
