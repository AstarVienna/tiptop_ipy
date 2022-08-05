import email
import email.policy
import requests
import json
from tempfile import TemporaryFile
from astropy.io import fits


def get_tiptop_psf(ini_content):

    with TemporaryFile() as ini_stream:
        ini_stream.write(ini_content.encode("ascii"))
        ini_stream.seek(0)

        url = f'http://dmogpu1.hq.eso.org:9999/p2services/eris/tiptop'
        desc_file = '../tiptop_ipy/instrument_templates/serviceDescription.json'
        files = {'serviceDescription': (desc_file, open(desc_file, 'rb'), 'application/json'),
                 'parameterFile': ("eris.ini", ini_stream, 'text/plain')}
        response = requests.post(url, files=files)

    if response.status_code == 200:
        # prepend multipart header
        msg = f"Content-type: {response.headers['Content-Type']}\n\n".encode() + response.content
        multipart = email.message_from_bytes(msg, policy=email.policy.HTTP)
        if multipart.is_multipart():
            for part in multipart.walk():
                if part.get_content_type() == "application/json":
                    dic = json.loads(part.get_content())
                    if "error" in dic.get("service"):
                        raise ValueError(f'Server could not parse {instrument}.ini file.\n"{dic["service"]["error"]}"')

                elif part.get_content_type() == "application/octet-stream":
                    fname = part.get_filename()
                    if fname and fname.endswith('.fits'):
                        with TemporaryFile(mode="w+b") as tmp:
                            tmp.write(part.get_content())
                            hdus = fits.open(tmp, mode="update", lazy_load_hdus=False)
                            _ = [hdu.data for hdu in hdus]  # force loading of data into RAM

    return hdus


if __name__ == "__main__":

    instrument = "mavis"

    with open(f"{instrument}.ini") as ini_file:
        ini_content = ini_file.read()

    hdus = get_tiptop_psf(ini_content=ini_content)
    hdus.writeto(f"{instrument}.fits", overwrite=True)
