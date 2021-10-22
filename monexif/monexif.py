from itertools import product
from pathlib import Path


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
    print(image_list("."))
