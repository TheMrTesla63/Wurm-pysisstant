import subprocess
import sys
import os

# Check if required packages are installed, and install them if not
def install_requirements():
    try:
        import PIL
    except ImportError:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])

    try:
        import watchdog
    except ImportError:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "watchdog"])

install_requirements()

from src.gui import main

if __name__ == "__main__":
    main()
