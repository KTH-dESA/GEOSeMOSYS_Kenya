rule all:
	input:
		"input_data/GIS_URL.txt"

rule download_files:
	input:
		wc='src/Download_files.py',
		url='input_data/GIS_URL.txt'
    output:"GIS_data/{file}.shp"
    shell: "python {input.wc} {input.url} {output}"
