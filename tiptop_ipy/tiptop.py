from copy import deepcopy
import os
import os.path as p
import yaml
import numpy as np

from . import utils


class TipTopConnection:
    def __init__(self, template_name=None):

        self.meta = deepcopy(utils.DEFAULTS_YAML)
        self._template_yaml = None

        fname = p.join(p.dirname(__file__), "instrument_templates", f"{template_name}.ini")
        if template_name is not None and os.path.exists(fname):
            with open(fname, "r") as f:
                self._template_yaml = utils.make_yaml_from_ini(f.read())
                for cat, dic in self._template_yaml.items():
                    self.meta[cat].update(dic)

        self.hdulist = None

    def get_hdulist(self):
        """ Requests a cube of PSFs from the ESO TIPTOP server """
        self.hdulist = utils.get_tiptop_psf(self.ini_contents)

    def nearest_psf(self, x, y):
        """ Returns a numpy array with the PSF kernel nearest to (x, y) in [arcsec] """
        r2 = (x - self.x) ** 2 + (y - self.y) ** 2
        i = np.argmin(r2)
        return self.hdulist[1].data[i, :, :]

    @property
    def psf(self):
        if self.hdulist is None:
            self.get_hdulist()
        return self.hdulist[1].data

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

    def writeto(self, **kwargs):
        """ Wrapper for astropy.io.fits.HDUList.writeto method """
        return self.hdulist.writeto(**kwargs)
