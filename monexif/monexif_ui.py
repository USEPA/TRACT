from guiFlds.guiFlds import guiFlds
from guiFlds.guiFldsTk import guiFldsTk

import monexif


class MonExifUI(guiFlds):

    # fields and commands, see guiFlds.py for documentation
    fldList = (
        ("imgdir", str, "Image Folder", "", "__OPENDIR__"),
        ("Scan", None),
    )

    def __init__(self):
        guiFlds.__init__(self)

    def Scan(self):
        print(monexif.image_list(self.fldDict()["imgdir"]))


guiFldsTk(MonExifUI())
