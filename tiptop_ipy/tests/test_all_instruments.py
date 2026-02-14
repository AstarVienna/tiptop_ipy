"""
Integration test: generate a PSF for every instrument template and verify
that the returned FITS dimensions match the config.

Run with:
    pytest tiptop_ipy/tests/test_all_instruments.py --network -v -s
"""
import time

import pytest
from tiptop_ipy import TipTop


ALL_INSTRUMENTS = TipTop.list_instruments()

# Instruments that reference server-side FITS files the ESO server
# doesn't have — these fail server-side, not a bug in our code.
SERVER_UNSUPPORTED = {
    "ANDES", "HARMONI_SCAO", "HarmoniLTAO_1", "HarmoniLTAO_2",
    "HarmoniLTAO_3", "METIS", "MICADO_SCAO", "MICADO_SCAO_less_layers",
    "MORFEO",
}

# MCAO instruments that cause the ESO server to reset the connection
# (computation too heavy for the public endpoint).
SERVER_FLAKY = {"MAVIS"}


@pytest.mark.network
@pytest.mark.parametrize("instrument", ALL_INSTRUMENTS)
def test_instrument_psf_dimensions(instrument):
    """Generate a PSF and check the FITS image dimensions match the config."""
    if instrument in SERVER_UNSUPPORTED:
        pytest.xfail(
            f"{instrument} uses server-side data files not available on ESO"
        )
    if instrument in SERVER_FLAKY:
        pytest.xfail(
            f"{instrument} MCAO computation too heavy for ESO public endpoint"
        )

    tt = TipTop(instrument)

    fov = tt["sensor_science", "FieldOfView"]
    n_wavelengths = len(tt["sources_science", "Wavelength"])
    n_zenith = len(tt["sources_science", "Zenith"])

    t0 = time.perf_counter()
    result = tt.generate_psf(timeout=300)
    elapsed = time.perf_counter() - t0
    print(f"\n  {instrument}: server responded in {elapsed:.1f}s "
          f"(Strehl={result.strehl[0]:.3f}, FWHM={result.fwhm[0]:.1f} mas)")

    # Number of PSF HDU cubes should match number of wavelengths
    assert result.n_wavelengths == n_wavelengths, (
        f"{instrument}: expected {n_wavelengths} wavelength cube(s), "
        f"got {result.n_wavelengths}"
    )

    # Each PSF cube should have spatial dimensions matching FieldOfView
    for wi in range(result.n_wavelengths):
        cube = result.psf_cube(wi)
        if cube.ndim == 3:
            _, ny, nx = cube.shape
        else:
            ny, nx = cube.shape

        assert nx == fov, (
            f"{instrument} wave {wi}: expected nx={fov}, got {nx}"
        )
        assert ny == fov, (
            f"{instrument} wave {wi}: expected ny={fov}, got {ny}"
        )

    # Number of positions in the cube should match Zenith count
    if result.psf.ndim == 3:
        n_positions = result.psf.shape[0]
        assert n_positions == n_zenith, (
            f"{instrument}: expected {n_zenith} position(s), "
            f"got {n_positions}"
        )

    # Coordinate count from header should match
    assert len(result.x) == n_zenith, (
        f"{instrument}: coordinate x has {len(result.x)} entries, "
        f"expected {n_zenith}"
    )
