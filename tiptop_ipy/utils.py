import os
import os.path as p
import time
from tempfile import TemporaryFile

import requests
from requests_toolbelt.multipart import decoder
import yaml
from astropy.io import fits

from .ini_parser import parse_ini, write_ini


with open(p.join(p.dirname(__file__), "defaults.yaml")) as f:
    DEFAULTS = f.read()
    DEFAULTS_YAML = yaml.full_load(DEFAULTS)

_ESO_URL = "https://www.eso.org/p2services/any/tiptop"
_UNIVIE_URL = "https://homepage.univie.ac.at/kieran.leschinski/tiptop/api"

SERVERS = {
    "eso": _ESO_URL,
    "univie": _UNIVIE_URL,
}

_server_url = os.environ.get("TIPTOP_SERVER_URL", _UNIVIE_URL)


def set_server(name_or_url):
    """Set the TIPTOP server.

    Parameters
    ----------
    name_or_url : str
        Either a server name ("eso", "univie") or a full URL.

    Examples
    --------
    >>> set_server("univie")       # University of Vienna (default)
    >>> set_server("http://...")    # Custom URL
    """
    global _server_url
    _server_url = SERVERS.get(name_or_url.lower(), name_or_url)


def get_server():
    """Return the current TIPTOP server URL."""
    return _server_url


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

    Routes to ESO (synchronous) or custom server (async polling) based on
    the current server URL set via ``set_server()`` or ``TIPTOP_SERVER_URL``.

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
    if _server_url == _ESO_URL:
        return _query_eso(ini_content, timeout)
    return _query_custom(ini_content, timeout)


def _query_eso(ini_content, timeout=120):
    """Send config to the ESO TIPTOP endpoint (synchronous)."""
    with TemporaryFile() as ini_stream:
        ini_stream.write(ini_content.encode("ascii"))
        ini_stream.seek(0)

        desc_file = p.join(p.dirname(__file__), "instrument_templates",
                           "serviceDescription.json")
        with open(desc_file, "rb") as df:
            files = {
                "serviceDescription": (desc_file, df, "application/json"),
                "parameterFile": ("tiptop_ipy.ini", ini_stream, "text/plain"),
            }
            response = requests.post(_ESO_URL, files=files, timeout=timeout)

    if response.status_code != 200:
        raise ValueError(
            f"TIPTOP server returned HTTP {response.status_code}: "
            f"{response.text[:200]}"
        )

    return _parse_multipart_fits(response)


def _query_custom(ini_content, timeout=300):
    """Send config to a custom TIPTOP server (async polling)."""
    submit_url = f"{_server_url}/submit.php"

    with TemporaryFile() as ini_stream:
        ini_stream.write(ini_content.encode("ascii"))
        ini_stream.seek(0)

        desc_file = p.join(p.dirname(__file__), "instrument_templates",
                           "serviceDescription.json")
        with open(desc_file, "rb") as df:
            files = {
                "serviceDescription": (desc_file, df, "application/json"),
                "parameterFile": ("tiptop_ipy.ini", ini_stream, "text/plain"),
            }
            response = requests.post(submit_url, files=files, timeout=60)

    if response.status_code != 200:
        raise ValueError(
            f"TIPTOP server returned HTTP {response.status_code}: "
            f"{response.text[:200]}"
        )

    # Cache hit: server returns multipart FITS directly
    content_type = response.headers.get("Content-Type", "")
    if "multipart" in content_type:
        return _parse_multipart_fits(response)

    # Cache miss: server returns JSON with job_id
    data = response.json()
    job_id = data["job_id"]

    # Poll for completion
    status_url = f"{_server_url}/status.php"
    deadline = time.time() + timeout
    poll_interval = 2

    while time.time() < deadline:
        time.sleep(poll_interval)
        resp = requests.get(status_url, params={"job_id": job_id}, timeout=30)
        resp.raise_for_status()
        status = resp.json()

        if status["status"] == "completed":
            # Fetch result
            result_url = f"{_server_url}/result.php"
            result_resp = requests.get(
                result_url, params={"job_id": job_id}, timeout=60
            )
            result_resp.raise_for_status()
            return _parse_multipart_fits(result_resp)

        if status["status"] == "failed":
            msg = status.get("error_message", "Unknown server error")
            raise ValueError(f"TIPTOP simulation failed: {msg}")

    raise TimeoutError(
        f"TIPTOP job {job_id} did not complete within {timeout}s"
    )


def _parse_multipart_fits(response):
    """Parse a multipart response containing a FITS file."""
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
