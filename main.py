import tkinter as tk
from tkinter import ttk
import asyncio
from app import App
import logging
import sys

# Setup logging
logging.basicConfig(filename='app.log', level=logging.DEBUG)

if __name__ == "__main__":
    try:
        root = tk.Tk()
        root.title("Car Simulation UI V1")
        root.geometry("400x400")  # Set the initial size of the window

        # Grid layout
        root.grid_rowconfigure(0, weight=1)
        root.grid_columnconfigure([0, 1, 2], weight=1)

        loop = asyncio.get_event_loop()
        app = App(root, None)
        app.create_ui()

        root.mainloop()
    except Exception as e:
        logging.exception("Exception occurred")
        print(f"An error occurred: {e}", file=sys.stderr)
        sys.exit(1)
