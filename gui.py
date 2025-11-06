import queue
import threading

import customtkinter as ctk
from PIL import Image
from pystray import Icon as TrayIcon, Menu as TrayMenu, MenuItem as TrayMenuItem

from loki_worker import LokiWorker

# --- UI Configuration ---
WINDOW_WIDTH = 700
WINDOW_HEIGHT = 450
TITLE = "LOKI"


class LokiApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # --- Window Setup ---
        self.x = None
        self.y = None
        self.title(TITLE)
        self.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        self.overrideredirect(True)  # Frameless window
        self.attributes("-alpha", 0.0)  # Start fully transparent for fade-in
        self.attributes("-topmost", True)

        # --- Draggable Window Logic ---
        self.bind("<ButtonPress-1>", self.start_move)
        self.bind("<ButtonRelease-1>", self.stop_move)
        self.bind("<B1-Motion>", self.do_move)

        # --- Colors and Fonts ---
        self.COLOR_USER = "#66B2FF"
        self.COLOR_LOKI = "#FFFFFF"
        self.COLOR_STATUS = "#B0B0B0"
        self.FONT_TITLE = ctk.CTkFont(family="Segoe UI", size=36, weight="bold")
        self.FONT_STATUS = ctk.CTkFont(family="Segoe UI", size=16)
        self.FONT_LOG = ctk.CTkFont(family="Segoe UI", size=14)

        # --- State Variables for Animations ---
        self.is_processing = False
        self.is_pulsing = False
        self.pulse_direction = 1
        self.pulse_color_value = 170  # Start color for pulse (AA in hex)
        self.spinner_chars = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
        self.spinner_index = 0
        self.status_text_label = None
        self.log_frame = None
        self._is_closing = False
        self.manually_opened = False  # Track if window was manually opened
        self.pending_hide_id = None  # Track scheduled hide operation

        # --- UI Layout and Widgets ---
        self.setup_ui()

        # --- Threading and Communication ---
        self.message_queue = queue.Queue()
        self.stop_event = threading.Event()
        self.loki_worker = LokiWorker(self.message_queue, self.stop_event)
        self.loki_thread = threading.Thread(target=self.loki_worker.run, daemon=True)

        # --- System Tray ---
        self.tray_icon = None
        self.setup_tray_icon()

        # --- Finalize and Run ---
        self.loki_thread.start()
        self.process_queue()
        self.withdraw()  # Start hidden
        self.protocol("WM_DELETE_WINDOW", self.hide_window)

    def setup_ui(self):
        # Background Image
        try:
            bg_image = ctk.CTkImage(Image.open("background.png"), size=(WINDOW_WIDTH, WINDOW_HEIGHT))
            bg_label = ctk.CTkLabel(self, image=bg_image, text="")
            bg_label.place(x=0, y=0, relwidth=1, relheight=1)
        except FileNotFoundError:
            print("WARNING: background.png not found. Using solid color.")

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        self.grid_rowconfigure(2, weight=0)

        # Header Frame
        top_frame = ctk.CTkFrame(self, fg_color="transparent")
        top_frame.grid(row=0, column=0, padx=20, pady=20, sticky="ew")
        top_frame.grid_columnconfigure(1, weight=1)

        title_label = ctk.CTkLabel(top_frame, text=TITLE, font=self.FONT_TITLE)
        title_label.grid(row=0, column=0, sticky="w")

        # Close button
        close_button = ctk.CTkButton(
            top_frame,
            text="✕",
            width=30,
            height=30,
            font=ctk.CTkFont(size=18),
            fg_color="transparent",
            hover_color=("#3B3B3B", "#2B2B2B"),
            command=self.minimize_to_tray
        )
        close_button.grid(row=0, column=1, sticky="e", padx=(0, 10))

        status_frame = ctk.CTkFrame(top_frame, fg_color="transparent")
        status_frame.grid(row=0, column=2, sticky="e")
        self.status_icon_label = ctk.CTkLabel(status_frame, text="⚫", font=self.FONT_STATUS,
                                              text_color=self.COLOR_STATUS)
        self.status_icon_label.pack(side="left", padx=(0, 10))
        self.status_text_label = ctk.CTkLabel(status_frame, text="Initializing...", font=self.FONT_STATUS,
                                              text_color=self.COLOR_STATUS)
        self.status_text_label.pack(side="left")

        # Conversation Log Frame
        self.log_frame = ctk.CTkScrollableFrame(self, fg_color=("#2B2B2B", "#1E1E1E"), border_width=0)
        self.log_frame.grid(row=1, column=0, padx=20, pady=(0, 10), sticky="nsew")

        # Text Input Frame
        input_frame = ctk.CTkFrame(self, fg_color="transparent")
        input_frame.grid(row=2, column=0, padx=20, pady=(0, 20), sticky="ew")
        input_frame.grid_columnconfigure(0, weight=1)

        self.text_input = ctk.CTkEntry(
            input_frame,
            placeholder_text="Type your command here...",
            font=self.FONT_LOG,
            height=40
        )
        self.text_input.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        self.text_input.bind("<Return>", lambda e: self.send_text_input())

        self.send_button = ctk.CTkButton(
            input_frame,
            text="Send",
            width=80,
            height=40,
            command=self.send_text_input
        )
        self.send_button.grid(row=0, column=1, sticky="e")

    def cancel_pending_hide(self):
        """Cancel any pending hide operation."""
        if self.pending_hide_id is not None:
            self.after_cancel(self.pending_hide_id)
            self.pending_hide_id = None
            print("[DEBUG GUI] Cancelled pending hide operation")

    def process_queue(self):
        if self._is_closing:
            return
        try:
            while True:  # Process ALL messages in queue
                message = self.message_queue.get_nowait()

                if message == "SHOW_WINDOW":
                    self.cancel_pending_hide()  # Cancel any pending hide
                    self.manually_opened = False  # Auto-opened by wake word
                    print(f"[DEBUG GUI] SHOW_WINDOW: manually_opened = {self.manually_opened}")
                    # Clear old logs for new conversation
                    for widget in self.log_frame.winfo_children():
                        widget.destroy()
                    self.fade_in()
                elif message == "HIDE_WINDOW":
                    print(f"[DEBUG GUI] HIDE_WINDOW received: manually_opened = {self.manually_opened}")
                    # Only auto-hide if not manually opened
                    if not self.manually_opened:
                        print("[DEBUG GUI] Scheduling auto-hide in 3 seconds...")
                        self.cancel_pending_hide()  # Cancel any existing hide
                        self.pending_hide_id = self.after(3000, self.auto_hide)
                    else:
                        print("[DEBUG GUI] Window was manually opened, skipping auto-hide")
                elif message.startswith("STATUS:"):
                    self.update_status(message.replace("STATUS: ", ""))
                elif message.startswith("HEARD:"):
                    self.add_log_entry("You", message.replace('HEARD: ', '').strip('"'), self.COLOR_USER)
                elif message.startswith("LOKI:"):
                    self.add_log_entry("LOKI", message.replace('LOKI: ', '').strip('"'), self.COLOR_LOKI)
                elif message.startswith("ERROR:"):
                    self.add_log_entry("ERROR", message.replace("ERROR: ", ""), "red")
                elif message.startswith("TEXT_INPUT:"):
                    # This message type is handled by loki_worker, not the GUI
                    pass
        except queue.Empty:
            pass
        finally:
            # Add this check before scheduling the next call
            if not self._is_closing:
                self.after(100, self.process_queue)

    def auto_hide(self):
        """Actually perform the auto-hide after delay."""
        if not self.manually_opened:
            print("[DEBUG GUI] Executing auto-hide now")
            self.fade_out()
            # Reset flag after auto-hide completes
            self.after(500, lambda: setattr(self, 'manually_opened', False))
        else:
            print("[DEBUG GUI] auto_hide cancelled - window was manually opened")
        self.pending_hide_id = None

    def update_status(self, status_text):
        self.is_processing = "Processing" in status_text
        self.is_pulsing = "LISTENING_ACTIVE" in status_text

        self.status_text_label.configure(text=status_text.replace("_", " ").title())

        if self.is_pulsing:
            self.pulse_animation()
        elif self.is_processing:
            self.update_spinner()
        else:  # Idle
            self.status_icon_label.configure(text="⚫", text_color=self.COLOR_STATUS)

    def add_log_entry(self, speaker, text, color):
        self.is_processing = False
        self.is_pulsing = False
        self.status_text_label.configure(text="Responding...")
        self.status_icon_label.configure(text="🔊", text_color=self.COLOR_LOKI)

        log_entry = ctk.CTkLabel(self.log_frame, text=f"{speaker}: {text}", font=self.FONT_LOG, text_color=color,
                                 wraplength=WINDOW_WIDTH - 60, justify="left")
        log_entry.pack(anchor="w", padx=10, pady=5)
        self.update_idletasks()
        self.log_frame._parent_canvas.yview_moveto(1.0)

    # --- Animation Methods ---
    def fade_in(self, alpha=0.0):
        if self.attributes("-alpha") >= 1.0: return
        self.attributes("-alpha", alpha)
        self.deiconify()
        self.lift()
        self.center_window()
        self.after(15, self.fade_in, alpha + 0.05)

    def fade_out(self, alpha=1.0):
        if alpha <= 0.0:
            self.withdraw()
            return
        self.attributes("-alpha", alpha)
        self.after(15, self.fade_out, alpha - 0.05)

    def pulse_animation(self):
        if not self.is_pulsing:
            self.status_icon_label.configure(text="⚫", text_color=self.COLOR_STATUS)
            return

        if self.pulse_color_value >= 255: self.pulse_direction = -1
        if self.pulse_color_value <= 150: self.pulse_direction = 1
        self.pulse_color_value += 10 * self.pulse_direction

        hex_color = f"#{self.pulse_color_value:02x}{self.pulse_color_value:02x}{self.pulse_color_value:02x}"
        self.status_icon_label.configure(text="🎤", text_color=hex_color)
        self.after(50, self.pulse_animation)

    def update_spinner(self):
        """Animates the spinner icon when LOKI is processing."""
        if self.is_processing:
            self.spinner_index = (self.spinner_index + 1) % len(self.spinner_chars)
            self.status_icon_label.configure(text=self.spinner_chars[self.spinner_index])
            self.after(100, self.update_spinner)

    def show_window(self):
        """Clears logs and brings the window to the front and center."""
        self.cancel_pending_hide()  # Cancel any pending hide
        self.manually_opened = True  # Mark as manually opened
        print(f"[DEBUG GUI] show_window() called: manually_opened = {self.manually_opened}")
        # Clear old logs
        for widget in self.log_frame.winfo_children(): widget.destroy()
        self.fade_in()

        self.deiconify()
        self.lift()
        self.center_window()
        self.attributes("-topmost", True)
        self.after(100, lambda: self.attributes("-topmost", False))

    def center_window(self):
        """Centers the window on the screen."""
        self.update_idletasks()
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width - WINDOW_WIDTH) // 2
        y = (screen_height - WINDOW_HEIGHT) // 2
        self.geometry(f"+{x}+{y}")

    def hide_window(self):
        self.fade_out()

    def minimize_to_tray(self):
        """Minimizes the window to the system tray (manual close via X button)."""
        self.cancel_pending_hide()  # Cancel any pending hide
        # Don't reset manually_opened here - it's used for auto-hide logic
        print(f"[DEBUG GUI] minimize_to_tray (manual close): manually_opened = {self.manually_opened}")
        self.fade_out()

    def send_text_input(self):
        """Sends text input to LOKI for processing."""
        text = self.text_input.get().strip()
        if not text:
            return

        # Clear the input field
        self.text_input.delete(0, 'end')

        # Show the window if it's hidden and mark as manually opened
        if not self.winfo_viewable():
            print("[DEBUG GUI] send_text_input: Window not visible, calling show_window()")
            self.show_window()
        else:
            # If already visible, ensure it stays open (user is typing)
            print(f"[DEBUG GUI] send_text_input: Window visible, setting manually_opened = True")
            self.cancel_pending_hide()  # Cancel any pending hide
            self.manually_opened = True

        # Send text to worker for processing
        self.message_queue.put(f"TEXT_INPUT:{text}")

    def start_move(self, event):
        # Don't start dragging if clicking on an Entry or Button widget
        widget = event.widget
        # Check if the widget is an entry or button, or if it's a child of one
        while widget:
            if widget == self.text_input or widget == self.send_button:
                return
            if isinstance(widget, (ctk.CTkEntry, ctk.CTkButton)):
                return
            widget = widget.master if hasattr(widget, 'master') else None
        self.x, self.y = event.x, event.y

    def stop_move(self, event):
        self.x, self.y = None, None

    def do_move(self, event):
        if self.x is not None and self.y is not None:
            deltax = event.x - self.x
            deltay = event.y - self.y
            self.geometry(f"+{self.winfo_x() + deltax}+{self.winfo_y() + deltay}")

    def setup_tray_icon(self):
        """Creates and runs the system tray icon."""
        try:
            icon_image = Image.open("icon.png")
            menu = TrayMenu(
                TrayMenuItem("Show LOKI", self.show_window, default=True),
                TrayMenuItem("Quit", self.quit_app)
            )
            self.tray_icon = TrayIcon("LOKI", icon_image, "LOKI Voice Assistant", menu)
            threading.Thread(target=self.tray_icon.run, daemon=True).start()
        except FileNotFoundError:
            self.add_log_entry("ERROR", "icon.png not found. No tray icon.", "red")

    def quit_app(self):
        """Handles the complete shutdown of the application."""
        print("Closing application...")
        self._is_closing = True  # Set the flag to stop all 'after' loops
        self.cancel_pending_hide()  # Cancel any pending operations

        if self.tray_icon:
            self.tray_icon.stop()

        self.stop_event.set()
        self.loki_thread.join(timeout=2)

        self.destroy()  # Destroy the window last


if __name__ == "__main__":
    app = LokiApp()
    app.mainloop()
