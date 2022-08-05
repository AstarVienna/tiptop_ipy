# TIPTOP

TIPTOP PSF Simulation Wrapper for https://github.com/FabioRossiArcetri/TIPTOP

## Prerequisites

Linux Server with NVIDIA GPU acceleration, using dmogpu1 for now.

## Installation
Download and install Anaconda using suitable installer from https://www.anaconda.com/products/distribution#linux

```
$ conda create --name tiptop python=3.8
$ conda activate tiptop
$ conda install -c conda-forge cupy    
$ conda install ipython matplotlib scipy astropy sympy
$ conda install jupyter
$ conda install -c conda-forge jupyterlab
$ git clone https://github.com/FabioRossiArcetri/TIPTOP.git
$ cd TIPTOP
$ git clone https://github.com/FabioRossiArcetri/MASTSEL
$ git clone https://github.com/FabioRossiArcetri/SYMAO
$ git clone https://github.com/FabioRossiArcetri/SEEING
$ git clone https://github.com/oliviermartin-lam/P3/
$ cd P3
$ pip install -e .
$ cd ../SYMAO
$ pip install -e .
$ cd ../MASTSEL
$ pip install -e .
$ cd ../SEEING
$ pip install -e .
$ cd ..
$ pip install -e .
```

## How to invoke the simulation 
The `overallSimulation()` function takes 6 arguments
```
overallSimulation(
    <pathToIniFile>, 
    <IniFilenameWithoutExtension>, 
    <pathToOutputFile>, 
    <outputFilenameWithoutExtension>, 
    doPlot=False, 
    doConvolve=False)
```
and can be invoked as follows
```
$ python
>>> from tiptop.tiptop import *
>>> overallSimulation('perfTest', 'HarmoniSCAO_1', 'perfTest', 'harmoni', doPlot=False, doConvolve=False)
```

## Documentation
Some TIPTOP documentation can be found at https://tiptopdoc.readthedocs.io/en/latest/, specifically the section about input parameters that are read from the input `.ini` file is noteworthy https://tiptopdoc.readthedocs.io/en/latest/parameterFile.html


## Instrument-specific input files
In this repository "ini" files for SPHERE and ERIS in LGS mode were provided by INAF.


## Integration with the ESO Phase 2 Microservice Infrastructure
The microservice is _prototypically_ installed at http://dmogpu1.hq.eso.org:9999/p2services/eris/tiptop.

It can be invoked using a simple Python script
```
import requests
import email
import email.policy

url = 'http://dmogpu1.hq.eso.org:9999/p2services/eris/tiptop'
instrument = 'eris'
files = {
    'serviceDescription': ('serviceDescription.json', open('serviceDescription.json', 'rb'), 'application/json'),
    'parameterFile': (instrument + '.ini', open(instrument + '.ini', 'rb'), 'text/plain')
}
response = requests.post(url, files=files) 
if response.status_code == 200:
    # prepend multipart header
    msg = ('Content-type: ' + response.headers['Content-Type'] + '\n\n').encode() + response.content
    multipart = email.message_from_bytes(msg, policy=email.policy.HTTP);
    if (multipart.is_multipart()):
        for part in multipart.walk():
            fname = part.get_filename();
            if fname and fname.endswith('.fits'):
                with open(fname, 'wb') as f:
                    f.write(part.get_content());
                    print('created eris.fits');

```

The script invokes the microservice API and passes as inputs the `eris.ini` file and an almost empty (for now) `serviceDescription.json`. It produces 
an `eris.fits` file as output.

## Example Usage

Prerequisites: `git` command line tool, `Python 3` with `requests` library installed.

```
git clone https://gitlab.eso.org/dfs/tiptop.git
cd tiptop
python tiptop.py
```
This produces an`eris.fits` file after a few seconds in the local directory.

