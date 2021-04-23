# GEOSeMOSYS_Kenya
This repository is for paper GEOSeMOSYS Kenya, by: Nandi Moksnes, Mark Howells, ...

To be able to run the model you need to run it on a HPC computer with at least 512 GB RAM - 24 cores.
This code is adjusted for the cluster at PDC Tegner from SNIC (Swedish National Infrastructure for Computing).

The whole workflow is run in Jupyter Notebook.

# Dependencies
The workflow has a number packages that needs to be installed.

The easiest way to install the Python packages is to use miniconda.

Obtain the miniconda package (https://docs.conda.io/en/latest/miniconda.html):
1) Add the conda-forge channel conda config --add channels conda-forge
2) Create a new Python environment: conda env create -f environment.yml
3) Activate the new environment conda activate geosemosys

Then open the src/GEOSeMOSYS - exploring linear programming geospatial modelling.ipynb in Jupyter Notebook

Run the code step by step.
