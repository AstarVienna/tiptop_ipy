"""Tests for utility functions."""
import pytest
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
        assert all(isinstance(utils.DEFAULTS_YAML[cat], dict) for cat in cats)

    def test_defaults_raw_is_string(self):
        assert isinstance(utils.DEFAULTS, str)

    def test_new_sections_present(self):
        assert "sources_Focus" in utils.DEFAULTS_YAML
        assert "sensor_Focus" in utils.DEFAULTS_YAML


class TestListInstruments:
    def test_returns_list_of_instruments(self):
        instruments = utils.list_instruments()
        assert isinstance(instruments, list)
        assert len(instruments) > 0

    def test_no_ini_extension(self):
        instruments = utils.list_instruments()
        for name in instruments:
            assert not name.endswith(".ini")

    def test_sorted(self):
        instruments = utils.list_instruments()
        assert instruments == sorted(instruments)

    def test_include_path(self):
        paths = utils.list_instruments(include_path=True)
        for path in paths:
            assert path.endswith(".ini")

    def test_known_instruments_present(self):
        instruments = utils.list_instruments()
        # Check a few known instruments (case-sensitive file names)
        lower_instruments = [i.lower() for i in instruments]
        assert "micado_scao" in lower_instruments
        assert "eris" in lower_instruments


class TestParseIniIntegration:
    """Test that parse_ini works on real template files."""

    def test_parses_eris(self):
        from tiptop_ipy.ini_parser import parse_ini
        paths = utils.list_instruments(include_path=True)
        eris_path = [p for p in paths if "ERIS" in p and "LGS" not in p][0]
        config = parse_ini(eris_path)
        assert "atmosphere" in config
        assert config["atmosphere"]["Seeing"] == 0.8

    def test_parses_morfeo(self):
        from tiptop_ipy.ini_parser import parse_ini
        paths = utils.list_instruments(include_path=True)
        morfeo_path = [p for p in paths if "MORFEO" in p][0]
        config = parse_ini(morfeo_path)
        assert "sources_Focus" in config
        assert "sensor_Focus" in config
        assert config["telescope"]["extraErrorNm"] == 93
