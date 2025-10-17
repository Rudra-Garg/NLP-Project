import subprocess
import sys

from .base_agent import IAgent


class SystemControlAgent(IAgent):
    """An agent for OS-level actions like launching applications."""

    def get_name(self) -> str:
        return "system_control"

    def execute(self, intent: dict) -> str:
        action = intent.get("action")

        if action == "launch_application":
            # A very simple parameter extraction for now
            transcript = intent.get("transcript", "")
            app_name = self._extract_app_name(transcript)

            if not app_name:
                return "You asked me to launch something, but I didn't catch the name."

            try:
                print(f"[SystemControlAgent] Attempting to launch '{app_name}'...")
                # Use Popen for non-blocking process start
                subprocess.Popen(app_name)
                return f"Okay, launching {app_name}."
            except FileNotFoundError:
                print(f"[SystemControlAgent] ERROR: Command '{app_name}' not found.")
                return f"I'm sorry, I couldn't find an application named {app_name}."
            except Exception as e:
                print(f"[SystemControlAgent] ERROR: Failed to launch '{app_name}': {e}")
                return f"I'm sorry, I ran into an error trying to launch {app_name}."

        return f"I don't know how to perform the system control action: {action}"

    def _extract_app_name(self, transcript: str) -> str:
        """A simple helper to guess the application name from the transcript."""
        transcript = transcript.lower()
        if "notepad" in transcript:
            return "notepad"
        if "calculator" in transcript:
            # Check the operating system to launch the correct calculator app
            if sys.platform == "win32":
                return "calc"
            elif sys.platform == "darwin":  # macOS
                return "Calculator"
            else:  # Linux
                return "gnome-calculator"  # or 'kcalc'
        if "chrome" in transcript or "browser" in transcript:
            return "chrome"
        if "firefox" in transcript:
            return "firefox"
        return ""
