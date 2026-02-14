"""Tests for the TipTopResult class."""
import numpy as np
import pytest
from astropy.io import fits

from tiptop_ipy.result import TipTopResult


def _make_mock_hdulist(n_positions=3, n_wavelengths=1, size=64):
    """Create a mock FITS HDUList matching TIPTOP server output format.

    Format: PrimaryHDU + N PSF CUBEs + OPEN-LOOP + DIFFRACTION + PROFILES
    """
    hdus = [fits.PrimaryHDU()]

    for wi in range(n_wavelengths):
        psf_data = np.random.rand(n_positions, size, size).astype(np.float32)
        header = fits.Header()
        header["CONTENT"] = "PSF CUBE"
        header["WL_NM"] = 1650 + wi * 500
        header["PIX_MAS"] = 14
        for j in range(n_positions):
            header[f"CCX{j:04d}"] = float(j * 5.0)
            header[f"CCY{j:04d}"] = float(j * 3.0)
            header[f"SR{j:04d}"] = 0.85 + j * 0.01
            header[f"FWHM{j:04d}"] = 50.0 + j * 2.0
        hdus.append(fits.ImageHDU(data=psf_data, header=header))

    # Open-loop PSF
    ol_header = fits.Header()
    ol_header["CONTENT"] = "OPEN-LOOP PSF"
    hdus.append(fits.ImageHDU(
        data=np.random.rand(size, size).astype(np.float32),
        header=ol_header,
    ))

    # Diffraction-limited PSF
    dl_header = fits.Header()
    dl_header["CONTENT"] = "DIFFRACTION LIMITED PSF"
    hdus.append(fits.ImageHDU(
        data=np.random.rand(size, size).astype(np.float32),
        header=dl_header,
    ))

    # Radial profiles
    prof_header = fits.Header()
    prof_header["CONTENT"] = "Final PSFs profiles"
    hdus.append(fits.ImageHDU(
        data=np.random.rand(2, n_positions, size // 2).astype(np.float32),
        header=prof_header,
    ))

    return fits.HDUList(hdus)


class TestTipTopResult:
    def test_detect_structure(self):
        hdulist = _make_mock_hdulist(n_positions=3, n_wavelengths=2)
        result = TipTopResult(hdulist)
        assert result.n_wavelengths == 2
        assert result._open_loop_index is not None
        assert result._diffraction_index is not None
        assert result._profile_index is not None

    def test_psf_property(self):
        hdulist = _make_mock_hdulist(n_positions=3)
        result = TipTopResult(hdulist)
        psf = result.psf
        assert psf.shape == (3, 64, 64)

    def test_open_loop_psf(self):
        hdulist = _make_mock_hdulist()
        result = TipTopResult(hdulist)
        assert result.open_loop_psf.shape == (64, 64)

    def test_diffraction_psf(self):
        hdulist = _make_mock_hdulist()
        result = TipTopResult(hdulist)
        assert result.diffraction_psf.shape == (64, 64)

    def test_coordinates_from_header(self):
        hdulist = _make_mock_hdulist(n_positions=5)
        result = TipTopResult(hdulist)
        assert result.x.shape == (5,)
        assert result.y.shape == (5,)
        assert result.x[0] == 0.0
        assert result.x[1] == 5.0

    def test_strehl(self):
        hdulist = _make_mock_hdulist(n_positions=3)
        result = TipTopResult(hdulist)
        sr = result.strehl
        assert sr.shape == (3,)
        assert sr[0] == pytest.approx(0.85)

    def test_fwhm(self):
        hdulist = _make_mock_hdulist(n_positions=3)
        result = TipTopResult(hdulist)
        fwhm = result.fwhm
        assert fwhm.shape == (3,)
        assert fwhm[0] == pytest.approx(50.0)

    def test_psf_cube(self):
        hdulist = _make_mock_hdulist(n_positions=3, n_wavelengths=3)
        result = TipTopResult(hdulist)
        cube0 = result.psf_cube(0)
        cube2 = result.psf_cube(2)
        assert cube0.shape == (3, 64, 64)
        assert cube2.shape == (3, 64, 64)

    def test_psf_cube_out_of_range(self):
        hdulist = _make_mock_hdulist(n_wavelengths=1)
        result = TipTopResult(hdulist)
        with pytest.raises(IndexError):
            result.psf_cube(5)

    def test_nearest_psf(self):
        hdulist = _make_mock_hdulist(n_positions=3)
        result = TipTopResult(hdulist)
        psf = result.nearest_psf(result.x[0], result.y[0])
        assert psf.ndim == 2
        assert psf.shape == (64, 64)

    def test_repr(self):
        hdulist = _make_mock_hdulist(n_positions=3, n_wavelengths=2)
        result = TipTopResult(hdulist)
        r = repr(result)
        assert "TipTopResult" in r
        assert "2 wavelength" in r
        assert "Strehl" in r

    def test_repr_html(self):
        hdulist = _make_mock_hdulist(n_positions=3)
        result = TipTopResult(hdulist)
        html = result._repr_html_()
        assert "<table>" in html
        assert "TipTopResult" in html
        assert "PSF CUBE" in html

    def test_writeto(self, tmp_path):
        hdulist = _make_mock_hdulist()
        result = TipTopResult(hdulist)
        path = str(tmp_path / "test.fits")
        result.writeto(path)
        loaded = fits.open(path)
        assert len(loaded) >= 4
        loaded.close()

    def test_plot(self):
        """Test that plot runs without error (don't display)."""
        matplotlib = pytest.importorskip("matplotlib")
        matplotlib.use("Agg")

        hdulist = _make_mock_hdulist(n_positions=3)
        result = TipTopResult(hdulist)
        fig, ax = result.plot()
        assert fig is not None
        import matplotlib.pyplot as plt
        plt.close(fig)
