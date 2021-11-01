import os
import sys
import tkinter as tk
import tkinter.ttk as ttk
from tkinter import filedialog

from PIL import Image, ImageTk

import monexif

DEVMODE = os.environ.get("MONEXIF_DEVMODE")
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
        if DEVMODE:
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
        f = ttk.Frame()
        self.console = P(tk.Text(f), side="right", expand="yes", fill="both")
        self.nb.add(self.make_setup_frame(), text="File")
        self.nb.add(self.make_classify_frame(), text="Classify")
        # self.nb.add(self.make_tools_frame(), text="Tools")
        if DEVMODE:
            self.nb.select(1)
        stack.add(self.nb)

        def cb(self=self):
            path = self.path_data.value.get()
            monexif.sqlite_to_xlsx(self.con, path)
            print(f"Saved {path}")

        P(ttk.Button(f, text="Save data to file", command=cb), anchor="nw", side="left")
        stack.add(f)

        print("Init. complete.")

    def make_setup_frame(self):
        pad = dict(anchor="nw", side="top")
        f = self.frm_setup = P(ttk.Frame(self.nb), **pad)
        self.path_pics = P(make_requester(f, "Image folder", "dir"), **pad)
        self.path_pics.value.set("SET THIS FIRST")

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
        else:
            self.path_data.value.set("SET THIS NEXT")

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
            path = path_pics.value.get()
            imgs = monexif.image_list(path)
            renames = monexif.new_image_names(path, imgs)
            print(f"{len(imgs)} images, {len(renames)} need renaming")

        P(ttk.Button(f, text="Check image file names", command=cb), **pad)

        def cb(path_pics=self.path_pics):
            path = path_pics.value.get()
            imgs = monexif.image_list(path)
            renames = monexif.new_image_names(path, imgs, do_renames=True)
            print(f"{len(imgs)} images, {len(renames)} renamed")

        P(ttk.Button(f, text="Rename images", command=cb), **pad)

        def cb(self=self):
            monexif.load_new(self.con, self.path_pics.value.get())
            self.update_images()

        P(ttk.Button(f, text="Load new images", command=cb), **pad)

        def cb(self=self):
            path = self.path_data.value.get()
            monexif.sqlite_to_xlsx(self.con, path)
            print(f"Saved {path}")

        P(ttk.Button(f, text="Save data to file", command=cb), **pad)

        return self.frm_setup

    def make_tools_frame(self):
        """Not used"""
        f = self.frm_tools = ttk.Frame()

        def cb(path_pics=self.path_pics):
            path = path_pics.value.get()
            imgs = monexif.image_list(path)
            renames = monexif.new_image_names(path, imgs)
            print(f"{len(imgs)} images, {len(renames)} need renaming")

        P(ttk.Button(f, text="Check image file names", command=cb))

        def cb(path_pics=self.path_pics):
            path = path_pics.value.get()
            imgs = monexif.image_list(path)
            renames = monexif.new_image_names(path, imgs, do_renames=True)
            print(f"{len(imgs)} images, {len(renames)} renamed")

        P(ttk.Button(f, text="Rename images", command=cb))

        return self.frm_tools

    def update_inputs(self):
        cur = self.con.cursor()
        cur.execute(
            "select * from imgdata where image_path = ?",
            [self.frm_classify.view.path],
        )
        data = {k[0]: v for k, v in zip(cur.description, next(cur))}
        rec = self.frm_classify.rec
        for item in rec.winfo_children():
            item.destroy()
        for field in monexif.field_defs()["fields"].values():
            self.render(rec, field, data)
        return data

    def make_classify_frame(self):
        f = self.frm_classify = ttk.Frame()

        def cb(self=self):
            data = self.update_inputs()
            print(data["image_path"], data["image_time"])

        f.input = ttk.Frame()

        f.view = P(self.make_browser(f, command=cb), side="right")
        f.rec = P(ttk.Frame(f), side="left", anchor="nw")

        return f

    def render(self, outer, field, data):
        if not field.get("show") and not field.get("input"):
            return
        P(ttk.Label(outer, text=field["name"]), side="top", anchor="nw")
        value = data.get(field["name"])
        if field.get("show"):
            P(ttk.Label(outer, text=value), side="top", anchor="nw")
        elif field.get("input"):
            if field["name"] == "related":
                P(self.make_related(outer, field, data), side="top", anchor="nw")
            elif field.get("values"):

                input = P(
                    ttk.Combobox(outer, values=field["values"]),
                    side="top",
                    anchor="nw",
                )

                def cb(event, self=self, data=data, key=field["name"], input=input):
                    print(key, input.get())
                    self.con.execute(
                        f"update imgdata set {key} = ? where image_path = ?",
                        [input.get(), data["image_path"]],
                    )

                input.bind("<<ComboboxSelected>>", cb)
                if value in field["values"]:
                    input.set(field["values"].index(value))

    def make_related(self, outer, field, data):
        f = P(ttk.Frame(outer))
        # P(ttk.Label(f, text=data["related"]), side="top")

        def cb():
            top = tk.Toplevel(self.root)
            browser = P(self.make_browser(top), side="top", fill="x")
            path = None
            if data["related"]:
                res = self.con.execute(
                    "select image_path from imgdata where image_id=?", [data["related"]]
                )
                try:
                    path = next(res)[0]
                except StopIteration:
                    pass
            if path is None:
                path = data["image_path"]
            browser.path = path
            browser.show(browser)

            def cb(browser=browser, path=data["image_path"]):
                browser.path = path
                browser.show(browser)

            P(
                ttk.Button(top, text="Original", command=cb),
                side="left",
                fill="x",
                expand="y",
            )

            def cb(data=data, browser=browser, top=top, self=self):
                monexif.set_related(self.con, browser.path, data["image_path"])
                top.destroy()
                self.update_inputs()

            P(
                ttk.Button(top, text="Select", command=cb),
                side="left",
                fill="x",
                expand="y",
            )

            def cb(top=top):
                top.destroy()

            P(
                ttk.Button(top, text="Cancel", command=cb),
                side="left",
                fill="x",
                expand="y",
            )

        if data.get("related"):
            res = self.con.execute(
                "select image_path from imgdata where image_id = ?", [data["related"]]
            )
            path = next(res)[0]
            tn = Image.open(path)
            tn.thumbnail((200, 200))
            f.pimg = ImageTk.PhotoImage(tn)
            P(ttk.Label(f, image=f.pimg), side="top")

        P(ttk.Button(f, width=25, text="Select or view", command=cb), side="top")
        return f

    def make_browser(self, outer, command=None):
        nav = [
            (-9999, "|<"),
            (-1000, "≪≪"),
            (-100, "⋘"),
            (-10, "≪"),
            (-1, "<"),
            (+1, ">"),
            (+10, "≫"),
            (+100, "⋙"),
            (+1000, "≫≫"),
            (+9999, ">|"),
        ]
        view = ttk.Frame(outer)
        view.img = P(ttk.Label(view, text="Click any arrow to start"), side="top")
        view.path = None
        row = P(ttk.Frame(view), side="top")

        def show(view):
            tn = Image.open(view.path)
            tn.thumbnail((700, 700))
            view.pimg = ImageTk.PhotoImage(tn)
            view.img.configure(image=view.pimg)

        view.show = show

        for n, text in nav:

            def cb(self=self, view=view, n=n, command=command):
                if view.path is None:
                    view.path = self.images[0]
                else:
                    idx = self.images.index(view.path)
                    idx += n
                    idx = max(0, min(idx, len(self.images) - 1))
                    view.path = self.images[idx]
                view.show(view)
                if command:
                    command()

            P(ttk.Button(row, text=text, command=cb, width=4))
        view.pack(fill="both", expand="yes")
        return view


MonExifUI()
