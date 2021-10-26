from itertools import product
from pathlib import Path
from openpyxl import Workbook, load_workbook
import yaml
import sqlite3

def create_data_file(path: str) -> None:
    """Read monexif_fields.yml and create a new workbook, *OVERWRITING* existing."""
    fields = yaml.safe_load(Path(__file__).with_name("monexif_fields.yml").open())
    wb = Workbook()
    ws = wb.active
    ws.title = "ImageData"
    for field_i, field in enumerate(fields['fields']):
        ws.cell(0+1, field_i+1, field)
    wb.save(path)

def xlsx_to_sqlite(xlsx_path: str, sqlite_path) -> None:
    """Convert .xlsx to .db, *OVERWRITING* existing .db."""
    fields = yaml.safe_load(Path(__file__).with_name("monexif_fields.yml").open())
    wb = load_workbook(xlsx_path)
    ws = wb.active
    sql = [cell.value + " " + (fields['fields'].get(cell.value) or {"type": "text"})["type"] for cell in ws[0+1]]
    sql = "create table imgdata (\n"+",\n".join(sql)+"\n)"
    con = sqlite3.connect(sqlite_path)
    con.execute("drop table if exists imgdata")
    con.execute(sql)


def image_list(path: str) -> list[str]:
    """List of images from path *and its subfolders*."""

    image_paths = []
    #  Iterate .jpg, .JPEG, .Png etc.
    for transform, extension in product(
        (str.upper, str.lower, str.title), ("jpg", "png", "jpeg", "gif")
    ):
        ext = transform(extension)
        image_paths.extend(
            [str(i.relative_to(path)) for i in Path(path).rglob(f"*.{ext}")]
        )
    return image_paths


if __name__ == "__main__":
    # print(image_list("."))
    # create_data_file("test.xlsx")
    xlsx_to_sqlite("test.xlsx", "test.db")
