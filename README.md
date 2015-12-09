# Long Term Care Cost Report Data Download

This is a hodge-podge of `bash` and `python` scripting to

1. Download a bunch of pdf files from [the Illinois HFS website](http://www.illinois.gov/hfs/MedicalProviders/CostReports/Pages/2014LongTermCareCostReports.aspx)
2. Convert the downloaded pdfs to xml format
3. Parse the xml files for information we have determined we will use for modeling purposes.


## Setup
The bash scripts will require the command line tool `pdftohtml` (part of the [poppler-utils package](http://packages.ubuntu.com/precise/poppler-utils)). Install via your system's package manager (e.g. on Debian)

```bash
sudo apt-get install poppler-utils
```

The python scripts will require an environment with a few non-standard python libraries available. I recommend a [conda](http://docs.continuum.io/anaconda/install) or pip virtual environment -- they can be created using `environments.yaml` (conda) or `requirements.txt` (`pip`). Choose one of the following:

```bash
# conda
conda env create -f environment.yml

# pip
pip install -r requirements.txt
```


## Usage

The help text for the `long_term_cost_care.sh` script should be sufficient, but just to be clear:

```bash
bash long_term_cost_care.sh [SUBCMD]
```

1. `get_pdfs` will download (with wget) all of the pdfs we will parse. Under the hood, this will:
  1. call the python `long_term_cost_care.py` script to create a `wget_pdfs.sh` shell script, and
  2. execute the `wget_pdfs.sh` script (actually does the downloading).
2. `pdfs_to_xml` will convert all pdfs in the download directory (`data/long_term_cost_care`) into xml
3. `parse_xml` will read all the xml files in `data/long_term_cost_care` looking for info and writing the output to './parsed_pdf_info.csv`
