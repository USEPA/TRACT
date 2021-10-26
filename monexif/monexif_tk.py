import tkinter as tk
import tkinter.ttk as ttk
from tkinter import filedialog

from PIL import Image, ImageTk


def P(x, **kwargs):
    pack_kwargs = dict(padx=2, pady=2, side="left")
    if "pad" in kwargs:
        kwargs["padx"] = kwargs["pad"]
        kwargs["pady"] = kwargs["pad"]
        del kwargs["pad"]
    pack_kwargs.update(kwargs)
    x.pack(pack_kwargs)
    return x


def make_requester(outer, label, kind):
    line = ttk.Frame(outer)
    func = {
        "dir": filedialog.askdirectory,
        "open": filedialog.askopenfilename,
        "save": filedialog.asksaveasfilename,
    }[kind]
    line.button = P(ttk.Button(line, text="..", width=3), side="right")
    line.value = tk.StringVar()
    P(ttk.Entry(line, width=30, textvariable=line.value), side="right")

    def cb(event, func=func, entry=line.value):
        text = func()
        if text:
            entry.set(text)

    line.button.bind("<ButtonRelease-1>", cb)
    line.button.bind
    P(ttk.Label(line, text=label, width=15, anchor="e"), side="right")
    return line


class MonExifUI:
    """TTK GUI for monexif."""

    def __init__(self):

        self.root = tk.Tk()
        self.style = ttk.Style()
        self.initialize()
        self.root.mainloop()

    def initialize(self):
        """layout gui, set up callbacks"""

        self.nb = P(
            ttk.Notebook(self.root),
            anchor="nw",
            fill="both",
            expand="yes",
            pad=6,
        )
        self.nb.add(self.make_setup_frame(), text="Setup")
        self.nb.add(self.make_tools_frame(), text="Tools")
        self.nb.add(self.make_classify_frame(), text="Classify")
        # self.frm_setup.pack(fill="both", expand="yes")

    def make_setup_frame(self):
        pad = dict(anchor="nw", side="top")
        f = self.frm_setup = P(ttk.Frame(self.nb), **pad)
        self.path_pics = P(make_requester(f, "Image folder", "dir"), **pad)
        self.path_data = P(make_requester(f, "Data file", "open"), **pad)

        def cb(value=self.path_data.value):
            text = filedialog.asksaveasfilename()
            if text:
                value.set(text)

        P(ttk.Button(f, text="Create new data file", command=cb), **pad)

        return self.frm_setup

    def make_tools_frame(self):
        self.frm_tools = ttk.Frame()
        return self.frm_tools

    def make_classify_frame(self):
        f = self.frm_classify = ttk.Frame()
        tn = Image.open("./pics/recent/IMG_0291.JPG")
        tn.thumbnail((240, 240))
        self.img = ImageTk.PhotoImage(tn)
        ttk.Label(f, image=self.img).pack()
        but = ttk.Button(f, text="test")
        but.pack()
        f.pack(fill="both", expand="yes")
        return self.frm_classify


MonExifUI()
