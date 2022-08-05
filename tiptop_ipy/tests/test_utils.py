import os.path as p
from astropy.io import fits

from tiptop_ipy import utils


class TestDefaults:
    def test_reads_in_yaml(self):
        assert isinstance(utils.DEFAULTS_YAML, dict)
        assert isinstance(utils.DEFAULTS_YAML["DM"], dict)
        assert "NumberActuators" in utils.DEFAULTS_YAML["DM"]["required_keywords"]

    def test_all_categories_present(self):
        cats = ["atmosphere", "telescope", "DM", "RTC",
                "sources_science", "sources_HO", "sources_LO",
                "sensor_science", "sensor_HO", "sensor_LO"]
        assert all([isinstance(utils.DEFAULTS_YAML[cat], dict) for cat in cats])

    def test_defaults_raw_is_string(self):
        assert isinstance(utils.DEFAULTS, str)


class TestMakeIniFromYaml:
    def test_returns_ini_string_with_correct_formatting(self):
        ini_str = utils.make_ini_from_yaml(utils.DEFAULTS_YAML)
        assert "[DM]" in ini_str
        assert "InfModel = 'gaussian'" in ini_str
        assert "description" not in ini_str
        assert "required_keywords" not in ini_str


class TestMakeYamlFromIni:
    def test_returns_full_yaml_dict(self):
        ini_str = """
        [DM]
        NumberActuators = [40, 4.e+1, 4.0E-1]
        InfModel = 'gaussian'

        [RTC]
        LoopGain_HO = 0.3
        """
        yaml_dict = utils.make_yaml_from_ini(ini_str)
        print(yaml_dict)
        assert "DM" in yaml_dict
        assert isinstance(yaml_dict["DM"]["NumberActuators"], list)
        assert isinstance(yaml_dict["DM"]["InfModel"], str)
        assert isinstance(yaml_dict["RTC"]["LoopGain_HO"], float)
        assert yaml_dict["DM"]["NumberActuators"][2] == 0.4


class TestGetTipTopPSF:
    def test_returns_eris_psf_cube(self):
        fname = p.join(p.dirname(__file__), "../", "instrument_templates", "eris.ini")
        with open(fname) as f:
            ini_content = f.read()

        hdulist = utils.query_tiptop_server(ini_content=ini_content)

        assert isinstance(hdulist, fits.HDUList)
        assert len(hdulist) == 3
        assert hdulist[1].header["NAXIS1"] == 256


class TestListInstruments:
    def test_returns_list_of_instruments(self):
        files = utils.list_instruments()
        assert "eris.ini" in files