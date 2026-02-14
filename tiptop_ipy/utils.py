import os
import os.path as p
from tempfile import TemporaryFile

import requests
from requests_toolbelt.multipart import decoder
import yaml
from astropy.io import fits

from .ini_parser import parse_ini, write_ini


with open(p.join(p.dirname(__file__), "defaults.yaml")) as f:
    DEFAULTS = f.read()
    DEFAULTS_YAML = yaml.full_load(DEFAULTS)


def list_instruments(include_path=False):
    """List available instrument template names.

    Parameters
    ----------
    include_path : bool
        If True, return full paths instead of just names.

    Returns
    -------
    names : list[str]
        Sorted list of instrument names (without .ini extension)
        or full paths if include_path is True.
    """
    dname = p.join(p.dirname(__file__), "instrument_templates")
    fnames = sorted(
        fname for fname in os.listdir(dname)
        if fname.endswith(".ini")
    )

    if include_path:
        return [p.join(dname, fname) for fname in fnames]

    return [fname.replace(".ini", "") for fname in fnames]


def query_tiptop_server(ini_content, timeout=120):
    """Send an INI config to the TIPTOP server and return the FITS result.

    Parameters
    ----------
    ini_content : str
        The raw contents of a TIPTOP config .ini file.
    timeout : int
        Request timeout in seconds.

    Returns
    -------
    hdus : fits.HDUList
        A FITS file with extensions:
        - [0] PrimaryHDU: header info
        - [1] ImageHDU: PSF cube(s)
        - [-1] ImageHDU: (2, N) cartesian coordinates of PSF positions
    """
    with TemporaryFile() as ini_stream:
        ini_stream.write(ini_content.encode("ascii"))
        ini_stream.seek(0)

        url = "https://www.eso.org/p2services/any/tiptop"
        desc_file = p.join(p.dirname(__file__), "instrument_templates",
                           "serviceDescription.json")
        with open(desc_file, "rb") as df:
            files = {
                "serviceDescription": (desc_file, df, "application/json"),
                "parameterFile": ("tiptop_ipy.ini", ini_stream, "text/plain"),
            }
            response = requests.post(url, files=files, timeout=timeout)

    if response.status_code != 200:
        raise ValueError(
            f"TIPTOP server returned HTTP {response.status_code}: "
            f"{response.text[:200]}"
        )

    payload = decoder.MultipartDecoder.from_response(response)
    if "cannot extract JSON structure from service output" in str(
        payload.parts[0].content
    ):
        raise ValueError("Config file cannot be parsed by server")

    with TemporaryFile(mode="w+b") as tmp:
        found_fits_file = False
        for part in payload.parts:
            content_type = part.headers.get(b"Content-Type")
            disposition = part.headers.get(b"Content-Disposition", b"").decode()
            if (content_type == b"application/octet-stream"
                    and "tiptop_ipy.fits" in disposition):
                tmp.write(part.content)
                hdus = fits.open(tmp, mode="update", lazy_load_hdus=False)
                # Force loading data into RAM before temp file closes
                _ = [hdu.data for hdu in hdus]
                found_fits_file = True

        if not found_fits_file:
            # Dump what the server actually sent back
            parts_summary = []
            max_msg_len = -1
            for i, part in enumerate(payload.parts):
                ct = part.headers.get(b"Content-Type", b"unknown").decode()
                disp = part.headers.get(b"Content-Disposition", b"").decode()
                try:
                    body = part.content.decode(errors="replace")[:max_msg_len]
                except Exception:
                    body = repr(part.content[:max_msg_len])
                parts_summary.append(
                    f"  Part {i}: Content-Type={ct}, "
                    f"Disposition={disp}\n  {body}"
                )
            detail = "\n".join(parts_summary)
            raise ValueError(
                f"TIPTOP did not return a FITS file. "
                f"Server response ({len(payload.parts)} parts):\n{detail}"
            )

    return hdus
