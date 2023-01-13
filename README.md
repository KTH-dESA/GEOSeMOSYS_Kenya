## GEOSeMOSYS_Kenya

This repository is for the paper

**Increasing spatial and temporal resolution in energy system optimization model – the case of Kenya**

Nandi Moksnes (1) *, Mark Howells (2,3), William Usher (1)
1)	KTH Royal Institute of Technology
2)	STEER Centre, Department of Geography & Environment, Loughborough University, UK
3)	Imperial College, London, United Kingdom

To be able to run the model you need to have approx 256 GB RAM. This model has been run on a High performance cluster at KTH.
The shell file is therefor applicable for the HPC at PDC Dardel from SNIC (Swedish National Infrastructure for Computing).

The whole workflow is run in Jupyter Notebook. The work flow is only tested on a Windows computer, therefore there might be small adjustements needed for other OS.

![image](https://user-images.githubusercontent.com/30128518/212334273-5084f5cf-25e2-4672-8c89-bdb5cd639706.png)

# Python dependencies
The workflow has a number packages that needs to be installed.

The easiest way to install the Python packages is to use miniconda.

Obtain the miniconda package (https://docs.conda.io/en/latest/miniconda.html):
1) Add the conda-forge channel: **conda config --add channels conda-forge**
2) Create a new Python environment: **conda env create -f environment.yml**
3) Activate the new environment: **conda activate geosemosys**

# R
To download the capacityfactors for solar and wind you need to have R on your computer.
You can download R for free https://www.r-project.org/
You also need to install the package "curl" which you install through the R commander
<pre><code>install.packages("curl")</code></pre>

# Required accounts (free to register)
To run the code you need to create accounts in the following places:
- https://www.renewables.ninja/ and get the token to download several files per hour
- https://payneinstitute.mines.edu/eog/nighttime-lights/ and the password is entered in the first cell in the notebook

# Run the model
To run the code go the src folder and write: ****juputer notebook**** and then 
open the src/GEOSeMOSYS - exploring linear programming geospatial modelling.ipynb

Run the code step by step. The building of the model takes about 24 hours to run. This is related to several aspects. One of the functions clips the vector file of the 11 kV transmission lines which consists of several hundreds of lines. The renewables.ninja account only allows for 50 download per hour which (if you have many locations and technologies) makes the run longer.
