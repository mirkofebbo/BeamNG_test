import tkinter as tk
from tkinter import ttk
import tkinter as tk
import asyncio
from app import App

if __name__ == "__main__":
    root = tk.Tk()
    root.title("OSTI DE CALISSE DE TABARNAK V3")
    root.geometry("500x600")  # Set the initial size of the window

    # Grid layout
    root.grid_rowconfigure(0, weight=1)
    root.grid_columnconfigure([0, 1, 2], weight=1)

    loop = asyncio.get_event_loop()
    app = App(root, None)
    app.create_ui()