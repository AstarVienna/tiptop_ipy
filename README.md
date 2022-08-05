# TIPTOP-iPy

A wrapper for the ESO TIPTOP microservice

    $ pip install git+https://github.com/astronomyk/tiptop_ipy.git

## Basic Usage

List the instrument config files included in this version of TIPTOP-ipy

    >>> import tiptop_ipy

    >>> tiptop_ipy.list_instruments()
    ['ANDES.ini', 'eris.ini', 'eris_lgs.ini', 'HarmoniLTAO_1.ini', 'HarmoniSCAO_1.ini', 'mavis.ini', 'sphere.ini']

Create a ``TipTopConnection`` object and query the TIPTOP server
    
    >>> eris = tiptop_ipy.TipTopConnection("eris.ini")
    >>> eris.query_server()
    >>> eris.writeto("eris.fits", overwrite=True)

The astropy.io.fits.HDUList is held in the ``.hdulist`` property

    >>> eris.hdulist

Query the TIPTOP server directly with the raw string from an existing ``.ini`` config file

    >>> eris_path = tiptop_ipy.list_instruments(include_path=True)[1]
    >>> with open(eris_path) as f:
    >>>     eris_content = f.read()

    >>> hdulist = tiptop_ipy.utils.query_tiptop_server(ini_content=eris_content)
    >>> hdulist.writeto("eris.fits", overwrite=True)

## Playing with parameters

In general the parameters are kept in the ``.meta`` dictionary of the ``TipTopConnection`` object:

    >>> eris.meta
    {'telescope': {'TelescopeDiameter': 8.0, 'ZenithAngle': 30.0, 'ObscurationRatio': 0.16, ... }

Categories can also be accessed directly using the ``getitem`` syntax:

    >>> eris["sources_science"]
    {'Wavelength': [1.65e-06], 'Zenith': [0], 'Azimuth': [0]}

Values can be updated or changed using this syntax too.
For example, we can ask TIPTOP to generate two PSFs (on-axis, 10" off-axis) by doing this:

    >>> eris["sources_science"]["Zenith"] = [0, 10]
    >>> eris["sources_science"]["Azimuth"] = [0, 180]
    >>> eris.query_server()

    >>> from matplotlib import pyplot as plt     
    >>> from matplotlib.colors import LogNorm
    >>> for i in range(2): 
    >>>     plt.subplot(1, 2, i+1)
    >>>     plt.imshow(eris.hdulist[1].data[i, :, :], norm=LogNorm())
    >>> plt.show()

## PSF FITS file format

    >>> eris = tiptop_ipy.TipTopConnection("eris.ini")
    >>> eris.query_server()
    >>> eris.hdulist.info()
    No.    Name      Ver    Type      Cards   Dimensions   Format
    0  PRIMARY       1 PrimaryHDU       5   ()      
    1                1 ImageHDU        13   (256, 256, 1)   float64   
    2                1 ImageHDU        10   (1, 2)   float64  


## Documentation

The reader is referred to the [TIPTOP documentation](https://tiptopdoc.readthedocs.io/en/latest/parameterFile.html) for queries regarding the configuration parameters:

User documentation will appear soon for this package. 
In the meantime, feel free to contact me via the [GitHub issues page](https://github.com/astronomyk/tiptop_ipy/issues)