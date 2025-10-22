import sys
import subprocess
from .base_agent import IAgent

# Platform-specific dependencies
IS_WINDOWS = sys.platform == "win32"
IS_MAC = sys.platform == "darwin"
IS_LINUX = sys.platform.startswith("linux")

if IS_WINDOWS:
    try:
        from comtypes import CLSCTX_ALL
        from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
    except ImportError:
        print("[VolumeControlAgent] WARNING: pycaw library not found. Windows volume control will not work.")
        print("Please run: pip install pycaw")
        IS_WINDOWS = False  # Disable Windows-specific logic if library is missing


class VolumeControlAgent(IAgent):
    """An agent to control system volume across different operating systems."""
    DEFAULT_VOLUME_CHANGE = 10
    DEFAULT_VOLUME = 50

    def get_name(self) -> str:
        return "volume_control"

    def execute(self, intent: dict) -> str:
        action = intent.get("action")
        params = intent.get("parameters", {})
        
        try:
            if action == "set_volume":
                level = params.get("level")
                if level is None:
                    return "You need to specify a volume level."
                return self._set_volume(int(level))
            
            elif action == "increase_volume":
                amount = params.get("amount", self.DEFAULT_VOLUME_CHANGE) # Default to 10%
                return self._change_volume(int(amount))

            elif action == "decrease_volume":
                amount = params.get("amount", self.DEFAULT_VOLUME_CHANGE) # Default to 10%
                return self._change_volume(-int(amount))

            else:
                return f"I don't know how to perform the volume action: {action}."

        except Exception as e:
            print(f"[VolumeControlAgent] ERROR: {e}")
            return "I'm sorry, I couldn't adjust the volume."
            return "I'm sorry, I couldn't adjust the volume."

    def _get_current_volume(self) -> int:
        """Gets the current system volume as a percentage (0-100)."""
        if IS_WINDOWS:
            devices = AudioUtilities.GetSpeakers()
            interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
            volume = interface.QueryInterface(IAudioEndpointVolume)
            return int(volume.GetMasterVolumeLevelScalar() * 100)
        
        elif IS_MAC:
            result = subprocess.run(['osascript', '-e', 'output volume of (get volume settings)'], capture_output=True, text=True)
            return int(result.stdout.strip())

        elif IS_LINUX:
            result = subprocess.run(['amixer', 'sget', 'Master'], capture_output=True, text=True)
            line = [l for l in result.stdout.split('\n') if 'Front Left:' in l][0]
        return self.DEFAULT_VOLUME # Default fallback
        
        return 50 # Default fallback

    def _set_volume(self, level: int) -> str:
        """Sets the system volume to a specific level (0-100)."""
        level = max(0, min(100, level)) # Clamp between 0 and 100

        if IS_WINDOWS:
            devices = AudioUtilities.GetSpeakers()
            interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
            volume = interface.QueryInterface(IAudioEndpointVolume)
            volume.SetMasterVolumeLevelScalar(level / 100.0, None)
        
        elif IS_MAC:
            subprocess.run(['osascript', '-e', f"set volume output volume {level}"])

        elif IS_LINUX:
            subprocess.run(['amixer', 'sset', 'Master', f'{level}%'])
        
        else:
            return "Volume control is not supported on this operating system."

        return f"Volume set to {level}%."

    def _change_volume(self, amount: int) -> str:
        """Increases or decreases the volume by a given amount."""
        current_volume = self._get_current_volume()
        new_level = current_volume + amount
        return self._set_volume(new_level)
