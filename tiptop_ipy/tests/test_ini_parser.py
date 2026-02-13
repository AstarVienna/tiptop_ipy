"""Tests for the INI parser module."""
import pytest
from tiptop_ipy.ini_parser import parse_ini, write_ini


class TestParseIni:
    def test_basic_sections_and_keys(self):
        ini = """
        [DM]
        NumberActuators = [40]
        InfModel = 'gaussian'

        [RTC]
        LoopGain_HO = 0.3
        """
        config = parse_ini(ini)
        assert "DM" in config
        assert "RTC" in config
        assert config["DM"]["NumberActuators"] == [40]
        assert config["DM"]["InfModel"] == "gaussian"
        assert config["RTC"]["LoopGain_HO"] == 0.3

    def test_scientific_notation(self):
        ini = """
        [atmosphere]
        Wavelength = 500e-9
        L0 = 25.0
        """
        config = parse_ini(ini)
        assert config["atmosphere"]["Wavelength"] == 500e-9
        assert config["atmosphere"]["L0"] == 25.0

    def test_scientific_notation_in_lists(self):
        ini = """
        [sources_science]
        Wavelength = [2200e-9, 1.6e-6, 589e-9]
        """
        config = parse_ini(ini)
        wl = config["sources_science"]["Wavelength"]
        assert len(wl) == 3
        assert wl[0] == pytest.approx(2.2e-6)
        assert wl[1] == pytest.approx(1.6e-6)
        assert wl[2] == pytest.approx(589e-9)

    def test_none_values(self):
        ini = """
        [sensor_HO]
        Modulation = None
        NoiseVariance = [None]
        """
        config = parse_ini(ini)
        assert config["sensor_HO"]["Modulation"] is None
        assert config["sensor_HO"]["NoiseVariance"] == [None]

    def test_boolean_values(self):
        ini = """
        [sensor_LO]
        noNoise = False
        filtZernikeCov = True
        """
        config = parse_ini(ini)
        assert config["sensor_LO"]["noNoise"] is False
        assert config["sensor_LO"]["filtZernikeCov"] is True

    def test_semicolon_comments(self):
        ini = """
        [telescope]
        ; this is a comment
        TelescopeDiameter = 38.5
        Resolution = 480 ; inline comment
        """
        config = parse_ini(ini)
        assert config["telescope"]["TelescopeDiameter"] == 38.5
        assert config["telescope"]["Resolution"] == 480

    def test_hash_comments(self):
        ini = """
        [telescope]
        # this is a comment
        TelescopeDiameter = 8.0
        Resolution = 320 # inline comment
        """
        config = parse_ini(ini)
        assert config["telescope"]["TelescopeDiameter"] == 8.0
        assert config["telescope"]["Resolution"] == 320

    def test_string_values_with_quotes(self):
        ini = """
        [sensor_HO]
        WfsType = 'Shack-Hartmann'
        Algorithm = "wcog"
        WindowRadiusWCoG = 'optimize'
        """
        config = parse_ini(ini)
        assert config["sensor_HO"]["WfsType"] == "Shack-Hartmann"
        assert config["sensor_HO"]["Algorithm"] == "wcog"
        assert config["sensor_HO"]["WindowRadiusWCoG"] == "optimize"

    def test_nested_lists(self):
        ini = """
        [sensor_HO]
        SpotFWHM = [[2500.0, 2500.0, 0.0]]
        Dispersion = [[0.0], [0.0]]
        """
        config = parse_ini(ini)
        assert config["sensor_HO"]["SpotFWHM"] == [[2500.0, 2500.0, 0.0]]
        assert config["sensor_HO"]["Dispersion"] == [[0.0], [0.0]]

    def test_empty_string_value(self):
        ini = """
        [telescope]
        PathApodizer = ''
        """
        config = parse_ini(ini)
        assert config["telescope"]["PathApodizer"] == ""

    def test_path_with_equals(self):
        """Regression: values containing '=' should be parsed correctly."""
        ini = """
        [telescope]
        PathPupil = 'tiptop/data/file=test.fits'
        """
        config = parse_ini(ini)
        # partition on first '=' means the rest is preserved
        assert "file=test.fits" in config["telescope"]["PathPupil"]


class TestWriteIni:
    def test_roundtrip(self):
        original = {
            "DM": {"NumberActuators": [40], "InfModel": "gaussian"},
            "RTC": {"LoopGain_HO": 0.3},
        }
        ini_str = write_ini(original)
        parsed = parse_ini(ini_str)
        assert parsed["DM"]["NumberActuators"] == [40]
        assert parsed["DM"]["InfModel"] == "gaussian"
        assert parsed["RTC"]["LoopGain_HO"] == pytest.approx(0.3)

    def test_none_roundtrip(self):
        original = {"sensor_HO": {"Modulation": None}}
        ini_str = write_ini(original)
        parsed = parse_ini(ini_str)
        assert parsed["sensor_HO"]["Modulation"] is None

    def test_boolean_roundtrip(self):
        original = {"sensor_LO": {"noNoise": False, "filtZernikeCov": True}}
        ini_str = write_ini(original)
        parsed = parse_ini(ini_str)
        assert parsed["sensor_LO"]["noNoise"] is False
        assert parsed["sensor_LO"]["filtZernikeCov"] is True
