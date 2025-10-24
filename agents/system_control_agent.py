import subprocess
import sys

from .base_agent import IAgent


class SystemControlAgent(IAgent):
    def get_name(self) -> str:
        return "system_control"

    def execute(self, intent: dict) -> str:
        action = intent.get("action")
        params = intent.get("parameters", {})

        if action == "launch_application":
            # The app name is now passed directly as a parameter from the NER model
            app_name = params.get("APP_NAME")

            if not app_name:
                return "You asked me to launch something, but I didn't catch the name."

            # Use a dictionary for OS-specific commands
            app_command = self._get_app_command(app_name.lower())

            try:
                print(f"[SystemControlAgent] Attempting to launch '{app_name}' with command '{app_command}'...")
                subprocess.Popen(app_command)
                return f"Okay, launching {app_name}."
            except FileNotFoundError:
                print(f"[SystemControlAgent] ERROR: Command '{app_command}' not found.")
                return f"I'm sorry, I couldn't find an application named {app_name}."
            except Exception as e:
                print(f"[SystemControlAgent] ERROR: Failed to launch '{app_name}': {e}")
                return f"I'm sorry, I ran into an error trying to launch {app_name}."

        return f"I don't know how to perform the system control action: {action}"

    def _get_app_command(self, app_name: str) -> str:
        """Maps a generic app name to an OS-specific command."""
        # Simple mapping for demonstration
        if "calculator" in app_name:
            if sys.platform == "win32":
                return "calc"
            elif sys.platform == "darwin":
                return "Calculator"
            else:
                return "gnome-calculator"

        if "notepad++" in app_name or "notepad plus plus" in app_name:
            return "notepad++"

        # For most other apps, the name is the command
        # This can be expanded with more aliases
        return app_name.replace(" ", "")  # e.g., "google chrome" -> "googlechrome"
