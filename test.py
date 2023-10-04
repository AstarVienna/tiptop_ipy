# It would be super cool to spend time getting the configuration files to work
import argparse
import argparsedirs

from scalyca import Scala
from tiptop_ipy.tiptop_connection import TipTopConnection
import logging


log = logging.getLogger('root')
log.setLevel(logging.DEBUG)

class TipTop(Scala):
    app_name = "TIPTOP wrapper"
    prog = ""

    def add_arguments(self):
        self.argparser.add_argument('template', type=argparse.FileType('r'))
        self.argparser.add_argument('outdir', type=argparsedirs.WriteableDir)

    def main(self):
        connection = TipTopConnection(self.args.template)
        hdu = connection.query_server()
        hdu.write(self.args.outdir / 'tiptop.fits')


if __name__ == "__main__":
    TipTop().run()