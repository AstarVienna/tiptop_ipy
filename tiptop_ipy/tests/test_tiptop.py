from astropy.io import fits
from tiptop_ipy import TipTopConnection


class TestTipTopConnection:
    def test_initialised_with_no_template(self):
        ttc = TipTopConnection()
        assert isinstance(ttc, TipTopConnection)
        assert isinstance(ttc.meta, dict)
        assert ttc.meta["DM"]["InfCoupling"][0] == 0.2
        assert ttc.meta["RTC"]["SensorFrameRate_HO"] == 1000.

    def test_getattr_and_setattr_calls(self):
        ttc = TipTopConnection("eris.ini")
        assert ttc["DM"]["NumberActuators"][0] == 40
        ttc["DM"]["NumberActuators"][0] = 9001
        assert ttc["DM"]["NumberActuators"][0] != 40

    def test_initialised_with_eris_template(self):
        ttc = TipTopConnection("eris.ini")
        ttc.query_server()
        assert isinstance(ttc.hdulist, fits.HDUList)

    def test_add_wavelength_to_eris_server_query(self):
        ttc = TipTopConnection("eris.ini")
        ttc["sources_science"]["Wavelength"] = [1.2e-6, 1.65e-6, 2.2e-6]
        ttc.query_server()
        assert isinstance(ttc.hdulist, fits.HDUList)
        assert len(fits.HDUList) == 4
