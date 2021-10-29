import sys
import tkinter as tk
import tkinter.ttk as ttk
from tkinter import filedialog

from PIL import Image, ImageTk

import monexif

SQLPATH = ":memory:"


def P(x, **kwargs):
    pack_kwargs = dict(padx=2, pady=2, side="left")
    if "pad" in kwargs:
        kwargs["padx"] = kwargs["pad"]
        kwargs["pady"] = kwargs["pad"]
        del kwargs["pad"]
    pack_kwargs.update(kwargs)
    x.pack(pack_kwargs)
    return x


def make_requester(outer, label, kind, callback=None):
    line = ttk.Frame(outer)
    func = {
        "dir": filedialog.askdirectory,
        "open": filedialog.askopenfilename,
        "save": filedialog.asksaveasfilename,
    }[kind]
    line.value = tk.StringVar()

    def cb(func=func, entry=line.value, callback=callback):
        text = func()
        if text:
            entry.set(text)
            if callback is not None:
                callback()

    line.button = P(ttk.Button(line, text="..", width=3, command=cb), side="right")
    P(ttk.Entry(line, width=30, textvariable=line.value), side="right")
    # line.button.bind("<ButtonRelease-1>", cb)
    P(ttk.Label(line, text=label, width=15, anchor="e"), side="right")
    return line


class MonExifUI:
    """TTK GUI for monexif."""

    def __init__(self):

        self.images = []  # list of images in time order
        self.image_i = 0  # current image index
        self.con = None  # DB connection
        # switch print() to console widget
        self.stdout = sys.stdout
        self.stderr = sys.stderr
        sys.stdout = self
        sys.stderr = self
        # Tk setup
        self.root = tk.Tk()
        self.style = ttk.Style()
        self.initialize()  # build UI
        self.root.mainloop()

    def update_images(self):
        """Loads list of image paths by date order"""
        self.images = [
            i[0]
            for i in self.con.execute(
                "select image_path from imgdata order by image_time asc"
            )
        ]

    def write(self, text):
        self.stdout.write(text)
        self.stdout.write("\n")
        # self.console.configure(state=tk.NORMAL)
        self.console.insert(tk.END, text)
        # self.console.configure(state=tk.DISABLED)
        self.console.see(tk.END)
        self.root.update()

    def initialize(self):
        """layout gui, set up callbacks"""

        stack = P(ttk.PanedWindow(self.root), fill="both", expand="yes")
        self.nb = P(
            ttk.Notebook(stack),
            fill="both",
            expand="yes",
            pad=6,
            side="top",
        )

        # create this first so output to console works
        self.console = P(tk.Text(stack), pad=6, side="top")
        self.nb.add(self.make_classify_frame(), text="Classify")
        self.nb.add(self.make_setup_frame(), text="File")
        # self.nb.add(self.make_tools_frame(), text="Tools")
        stack.add(self.nb)
        stack.add(self.console)

        print("Init. complete.")

    def make_setup_frame(self):
        pad = dict(anchor="nw", side="top")
        f = self.frm_setup = P(ttk.Frame(self.nb), **pad)
        self.path_pics = P(make_requester(f, "Image folder", "dir"), **pad)

        def cb_load(self=self):
            path = self.path_data.value.get()
            print(f"Loading {path}")
            self.con = monexif.xlsx_to_sqlite(path, SQLPATH)
            self.update_images()
            print(f"Data loaded, {len(self.images)} records")

        self.path_data = P(
            make_requester(f, "Data file", "open", callback=cb_load), **pad
        )
        if len(sys.argv) > 1:
            self.path_data.value.set(sys.argv[1])
            cb_load(self)

        def cb(value=self.path_data.value):
            text = filedialog.asksaveasfilename()
            if text:
                self.path_data.value.set(text)
                print(f"Creating {text}")
                monexif.create_data_file(text)
                cb_load(self)

        P(ttk.Button(f, text="Create new data file", command=cb), **pad)

        def cb(self=self):
            monexif.check_new(self.con, self.path_pics.value.get())

        P(ttk.Button(f, text="Check for new images", command=cb), **pad)

        def cb(path_pics=self.path_pics):
            imgs = monexif.image_list(path_pics.value.get())
            renames = monexif.new_image_names(imgs)
            print(f"{len(imgs)} images, {len(renames)} need renaming")

        P(ttk.Button(f, text="Check image file names", command=cb), **pad)

        def cb(path_pics=self.path_pics):
            imgs = monexif.image_list(path_pics.value.get())
            renames = monexif.new_image_names(imgs, do_renames=True)
            print(f"{len(imgs)} images, {len(renames)} renamed")

        P(ttk.Button(f, text="Rename images", command=cb), **pad)
        def cb(self=self):
            monexif.load_new(self.con, self.path_pics.value.get())

        P(ttk.Button(f, text="Load new images", command=cb), **pad)

        def cb(self=self):
            monexif.sqlite_to_xlsx(self.con, self.path_data.value.get())

        P(ttk.Button(f, text="Save data to file", command=cb), **pad)

        return self.frm_setup

    def make_tools_frame(self):
        f = self.frm_tools = ttk.Frame()

        def cb(path_pics=self.path_pics):
            imgs = monexif.image_list(path_pics.value.get())
            renames = monexif.new_image_names(imgs)
            print(f"{len(imgs)} images, {len(renames)} need renaming")

        P(ttk.Button(f, text="Check image file names", command=cb))

        def cb(path_pics=self.path_pics):
            imgs = monexif.image_list(path_pics.value.get())
            renames = monexif.new_image_names(imgs, do_renames=True)
            print(f"{len(imgs)} images, {len(renames)} renamed")

        P(ttk.Button(f, text="Rename images", command=cb))

        return self.frm_tools

    def make_classify_frame(self):
        f = self.frm_classify = ttk.Frame()

        def cb(self=self):
            cur = self.con.cursor()
            cur.execute(
                "select * from imgdata where image_path = ?",
                [self.frm_classify.view.path],
            )
            rec = {k[0]: v for k, v in zip(cur.description, next(cur))}
            print(rec["image_path"], rec["image_time"])

        f.view = P(self.make_browser(f, command=cb), side="top")
        return f

    def make_browser(self, outer, command=None):
        nav = [
            (-9999, "|<"),
            (-100, "<<<"),
            (-10, "<<"),
            (-1, "<"),
            (+1, ">"),
            (+10, ">>"),
            (+100, ">>>"),
            (+9999, ">|"),
        ]
        view = ttk.Frame(outer)
        view.img = P(ttk.Label(view, text="Image"), side="top")
        view.path = None
        row = P(ttk.Frame(view), side="top")
        for n, text in nav:

            def cb(self=self, view=view, n=n, command=command):
                if view.path is None:
                    view.path = self.images[0]
                else:
                    idx = self.images.index(view.path)
                    idx += n
                    idx = max(0, min(idx, len(self.images) - 1))
                    view.path = self.images[idx]
                tn = Image.open(view.path)
                tn.thumbnail((700, 700))
                view.pimg = ImageTk.PhotoImage(tn)
                view.img.configure(image=view.pimg)
                if command:
                    command()

            P(ttk.Button(row, text=text, command=cb))
        view.pack(fill="both", expand="yes")
        return view


MonExifUI()
