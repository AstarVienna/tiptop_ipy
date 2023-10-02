from copy import deepcopy
from pathlib import Path
import yaml
import numpy as np

from . import utils


class TipTopConnection:
    def __init__(self, template_file=None, template_dict=None):
        self.file = template_file
        self.defaults = deepcopy(utils.DEFAULTS_YAML)

        self._param_categories = list(self.defaults.keys())
        self._template_yaml = None
        self._wd = Path(__name__).parent

        if self.file is not None:
            fname = self.file.name

            try:
                with open(fname, "r") as f:
                    if ".ini" in self.file.name:
                        self._template_yaml = utils.make_yaml_from_ini(f.read())
                    elif ".yaml" in self.file.name:
                        self._template_yaml = yaml.full_load(f)
                    self.meta = deepcopy(self._template_yaml)
            except FileNotFoundError as e:
                raise ValueError(f"File {fname} does not exist") from e
        elif template_dict is not None and all([cat in template_dict for cat in self._param_categories]):
            self.meta = deepcopy(template_dict)
        else:
            self.meta = deepcopy(self.defaults)

        self.hdulist = None

    def query_server(self):
        """Requests a cube of PSFs from the ESO TIPTOP server """
        self.hdulist = utils.query_tiptop_server(self.ini_contents)

    def nearest_psf(self, x, y):
        """ Returns a numpy array with the PSF kernel nearest to (x, y) in [arcsec] """
        r2 = (x - self.x) ** 2 + (y - self.y) ** 2
        i = np.argmin(r2)
        return self.hdulist[1].data[i, :, :]

    @property
    def x(self):
        return self.hdulist[2].data[0, :]

    @property
    def y(self):
        return self.hdulist[2].data[1, :]

    @property
    def ini_contents(self):
        """ Returns the str needed by the TIPTOP server from the self.meta dict """
        return utils.make_ini_from_yaml(self.meta)

    def writeto(self, filename, **kwargs):
        """ Wrapper for astropy.io.fits.HDUList.writeto method """
        return self.hdulist.writeto(filename, **kwargs)

    def __getitem__(self, item):
        if item not in self._param_categories:
            raise ValueError(f"{item} not found in .meta dictionary")
        return self.meta[item]

    def __setitem__(self, key, value):
        if key not in self._param_categories:
            raise ValueError(f"{key} not found in .meta dictionary")
        self.meta[key] = value
