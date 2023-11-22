#!/usr/bin/env python
# It would be super cool to spend time getting the configuration files to work
import argparse
import argparsedirs
import logging

from pathlib import Path
from scalyca import Scala
from tiptop_ipy.tiptop_connection import TipTopConnection
import scalyca.colour as c

log = logging.getLogger('root')


class TipTop(Scala):
    _app_name = "TipTop wrapper"
    _prog = "TipTop wrapper"

    def add_arguments(self):
        self.add_argument('template', type=argparse.FileType('r'))
        self.add_argument('outdir', action=argparsedirs.WriteableDir)

    def main(self):
        connection = TipTopConnection(self.args.template)
        log.info(f"Making a request with config file {c.path(self.args.template.name)}")
        hdu = connection.query_server()
        outfile = Path(self.args.outdir) / Path(self.args.template.name).with_suffix('.fits').name
        log.info(f"Saving the output to {c.path(outfile)}")
        connection.writeto(outfile, overwrite=True)


if __name__ == "__main__":
    TipTop().run()
