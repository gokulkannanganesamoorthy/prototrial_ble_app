import sys
import os

# Ensure the core module is found
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ui.dashboard import App

if __name__ == "__main__":
    app = App()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()
