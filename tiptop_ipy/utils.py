import os.path as p
from tempfile import TemporaryFile

import requests
from requests_toolbelt.multipart import decoder
import yaml
from astropy.io import fits


with open(p.join(p.dirname(__file__), "defaults.yaml")) as f:
    DEFAULTS_RAW = f.read()
    DEFAULTS_YAML = yaml.full_load(DEFAULTS_RAW)


def make_ini_from_yaml(config_dict: dict) -> str:
    ini_str = ""
    for key, sub_dict in config_dict.items():
        ini_str += f"[{key}]\n"
        for sub_key, value in sub_dict.items():
            if sub_key not in ["description", "required_keywords"]:
                ini_str += f"{sub_key} = {value}\n" if not isinstance(value, str) else f"{sub_key} = '{value}'\n"
        ini_str += "\n"

    return ini_str


def make_yaml_from_ini(ini_contents: str) -> dict:
    yaml_dict = {}
    ini_list = ini_contents.split("\n")
    curr_cat = None
    for line in ini_list:
        line = line.strip()
        if len(line) > 0 and line[0] != ";":
            if line[0] == "[" and line[-1] == "]":
                curr_cat = line[1:-1]
                yaml_dict[curr_cat] = {}
            else:
                line = line.replace("=", ":")
                dic = yaml.full_load(line)
                yaml_dict[curr_cat].update(dic)

    return yaml_dict


def get_tiptop_psf(ini_content: str) -> fits.HDUList:
    """
    Returns a cube of PSFs for N on-sky positions relative to the optical axis

    Parameters
    ----------
    ini_content : str, dict
        str - the raw contents of a tiptop config .ini file

    Returns
    -------
    hdus : fits.HDUList
        A FITS file with 3 extensions:
        - [0] PrimaryHDU is empty apart from header info
        - [1] ImageHDU contains N PSFs for each of the *radial* on-sky coords from sources_science["Azimuth", "Zenith"]
        - [2] ImageHDU contains image with dimensions (N, 2) holding the *cartesian* on-sky coordinates of the PSFs

    """

    with TemporaryFile() as ini_stream:
        ini_stream.write(ini_content.encode("ascii"))
        ini_stream.seek(0)

        url = f' https://www.eso.org/p2services/any/tiptop'
        desc_file = p.join(p.dirname(__file__), "instrument_templates", "serviceDescription.json")
        files = {'serviceDescription': (desc_file, open(desc_file, 'rb'), 'application/json'),
                 'parameterFile': ("tiptop_ipy.ini", ini_stream, 'text/plain')}
        response = requests.post(url, files=files)

    if response.status_code == 200:
        payload = decoder.MultipartDecoder.from_response(response)
        if "cannot extract JSON structure from service output" in str(payload.parts[0].content):
            raise ValueError("Config file cannot be parsed by server :(")

        with TemporaryFile(mode="w+b") as tmp:
            for part in payload.parts:
                if part.headers.get(b'Content-Type') == b'application/octet-stream' and \
                        "tiptop_ipy.fits" in part.headers.get(b'Content-Disposition').decode():
                    tmp.write(part.content)
                    hdus = fits.open(tmp, mode="update", lazy_load_hdus=False)
                    _ = [hdu.data for hdu in hdus]          # force loading of data into RAM

    else:
        raise ValueError(f"TIPTOP server returned error: {response.status_code}")

    return hdus
