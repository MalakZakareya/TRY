from io import BytesIO
from typing import Any, TypedDict, cast

import pymupdf
from PIL import Image


ALLOWED_DESIGN_EXTENSIONS = {
    ".png",
    ".jpg",
    ".jpeg",
    ".pdf",
}

MAX_DESIGN_FILE_SIZE = 10 * 1024 * 1024


class DesignProcessingError(Exception):
    pass


class DesignResult(TypedDict):
    filename: str
    file_type: str
    file_size: int
    page_count: int
    content_type: str


def get_file_extension(
    filename: str,
) -> str:
    filename = filename.lower().strip()

    for extension in ALLOWED_DESIGN_EXTENSIONS:
        if filename.endswith(extension):
            return extension

    return ""


def validate_image(
    content: bytes,
) -> None:
    try:
        image = Image.open(
            BytesIO(content)
        )

        image.verify()

    except Exception as exc:
        raise DesignProcessingError(
            "The uploaded image could not be read."
        ) from exc


def get_pdf_page_count(
    content: bytes,
) -> int:
    try:
        document = pymupdf.open(
            stream=content,
            filetype="pdf",
        )

        page_count: int = len(document)

        document.close()

        if page_count <= 0:
            raise DesignProcessingError(
                "The uploaded PDF has no pages."
            )

        return page_count

    except DesignProcessingError:
        raise

    except Exception as exc:
        raise DesignProcessingError(
            "The uploaded PDF could not be read."
        ) from exc


def convert_pdf_to_images(
    content: bytes,
) -> list[bytes]:
    try:
        document: Any = pymupdf.open(
            stream=content,
            filetype="pdf",
        )

        images: list[bytes] = []

        page_count: int = len(document)

        for page_number in range(page_count):
            page: Any = document.load_page(
                page_number
            )

            pixmap: Any = page.get_pixmap(
                dpi=150,
                alpha=False,
            )

            raw_image: Any = pixmap.tobytes(
                "png"
            )

            image_bytes = cast(
                bytes,
                raw_image,
            )

            images.append(
                image_bytes
            )

        document.close()

        if not images:
            raise DesignProcessingError(
                "No pages could be converted "
                "from the PDF."
            )

        return images

    except DesignProcessingError:
        raise

    except Exception as exc:
        raise DesignProcessingError(
            "The PDF pages could not be "
            "converted to images."
        ) from exc


def prepare_design_images(
    filename: str,
    content: bytes,
) -> list[bytes]:
    extension = get_file_extension(
        filename
    )

    if extension == ".pdf":
        return convert_pdf_to_images(
            content
        )

    validate_image(
        content
    )

    return [content]


def process_design_file(
    filename: str,
    content: bytes,
) -> DesignResult:

    if not filename:
        raise DesignProcessingError(
            "Uploaded design must have a filename."
        )

    extension = get_file_extension(
        filename
    )

    if not extension:
        raise DesignProcessingError(
            "Unsupported design file. "
            "Please upload PNG, JPG, JPEG, or PDF."
        )

    if not content:
        raise DesignProcessingError(
            "Uploaded design is empty."
        )

    if len(content) > MAX_DESIGN_FILE_SIZE:
        raise DesignProcessingError(
            "Design file is too large. "
            "Maximum size is 10 MB."
        )

    if extension == ".pdf":
        page_count: int = get_pdf_page_count(
            content
        )

        content_type: str = "pdf"

    else:
        validate_image(
            content
        )

        page_count = 1
        content_type = "image"

    return {
        "filename": filename,
        "file_type": extension.lstrip("."),
        "file_size": len(content),
        "page_count": page_count,
        "content_type": content_type,
    }