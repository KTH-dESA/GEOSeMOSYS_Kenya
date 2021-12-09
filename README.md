# GEOSeMOSYS_Kenya
This repository is for paper ****High spatial and temporal resolution in linear programming - the case of Kenya****, by: Nandi Moksnes, Mark Howells, Will Usher

To be able to run the model you need to have approx 512 GB RAM. This model has been run on a High performance cluster at KTH.
The shell file is therefor applicable for the HPC at PDC Tegner from SNIC (Swedish National Infrastructure for Computing).

The whole workflow is run in Jupyter Notebook.

# Dependencies
The workflow has a number packages that needs to be installed.

The easiest way to install the Python packages is to use miniconda.

Obtain the miniconda package (https://docs.conda.io/en/latest/miniconda.html):
1) Add the conda-forge channel: **conda config --add channels conda-forge**
2) Create a new Python environment: **conda env create -f environment.yml**
3) Activate the new environment: **conda activate geosemosys**

# Required accounts (free to register)
To run the code you need to create accounts in the following places:
- https://www.renewables.ninja/ and get the token to download several files per hour
- https://payneinstitute.mines.edu/eog/nighttime-lights/ and the password is entered in the first cell in the notebook

To run the code go the folder where the code is place and write: ****juputer notebook**** and the 
open the src/GEOSeMOSYS - exploring linear programming geospatial modelling.ipynb

Run the code step by step. The building of the model takes about 24 hours to run. This is related to several aspects but several of the functions that are calculating how near distance to the 11 kV transmission lines is very heavy. The renewables.ninja account only allows for 50 dowinload per hour which (if you have many locations and technologies) makes the run longer.
