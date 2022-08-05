# if __name__ == "__main__":
#     instrument = "eris"
#     with open(f"{instrument}.ini") as ini_file:
#         ini_content = ini_file.read()
#
#     hdus = get_tiptop_psf(ini_content=ini_content)
#     hdus.writeto(f"{instrument}.fits", overwrite=True)

from tiptop_ipy import tiptop
from astropy.io import fits


class TestTipTopConnection:
    def test_initialised_with_no_template(self):
        ttc = tiptop.TipTopConnection()
        assert isinstance(ttc, tiptop.TipTopConnection)
        assert isinstance(ttc.meta, dict)
        assert ttc.meta["DM"]["InfCoupling"][0] == 0.2
        assert ttc.meta["RTC"]["SensorFrameRate_HO"] == 1000.

    def test_initialised_with_eris_template(self):
        ttc = tiptop.TipTopConnection("eris")
        ttc.get_hdulist()
        assert isinstance(ttc.hdulist, fits.HDUList)

