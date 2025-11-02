import queue
import threading

import customtkinter as ctk

from loki_worker import LokiWorker

# Set appearance and color theme
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")


class LokiApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("LOKI Voice Assistant")
        self.geometry("600x400")

        # Create a font for the labels
        self.status_font = ctk.CTkFont(family="Roboto", size=24, weight="bold")
        self.transcript_font = ctk.CTkFont(family="Roboto", size=16)

        # Main container
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # Status Label (displays "Listening...", "Transcribing...", etc.)
        self.status_label = ctk.CTkLabel(self, text="Initializing...", font=self.status_font, text_color="#A9A9A9")
        self.status_label.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="nsew")

        # Transcript Label (displays what was heard and LOKI's response)
        self.transcript_label = ctk.CTkLabel(self, text="", font=self.transcript_font, wraplength=550, justify="center")
        self.transcript_label.grid(row=1, column=0, padx=20, pady=(10, 20), sticky="nsew")

        # --- Threading and Communication Setup ---
        self.message_queue = queue.Queue()
        self.stop_event = threading.Event()

        self.loki_worker = LokiWorker(self.message_queue, self.stop_event)
        self.loki_thread = threading.Thread(target=self.loki_worker.run, daemon=True)
        self.loki_thread.start()

        # Start the queue processing loop
        self.process_queue()

        # Set the closing protocol
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def process_queue(self):
        """
        Check the queue for messages from the LokiWorker and update the GUI.
        """
        try:
            message = self.message_queue.get_nowait()
            # Parse the message based on its prefix
            if message.startswith("STATUS:"):
                self.status_label.configure(text=message.replace("STATUS: ", ""))
            elif message.startswith("HEARD:"):
                self.transcript_label.configure(text=message.replace("HEARD: ", ""))
            elif message.startswith("LOKI:"):
                self.transcript_label.configure(text=message.replace("LOKI: ", ""))
            elif message.startswith("ERROR:"):
                self.status_label.configure(text="Error", text_color="red")
                self.transcript_label.configure(text=message.replace("ERROR: ", ""))

        except queue.Empty:
            pass  # Do nothing if the queue is empty
        finally:
            # Schedule the next check in 100ms
            self.after(100, self.process_queue)

    def on_closing(self):
        """Handle the window closing event."""
        print("Closing application...")
        self.stop_event.set()  # Signal the worker to stop
        self.loki_thread.join(timeout=5)  # Wait for the worker thread to finish
        self.destroy()


if __name__ == "__main__":
    app = LokiApp()
    app.mainloop()
