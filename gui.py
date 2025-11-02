import queue
import threading

import customtkinter as ctk
from PIL import Image
from pystray import Icon as TrayIcon, Menu as TrayMenu, MenuItem as TrayMenuItem

from loki_worker import LokiWorker

# Set appearance and color theme
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")


class LokiApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("LOKI Voice Assistant")
        self.geometry("600x250")  # Made the window a bit shorter

        # --- UI Elements ---
        self.status_font = ctk.CTkFont(family="Roboto", size=24, weight="bold")
        self.transcript_font = ctk.CTkFont(family="Roboto", size=16)

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self.status_label = ctk.CTkLabel(self, text="Initializing...", font=self.status_font, text_color="#A9A9A9")
        self.status_label.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")

        self.transcript_label = ctk.CTkLabel(self, text="", font=self.transcript_font, wraplength=550, justify="center")
        self.transcript_label.grid(row=1, column=0, padx=20, pady=20, sticky="nsew")

        # --- Threading and Communication ---
        self.message_queue = queue.Queue()
        self.stop_event = threading.Event()

        self.loki_worker = LokiWorker(self.message_queue, self.stop_event)
        self.loki_thread = threading.Thread(target=self.loki_worker.run, daemon=True)

        # --- System Tray Setup ---
        self.tray_icon = None
        self.setup_tray_icon()

        # Start the LOKI worker and the queue processing
        self.loki_thread.start()
        self.process_queue()

        # --- Window Behavior ---
        # Hide the window at startup
        self.withdraw()
        # Instead of closing, the 'X' button will now hide the window
        self.protocol("WM_DELETE_WINDOW", self.hide_window)

    def setup_tray_icon(self):
        """Creates and runs the system tray icon in a separate thread."""
        try:
            icon_image = Image.open("icon.png")
            menu = TrayMenu(
                TrayMenuItem("Show LOKI", self.show_window, default=True),
                TrayMenuItem("Quit", self.quit_app)
            )
            self.tray_icon = TrayIcon("LOKI", icon_image, "LOKI Voice Assistant", menu)

            # Run the tray icon in a detached thread so it doesn't block the GUI
            threading.Thread(target=self.tray_icon.run, daemon=True).start()

        except FileNotFoundError:
            print("ERROR: icon.png not found. Cannot create system tray icon.")

    def process_queue(self):
        """Check the queue for messages from the LokiWorker and update the GUI."""
        try:
            message = self.message_queue.get_nowait()

            # --- NEW: Handle visibility messages ---
            if message == "SHOW_WINDOW":
                self.show_window()
            elif message == "HIDE_WINDOW":
                # Hide the window after a 4-second delay to allow user to read the response
                self.after(4000, self.hide_window)

            elif message.startswith("STATUS:"):
                self.status_label.configure(text=message.replace("STATUS: ", ""))
            elif message.startswith("HEARD:"):
                self.transcript_label.configure(text=message.replace("HEARD: ", ""))
            elif message.startswith("LOKI:"):
                self.transcript_label.configure(text=message.replace("LOKI: ", ""))
            elif message.startswith("ERROR:"):
                self.status_label.configure(text="Error", text_color="red")
                self.transcript_label.configure(text=message.replace("ERROR: ", ""))

        except queue.Empty:
            pass
        finally:
            self.after(100, self.process_queue)

    def show_window(self):
        """Brings the window to the front."""
        self.deiconify()  # Un-hides the window
        self.lift()  # Brings it to the top
        self.attributes("-topmost", True)  # Makes it stay on top
        self.after(100, lambda: self.attributes("-topmost", False))  # Then allows other windows on top

    def hide_window(self):
        """Hides the main window."""
        self.withdraw()

    def quit_app(self):
        """Handles the complete shutdown of the application."""
        print("Closing application...")
        if self.tray_icon:
            self.tray_icon.stop()
        self.stop_event.set()
        self.loki_thread.join(timeout=2)
        self.destroy()


if __name__ == "__main__":
    app = LokiApp()
    app.mainloop()
