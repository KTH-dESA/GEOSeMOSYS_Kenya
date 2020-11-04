from urllib.request import Request, urlopen
import pandas as pd

configfile: "config/config.yaml"

urls = pd.read_csv(config['urls'])

rule all:
    input:
        expand("GIS_data/{x}", x=urls['name'])

def get_url(wildcards):
    return urls.set_index('name').loc[wildcards.file].tolist()[0]

rule download_files:
    params: get_url
    output: "GIS_data/{file}"
    script: "src/download.py"

