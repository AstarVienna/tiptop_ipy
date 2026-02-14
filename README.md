# TIPTOP-iPy

A Python wrapper for the ESO TIPTOP adaptive optics PSF simulation microservice.

    $ pip install git+https://github.com/astronomyk/tiptop_ipy.git

## Basic Usage

List the available instrument templates:

    >>> from tiptop_ipy import TipTop

    >>> TipTop.list_instruments()
    ['ANDES', 'ERIS', 'ERIS_LGS', 'HARMONI_SCAO', 'HarmoniLTAO_1', ...]

Create a `TipTop` object and generate a PSF:

    >>> eris = TipTop("ERIS")
    >>> result = eris.generate_psf()
    >>> result.writeto("eris.fits", overwrite=True)

The result object provides convenient access to the PSF data:

    >>> result.psf.shape
    (1, 256, 256)

    >>> result.strehl
    array([0.891])

    >>> result.fwhm
    array([44.1])

## Playing with parameters

Parameters are accessed using tuple indexing on the `TipTop` object:

    >>> eris["atmosphere"]
    {'Cn2Weights': [0.59, 0.02, ...], 'Cn2Heights': [30, 140, ...], 'Seeing': 0.8, ...}

    >>> eris["atmosphere", "Seeing"]
    0.8

Values can be updated using the same syntax.
For example, we can ask TIPTOP to generate two PSFs (on-axis, 10" off-axis):

    >>> eris["sources_science", "Zenith"] = [0, 10]
    >>> eris["sources_science", "Azimuth"] = [0, 180]
    >>> result = eris.generate_psf()

    >>> result.plot()

To see what you've changed from the template defaults:

    >>> eris.diff()
    {'sources_science': {'Zenith': ([0], [0, 10]), 'Azimuth': ([0], [0, 180])}}

To reset back to the original template:

    >>> eris.reset()

## PSF FITS file format

The TIPTOP server returns a FITS file with 5 HDUs:

    >>> eris = TipTop("ERIS")
    >>> result = eris.generate_psf()
    >>> result
    TipTopResult(1 wavelength(s), 1 position(s), 5 HDUs, Strehl=0.891)

    HDU 0: PrimaryHDU — header with config parameters and timing
    HDU 1: ImageHDU   — PSF CUBE (N, FOV, FOV)
    HDU 2: ImageHDU   — OPEN-LOOP PSF (FOV, FOV)
    HDU 3: ImageHDU   — DIFFRACTION LIMITED PSF (FOV, FOV)
    HDU 4: ImageHDU   — Radial profiles

Strehl ratios, FWHM values, and coordinates are read from the PSF CUBE header cards.

## Documentation

Full documentation is available at [tiptop-ipy.readthedocs.io](https://tiptop-ipy.readthedocs.io).

For details on the TIPTOP configuration parameters, see the
[TIPTOP documentation](https://tiptopdoc.readthedocs.io/en/latest/parameterFile.html).

For bug reports and feature requests, please use the
[GitHub issues page](https://github.com/astronomyk/tiptop_ipy/issues).
