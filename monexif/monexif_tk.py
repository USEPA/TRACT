import tkinter as tk
import tkinter.ttk as ttk
from tkinter import filedialog

from PIL import Image, ImageTk


class MonExifUI:
    """TTK GUI for monexif."""

    def __init__(self):

        self.root = tk.Tk()
        self.style = ttk.Style()
        self.initialize()
        self.root.mainloop()

    def initialize(self):
        """layout gui, set up callbacks"""

        self.nb = ttk.Notebook(self.root)
        self.nb.pack(anchor="nw", fill="both", expand="yes")
        self.nb.add(self.make_setup_frame(), text="Setup")
        self.nb.add(self.make_tools_frame(), text="Tools")
        self.nb.add(self.make_classify_frame(), text="Classify")
        # self.frm_setup.pack(fill="both", expand="yes")

    def make_setup_frame(self):
        f = self.frm_setup = ttk.Frame(self.nb)
        tn = Image.open("./pics/recent/IMG_0291.JPG")
        tn.thumbnail((240,240))
        self.img = ImageTk.PhotoImage(tn)
        ttk.Label(f, image=self.img).pack()
        but = ttk.Button(f, text="test")
        but.pack()
        f.pack(fill="both", expand="yes")

        return self.frm_setup

    def make_tools_frame(self):
        self.frm_tools = ttk.Frame()
        return self.frm_tools

    def make_classify_frame(self):
        self.frm_classify = ttk.Frame()
        return self.frm_classify


MonExifUI()
