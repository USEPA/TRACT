import platform
import sqlite3
from itertools import product
from pathlib import Path

import exif
import yaml
from dateutil.parser import parse
from openpyxl import Workbook, load_workbook


def create_data_file(path: str) -> None:
    """Read monexif_fields.yml and create a new workbook, *OVERWRITING* existing."""
    fields = yaml.safe_load(Path(__file__).with_name("monexif_fields.yml").open())
    wb = Workbook()
    ws = wb.active
    ws.title = "ImageData"
    for field_i, field in enumerate(fields["fields"]):
        ws.cell(0 + 1, field_i + 1, field)
    wb.save(path)


def insert_row(con, fields: list[str], row: list) -> None:
    sql = "insert into imgdata (%s)" % ",".join(fields) + "values (%s)" % ",".join(
        "?" * len(fields)
    )


def xlsx_to_sqlite(xlsx_path: str, sqlite_path) -> None:
    """Convert .xlsx to .db, *OVERWRITING* existing imgdata table."""
    fields = yaml.safe_load(Path(__file__).with_name("monexif_fields.yml").open())
    wb = load_workbook(xlsx_path)
    ws = wb.active
    field_type = {k: v["type"] for k, v in fields["fields"].items()}
    fields = [cell.value for cell in ws[0 + 1]]
    sql = [field + " " + field_type.get(field, "text") for field in fields]
    sql = "create table imgdata (\n" + ",\n".join(sql) + "\n)"
    con = sqlite3.connect(sqlite_path)
    con.execute("drop table if exists imgdata")
    con.execute(sql)
    for row in ws[1 + 1 :]:
        insert_row(con, fields, row)


def image_list(path: str) -> list[str]:
    """List of images from path *and its subfolders*."""

    if platform.system() == "Windows":
        transforms = [lambda x: x]  # case insensitive filesystem
    else:
        transforms = (str.upper, str.lower, str.title)

    image_paths = []
    #  Iterate .jpg, .JPEG, .Png etc.
    for transform, extension in product(transforms, ("jpg", "png", "jpeg", "gif")):
        ext = transform(extension)
        image_paths.extend(
            [str(i.relative_to(Path.cwd())) for i in Path(path).rglob(f"*.{ext}")]
        )
    return image_paths


def read_exif(path: str) -> dict:
    img = exif.Image(Path(path).open("rb"))
    result = {}
    for key in img.list_all():
        try:
            result[key] = getattr(img, key)
        except Exception:  # a zoo of different exceptions possible
            continue
    # import pprint
    # pprint.pprint(result)
    return result


def image_time_filename(exif: dict) -> str:
    """FIXME: assumes .jpg"""
    return exif["datetime_original"].replace(":", "").replace(" ", "_") + ".jpg"


def new_image_names(paths: list[str], do_renames: bool = False) -> list[(str, str)]:
    renames = []
    for img_path in paths:
        exif = read_exif(img_path)
        name = image_time_filename(exif)
        if Path(img_path).name != name:
            new_path = Path(img_path).with_name(name)
            renames.append((img_path, new_path))
            if do_renames:
                Path(img_path).rename(new_path)
    return renames


if __name__ == "__main__":
    # print(image_list("pics"))
    # create_data_file("test.xlsx")
    # xlsx_to_sqlite("test.xlsx", "test.db")
    print(new_image_names(image_list("pics")))
