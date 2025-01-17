from typing import Any, Literal, Union
from io import BytesIO
import os
import requests
from PIL import Image
import numpy as np
import tempfile
import base64
import re

# TODO:
# support other input types such as lists, tensors, ...

def load_img(
    img: Union[str, bytes, np.ndarray, Image.Image],
    output_type: Literal["pil", "numpy", "str", "base64"] = "pil",
    input_type: Literal["auto", "base64", "file", "url", "numpy", "pil"] = "auto",
) -> Any:
    """Loads an image from various sources and returns it in a specified format.

    Args:
        img: The input image. Can be a base64 string, a file path, a URL,
            a NumPy array, or a Pillow Image object.
        output_type: The desired output type. Can be "pil" (Pillow Image),
            "numpy" (NumPy array), "str" (file path), or "base64" (base64 string).
        input_type: The type of the input image. If set to "auto", the function
            will try to automatically determine the type. Otherwise, it will
            assume the input is of the specified type.

    Returns:
        The loaded image in the specified output type.

    Raises:
        ValueError: If the input type is invalid or if the image cannot be loaded.

    Examples:
        ```python
        from loadimg import load_img

        # Load an image from a base64 string and return it as a Pillow Image.
        img = load_img(img="data:image/png;base64,...", output_type="pil")

        # Load an image from a file path and return it as a NumPy array.
        img = load_img(img="path/to/image.jpg", output_type="numpy")

        # Load an image from a URL and return it as a file path.
        img = load_img(img="https://example.com/image.png", output_type="str")

        # Load an image from a NumPy array and return it as a base64 string.
        img = load_img(img=np.array(...), output_type="base64")
        ```
    """
    img = load(img, input_type)
    if output_type == "pil":
        return img
    elif output_type == "numpy":
        return np.array(img)
    elif output_type == "str":
        secure_temp_dir = tempfile.mkdtemp(prefix="loadimg_", suffix="_folder")
        path = os.path.join(secure_temp_dir, "temp_image.png")
        img.save(path)
        return path
    elif output_type == "base64":
        img_file = BytesIO()
        img.save(img_file, format="PNG")
        img_bytes = img_file.getvalue()
        img_b64 = base64.b64encode(img_bytes)
        return img_b64


def download_image(url: str):
    """Downloads an image from a URL and returns it as a Pillow Image."""
    try:
        if "github" in url and "raw=true" not in url:
            url += "?raw=true"
        elif "drive" in url and "uc?id=" not in url:
            if "/view" in url or url.endswith("/"):
                url = "/".join(url.split("/")[:-1])
            url = "https://drive.google.com/uc?id=" + url.split("/")[-1]
        elif "hf.co" or "huggingface.co" in url:
            url = url.replace("/blob/", "/resolve")
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        return Image.open(BytesIO(response.content))
    except requests.exceptions.RequestException as e:
        print(f"Error downloading image from {url}: {e}")
        return None


def load(img, input_type="auto") -> Image.Image:
    """Loads an image from various sources and returns it as a Pillow Image."""
    if input_type == "auto":
        if isBase64(img):
            input_type = "base64"
        elif isinstance(img, str):
            if os.path.isfile(img):
                input_type = "file"
            else:
                input_type = "url"
        elif isinstance(img, np.ndarray):
            input_type = "numpy"
        elif isinstance(img, Image.Image):
            input_type = "pil"
        else:
            raise ValueError(
                f"Invalid input type: {input_type}. Expected one of: 'base64', 'file', 'url', 'numpy', 'pil'"
            )

    if input_type == "base64":
        if isinstance(img, str):
            img = re.sub(r"^data:image\/[a-zA-Z]+;base64,", "", img)
            image_bytes = base64.b64decode(img)
            image_file = BytesIO(image_bytes)
            return Image.open(image_file)
        else:
            image_bytes = base64.b64decode(img)
            image_file = BytesIO(image_bytes)
            return Image.open(image_file)
    elif input_type == "file":
        return Image.open(img)
    elif input_type == "url":
        out = download_image(img)
        if out is None:
            raise ValueError(f"could not download {img}")
        else:
            return out
    elif input_type == "numpy":
        return Image.fromarray(img)
    elif input_type == "pil":
        return img
    else:
        raise ValueError(
            f"Invalid input type: {input_type}. Expected one of: 'base64', 'file', 'url', 'numpy', 'pil'"
        )


def isBase64(sb):
    """
    checks if the input object is base64
    """
    try:
        if isinstance(sb, str):
            sb = re.sub(r"^data:image\/[a-zA-Z]+;base64,", "", sb)
            sb_bytes = bytes(sb, "ascii")
        elif isinstance(sb, bytes):
            sb_bytes = sb
        return base64.b64encode(base64.b64decode(sb_bytes)) == sb_bytes
    except Exception:
        return False
