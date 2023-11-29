#!/usr/bin/env python
# It would be super cool to spend time getting the configuration files to work
import argparse
import argparsedirs
import logging
import configparser

from pathlib import Path
from scalyca import Scala
from tiptop_ipy.tiptop_connection import TipTopConnection
from enschema import Schema, Or, And, Optional
from schema import SchemaError
from tiptop_ipy.validatedconfig import TiptopConfig
import scalyca.colour as c

log = logging.getLogger('root')

number = Or(int, float)


class TipTop(Scala):
    _app_name = "TipTop ipy"
    _prog = "TipTop ipy"

    def add_arguments(self):
        self.add_argument('template', type=argparse.FileType('r'))
        self.add_argument('outdir', action=argparsedirs.WriteableDir)
        self.add_argument('--dry-run', action='store_true')

    def initialize(self):
        try:
            self.parser = TiptopConfig.load(Path(self.args.template.name))
            log.info(f"Successfully validated template file {c.path(self.args.template.name)} against schema")
        except SchemaError as e:
            log.error(f"Could not validate template tile {c.path(self.args.template.name)}!")
            raise e

    def main(self):
        connection = TipTopConnection(Path(self.args.template.name))
        log.info(f"Making a request with config file {c.path(self.args.template.name)}")
        if self.args.dry_run:
            return
        hdu = connection.query_server()
        outfile = Path(self.args.outdir) / Path(self.args.template.name).with_suffix('.fits').name
        log.info(f"Saving the output to {c.path(outfile)}")
        connection.writeto(outfile, overwrite=True)


if __name__ == "__main__":
    TipTop().run()
