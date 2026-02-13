"""Tests for the TipTop main class."""
import pytest
from tiptop_ipy import TipTop, TipTopConnection


class TestTipTopInit:
    def test_initialised_with_no_template(self):
        tt = TipTop()
        assert isinstance(tt, TipTop)
        assert "DM" in tt.sections

    def test_initialised_with_instrument_name(self):
        tt = TipTop("MICADO_SCAO")
        assert tt._instrument == "MICADO_SCAO"
        assert tt["telescope", "TelescopeDiameter"] == 38.5

    def test_case_insensitive_instrument(self):
        tt = TipTop("micado_scao")
        assert tt["telescope", "TelescopeDiameter"] == 38.5

    def test_instrument_with_ini_extension(self):
        tt = TipTop("MICADO_SCAO.ini")
        assert tt["telescope", "TelescopeDiameter"] == 38.5

    def test_invalid_instrument_raises(self):
        with pytest.raises(FileNotFoundError, match="No template found"):
            TipTop("NONEXISTENT_INSTRUMENT")

    def test_backward_compat_alias(self):
        """TipTopConnection should still work as an alias."""
        tt = TipTopConnection()
        assert isinstance(tt, TipTop)


class TestTupleIndexing:
    def test_getitem_section(self):
        tt = TipTop("MICADO_SCAO")
        atm = tt["atmosphere"]
        assert isinstance(atm, dict)
        assert "Seeing" in atm

    def test_getitem_tuple(self):
        tt = TipTop("MICADO_SCAO")
        seeing = tt["atmosphere", "Seeing"]
        assert isinstance(seeing, (int, float))

    def test_setitem_tuple(self):
        tt = TipTop("MICADO_SCAO")
        tt["atmosphere", "Seeing"] = 0.6
        assert tt["atmosphere", "Seeing"] == 0.6

    def test_setitem_section(self):
        tt = TipTop("MICADO_SCAO")
        tt["atmosphere"] = {"Seeing": 1.2, "L0": 30.0}
        assert tt["atmosphere", "Seeing"] == 1.2
        assert tt["atmosphere", "L0"] == 30.0

    def test_setitem_creates_new_section(self):
        tt = TipTop("MICADO_SCAO")
        tt["new_section", "key"] = 42
        assert tt["new_section", "key"] == 42


class TestDiffAndReset:
    def test_diff_empty_when_unchanged(self):
        tt = TipTop("MICADO_SCAO")
        assert tt.diff() == {}

    def test_diff_shows_changes(self):
        tt = TipTop("MICADO_SCAO")
        original = tt["atmosphere", "Seeing"]
        tt["atmosphere", "Seeing"] = 1.5
        changes = tt.diff()
        assert "atmosphere" in changes
        assert "Seeing" in changes["atmosphere"]
        assert changes["atmosphere"]["Seeing"] == (original, 1.5)

    def test_reset_restores_original(self):
        tt = TipTop("MICADO_SCAO")
        original = tt["atmosphere", "Seeing"]
        tt["atmosphere", "Seeing"] = 1.5
        tt.reset()
        assert tt["atmosphere", "Seeing"] == original
        assert tt.diff() == {}


class TestSaveAndLoad:
    def test_save_and_load_roundtrip(self, tmp_path):
        tt = TipTop("MICADO_SCAO")
        tt["atmosphere", "Seeing"] = 0.5

        path = str(tmp_path / "test.ini")
        tt.save(path)

        tt2 = TipTop(ini_file=path)
        assert tt2["atmosphere", "Seeing"] == pytest.approx(0.5)
        assert tt2["telescope", "TelescopeDiameter"] == pytest.approx(38.5)


class TestRepr:
    def test_repr(self):
        tt = TipTop("MICADO_SCAO")
        r = repr(tt)
        assert "TipTop" in r
        assert "MICADO_SCAO" in r

    def test_repr_html(self):
        tt = TipTop("MICADO_SCAO")
        html = tt._repr_html_()
        assert "<table>" in html
        assert "MICADO_SCAO" in html


class TestListInstruments:
    def test_returns_sorted_list(self):
        instruments = TipTop.list_instruments()
        assert isinstance(instruments, list)
        assert len(instruments) > 0
        assert instruments == sorted(instruments)

    def test_no_ini_extension(self):
        instruments = TipTop.list_instruments()
        for name in instruments:
            assert not name.endswith(".ini")


class TestValidate:
    def test_template_validates(self):
        tt = TipTop("MICADO_SCAO")
        issues = tt.validate()
        errors = [i for i in issues if i.startswith("ERROR")]
        assert len(errors) == 0


class TestIniContents:
    def test_ini_contents_is_string(self):
        tt = TipTop("MICADO_SCAO")
        ini = tt.ini_contents
        assert isinstance(ini, str)
        assert "[telescope]" in ini
        assert "[atmosphere]" in ini


@pytest.mark.network
class TestServerIntegration:
    """These tests require network access to the ESO TIPTOP server."""

    def test_generate_psf_eris(self):
        tt = TipTop("ERIS")
        result = tt.generate_psf()
        assert result.psf is not None
        assert result.psf.ndim >= 2

    def test_generate_psf_multi_wavelength(self):
        tt = TipTop("ERIS")
        tt["sources_science", "Wavelength"] = [1.2e-6, 1.65e-6, 2.2e-6]
        result = tt.generate_psf()
        assert result.n_wavelengths >= 1
