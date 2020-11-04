from urllib.request import Request, urlopen
import shutil

req = snakemake.params[0]

with urlopen(req) as response:
    with open(snakemake.output[0], 'wb') as out_file:
        shutil.copyfileobj(response, out_file)