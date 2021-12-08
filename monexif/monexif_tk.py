import os
import sys
import tkinter as tk
import tkinter.ttk as ttk
from pathlib import Path
from tkinter import filedialog, messagebox
from uuid import uuid4

from PIL import Image, ImageTk

import monexif

DEVMODE = os.environ.get("MONEXIF_DEVMODE")
SQLPATH = ":memory:"


def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


print(resource_path(""))
print(os.listdir(resource_path("")))


def P(widget, **kwargs):
    """Convenience wrapper to pack a widget"""
    pack_kwargs = dict(padx=2, pady=2, side="left")
    if "pad" in kwargs:
        kwargs["padx"] = kwargs["pad"]
        kwargs["pady"] = kwargs["pad"]
        del kwargs["pad"]
    pack_kwargs.update(kwargs)
    widget.pack(pack_kwargs)
    return widget


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
        # bind window closing callback
        self.root.protocol("WM_DELETE_WINDOW", self.exiting)
        self.show_version()
        self.root.mainloop()

    def show_version(self):
        path = Path(__file__)
        for level in range(2):
            path = path.parent
            if (path / "version.txt").exists():
                print("Version: " + (path / "version.txt").read_text())
                return
        print("Couldn't find version.txt for version information")

    def exiting(self):
        message = "OK to exit losing unsaved work,\nCancel to abort and save work"
        if messagebox.askokcancel(message, message):
            self.root.destroy()

    def update_images(self):
        """Loads list of image paths by date order"""
        self.images = [
            i[0]
            for i in self.con.execute(
                "select observation_id from imgdata "
                "order by image_time, group_number asc"
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
            self.save()

        P(ttk.Button(f, text="Save data to file", command=cb), anchor="nw", side="left")
        stack.add(f)

        if len(sys.argv) > 1:
            self.path_pics.value.set(sys.argv[1])
            self.path_data.value.set(sys.argv[2])
            self.cb_load()

        print("Init. complete.")

    def save(self):
        self.pre_save_update()
        path = self.path_data.value.get()
        monexif.sqlite_to_xlsx(self.con, path)
        print(f"Saved {path}")

    def pre_save_update(self):
        paths = [i[0] for i in self.con.execute("select image_path from imgdata")]
        full_paths = [(self.absolute_path(i), i) for i in paths]
        self.con.executemany(
            "update imgdata set image_path_full = ? where image_path = ?", full_paths
        )

    def cb_load(self):
        path = self.path_data.value.get()
        print(f"Loading {path}")
        self.con = monexif.xlsx_to_sqlite(path, SQLPATH)
        self.update_images()
        self.update_inputs()
        print(f"Data loaded, {len(self.images)} records")

    def make_setup_frame(self):
        pad = dict(anchor="nw", side="top")
        f = self.frm_setup = P(ttk.Frame(self.nb), **pad)
        self.path_pics = P(make_requester(f, "Image folder", "dir"), **pad)
        self.path_pics.value.set("SET THIS FIRST")

        self.path_data = P(
            make_requester(f, "Data file", "open", callback=self.cb_load), **pad
        )
        self.path_data.value.set("SET THIS NEXT")

        def cb(value=self.path_data.value):
            text = filedialog.asksaveasfilename()
            if text:
                self.path_data.value.set(text)
                print(f"Creating {text}")
                monexif.create_data_file(text)
                self.cb_load()

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
            self.save()

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

    def observation_data(self, obs_id):
        cur = self.con.cursor()
        cur.execute("select * from imgdata where observation_id = ?", [obs_id])
        try:
            data = {k[0]: v for k, v in zip(cur.description, next(cur))}
        except StopIteration:
            data = {}
        return data

    def update_inputs(self):
        data = self.observation_data(self.frm_classify.view.path)
        rec = self.frm_classify.rec
        for item in rec.winfo_children():
            item.destroy()
        if data:
            for field in monexif.field_defs()["fields"].values():
                self.render(rec, field, data)
        return data

    def make_classify_frame(self):
        f = self.frm_classify = ttk.Frame()

        def cb(self=self):
            data = self.update_inputs()
            print(data["image_path"], data["image_time"])

        f.input = ttk.Frame()

        f.view = P(self.make_browser(f, command=cb, info=True), side="right")
        f.rec = P(ttk.Frame(f), side="left", anchor="nw")

        return f

    def render(self, outer, field, data):
        if not field.get("show") and not field.get("input"):
            return
        row = P(ttk.Frame(outer), side="top", anchor="nw")
        P(ttk.Label(row, text=field["name"], width=15), side="left", anchor="e")
        value = data.get(field["name"])
        if field.get("show"):
            truncated = str(value)
            if isinstance(value, str) and len(truncated) > 20:
                truncated = truncated[:10] + "…" + truncated[-10:]
            P(ttk.Label(row, text=truncated), side="left", anchor="nw")
            if field["name"] == "group_number":
                P(self.add_button(row, field, data), side="top", anchor="nw")
        elif field.get("input"):
            if field["name"] == "related":
                P(self.make_related(outer, field, data), side="top", anchor="nw")
            elif field.get("values"):
                input = P(
                    ttk.Combobox(row, values=field["values"]),
                    side="left",
                    anchor="nw",
                )

                def cb(event, self=self, data=data, key=field["name"], input=input):
                    print(key, input.get())
                    print(self.record_temp.get())
                    self.con.execute(
                        f"update imgdata set {key} = ? where observation_id = ?",
                        [input.get(), data["observation_id"]],
                    )
                    self.frm_classify.view.show(self.frm_classify.view)

                input.bind("<<ComboboxSelected>>", cb)
                if value in field["values"]:
                    input.set(value)
            else:
                self.record_temp = content = tk.StringVar()
                if value is not None:
                    content.set(str(value))

                def cb(*args, self=self, data=data, key=field["name"], input=content):
                    print(key, input.get())
                    self.con.execute(
                        f"update imgdata set {key} = ? where observation_id = ?",
                        [input.get(), data["observation_id"]],
                    )
                    self.frm_classify.view.show(self.frm_classify.view)
                    return True

                input = P(
                    ttk.Entry(row),
                    side="left",
                    anchor="nw",
                )
                input["textvariable"] = content
                # input.bind("<<KeyRelease>>", cb)
                content.trace_add("write", cb)

    def add_button(self, outer, field, data):
        """Add a button to add a new group_number entry"""

        def cb(field=field, data=data):
            count = next(
                self.con.execute(
                    "select count(*) from imgdata where image_path=?",
                    [data["image_path"]],
                )
            )[0]
            new = dict(data)
            new["group_number"] = count + 1
            new["observation_id"] = uuid4().hex
            for field_name, field in monexif.field_defs()["fields"].items():
                if "clear_to" in field and field_name in new:
                    new[field_name] = field["clear_to"]
            monexif.insert_row(self.con, new)
            new = list(
                self.con.execute(
                    "select observation_id from imgdata where image_path=? "
                    "order by group_number asc",
                    [data["image_path"]],
                )
            )
            self.frm_classify.view.path = new[-1][0]  # first field from last record
            self.update_images()
            self.update_inputs()

        return ttk.Button(outer, text="Add group", command=cb)

    def make_related(self, outer, field, data):
        f = P(ttk.Frame(outer))

        def cb():
            top = tk.Toplevel(self.root)
            browser = P(self.make_browser(top, info=True), side="top", fill="x")
            browser.path = data.get("related") or data["observation_id"]
            browser.show(browser)

            def cb(browser=browser, path=data["observation_id"]):
                browser.path = path
                browser.show(browser)

            P(
                ttk.Button(top, text="Original", command=cb),
                side="left",
                fill="x",
                expand="y",
            )

            def cb(data=data, browser=browser, top=top, self=self):
                monexif.set_related(self.con, browser.path, data["observation_id"])
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

        P(ttk.Button(f, text="Add", command=cb), side="top")

        res = self.con.execute(
            "select * from imgdata where group_id = ? and observation_id != ?",
            [data["group_id"], data["observation_id"]],
        )
        for other in monexif.named_tuples(res):
            line = P(ttk.Frame(f), side="top")
            P(ttk.Label(line, text=other.image_time), side="left")

            def cb_jump(self=self, data=other):
                self.frm_classify.view.path = data.observation_id
                self.frm_classify.view.show(self.frm_classify.view, self=self)
                self.update_inputs()

            P(ttk.Button(line, text="Go to", command=cb_jump, width=7), side="left")

            def cb(self=self, data=other):
                monexif.unset_related(self.con, data.observation_id)
                self.update_inputs()

            P(ttk.Button(line, text="Unrelate", command=cb, width=7), side="left")
        else:
            P(ttk.Frame(f, width=200), side="top")  # to stop image moving

        return f

    def relative_path(self, path):
        if not Path(path).is_absolute():
            #  .relative_to requires two absolute paths
            path = self.absolute_path(path)
        return str(Path(path).relative_to(self.path_pics.value.get()))

    def absolute_path(self, path):
        return str(Path(self.path_pics.value.get()) / path)

    def img_path(self, obs_id):
        return next(
            self.con.execute(
                "select image_path from imgdata where observation_id=?", [obs_id]
            )
        )[0]

    def make_browser(self, outer, command=None, info=False):
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

        def show(view, self=self):
            tn = Image.open(self.absolute_path(self.img_path(view.path)))
            tn.thumbnail((700, 700))
            view.pimg = ImageTk.PhotoImage(tn)
            view.img.configure(image=view.pimg)
            if view.info:
                data = self.observation_data(view.path)
                view.info.configure(
                    text="{image_time} Group: {group_number} {adults_n}/{children_n}/"
                    "{pets_n} {direction} {activity}".format_map(data)
                )

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

        if info:
            view.info = P(ttk.Label(view, text="info"), side="top")
        else:
            view.info = False

        view.pack(fill="both", expand="yes")
        return view


MonExifUI()
