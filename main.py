import queue
import threading

from loki_worker import LokiWorker


def main():
    """
    Console-based front-end for the LOKI Voice Assistant.
    
    This script initializes the LokiWorker in a separate thread and then
    listens for messages from it, printing them to the console.
    """
    message_queue = queue.Queue()
    stop_event = threading.Event()

    # 1. Create and start the LOKI worker thread
    print("--- Initializing LOKI Console Mode ---")
    worker = LokiWorker(message_queue, stop_event)
    worker_thread = threading.Thread(target=worker.run, daemon=True)
    worker_thread.start()

    # 2. Main loop to process messages from the worker
    try:
        while worker_thread.is_alive():
            try:
                # Wait for a message from the worker thread
                message = message_queue.get(timeout=1.0)

                # Simple parsing of the message prefix to format the output
                if message.startswith("STATUS:"):
                    # Light blue for status messages
                    print(f"\033[94m[STATUS] {message.replace('STATUS: ', '')}\033[0m")
                elif message.startswith("HEARD:"):
                    # Yellow for user's speech
                    print(f"\033[93m[HEARD]  {message.replace('HEARD: ', '')}\033[0m")
                elif message.startswith("LOKI:"):
                    # Green for LOKI's response
                    print(f"\033[92m[LOKI]   {message.replace('LOKI: ', '')}\033[0m")
                elif message.startswith("ERROR:"):
                    # Red for errors
                    print(f"\033[91m[ERROR]  {message.replace('ERROR: ', '')}\033[0m")
                else:
                    print(message)  # Default print for any other message

            except queue.Empty:
                # The timeout allows this loop to check if the thread is still alive
                # and to be interrupted by Ctrl+C.
                continue

    except KeyboardInterrupt:
        print("\n🛑 SIGINT received. Shutting down LOKI...")
    finally:
        # 3. Signal the worker thread to stop and wait for it to clean up
        if worker_thread.is_alive():
            stop_event.set()
            worker_thread.join(timeout=5)  # Wait for the thread to finish
        print("--- LOKI Console Mode Terminated ---")


if __name__ == '__main__':
    main()
