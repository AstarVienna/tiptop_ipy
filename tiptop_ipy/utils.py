import os
from pathlib import Path
from tempfile import TemporaryFile
from schema import Schema

import requests
from requests_toolbelt.multipart import decoder
import yaml
import json
import pprint
from astropy.io import fits
import logging


# Initialization of the module
log = logging.getLogger("root")

with open(Path(__file__).parent / "defaults.yaml") as f:
    DEFAULTS = f.read()
    DEFAULTS_YAML = yaml.full_load(DEFAULTS)
    URL = "https://www.eso.org/p2services/any/tiptop"


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
                line = line.replace("=", ":").replace("None", "!!null None")
                dic = yaml.full_load(line)

                yaml_dict[curr_cat].update(dic)

    return yaml_dict


def query_tiptop_server(ini_content: str) -> fits.HDUList:
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

    log.debug(f"Ini content: {ini_content}")

    with TemporaryFile() as ini_stream:
        ini_stream.write(ini_content.encode("ascii"))
        ini_stream.seek(0)

        desc_file = Path(__file__).parent / "instrument_templates" / "serviceDescription.json"
        schema = Schema(json.loads(open(desc_file, 'rb').read()))

        files = {
            'serviceDescription': (desc_file.name, open(desc_file, 'rb'), 'application/json'),
            'parameterFile': ("tiptop_ipy.ini", ini_stream, 'text/plain')
        }
        log.debug(f"Sending a request to {URL}: {files}")
        response = requests.post(URL, files=files)

    if response.status_code == 200:
        payload = decoder.MultipartDecoder.from_response(response)
        if "cannot extract JSON structure from service output" in str(payload.parts[0].content):
            raise ValueError("Config file could not be parsed by server :(")

        with TemporaryFile(mode="w+b") as tmp:
            found_fits_file = False

            for part in payload.parts:
                log.debug(f"Part {pprint.pformat(part.headers)}")
                match part.headers.get(b'Content-Type'):
                    case b'application/octet-stream':
                        if "tiptop_ipy.fits" in part.headers.get(b'Content-Disposition').decode():
                            tmp.write(part.content)
                            hdus = fits.open(tmp, mode="update", lazy_load_hdus=False)
                            _ = [hdu.data for hdu in hdus]          # force loading of data into RAM
                            found_fits_file = True
                            log.info(f"TIPTOP sent back a FITS file")
                        else:
                            log.error(f"Received an application/octet-stream that is not a FITS file")

                    case b'text/plain':
                        log.debug(f"Received a plain text file")
                        log.debug(f'"{part.content.decode()}"')

                    case b'application/json':
                        log.debug(f"Received a JSON file")
                        content = json.loads(part.content.decode())
                        #schema.validate(content)
                        log.debug(pprint.pformat(content, indent=4))

                        if (code := content['admin']['exitCode']) == 0:
                            log.info(f"TipTop completed successfully")
                        else:
                            log.error(f"Server returned an error, exit code {code}: {content['service']['message']}")

                    case _:
                        raise ValueError("Received something strange")

            if found_fits_file is False:
                raise ValueError("TIPTOP did not create a FITS file. "
                                 "Something is bung with the config file.")
    else:
        raise ValueError(f"TIPTOP server returned error {response.status_code}: {response.text}")

    return hdus
