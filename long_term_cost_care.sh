#!/bin/bash
# this script will hit up this url:
#  http://www2.illinois.gov/hfs/MedicalProvider/CostReports/Pages/2013LongTermCareCostReports.aspx
# to pull down all pdfs. It will then parse the pdfs into text, and execute a
# python script to synthesize the (really messy) output into a usable csv

# exit on any error
set -e


# defining functions ----------------------------------------------------------

# downloading all ltcc pdf files
function get_pdfs {
    echo "                                    "
    echo "************************************"
    echo "*  downloading pdfs                *"
    echo "************************************"
    echo "                                    "
    ## create wget script of all links on the main page
    python long_term_cost_care.py make_wget

    ## run the script just generated
    ./wget_pdfs.sh
}

# converting pdfs (to xml)
function pdfs_to_xml {
    echo "                                    "
    echo "************************************"
    echo "*  converting pdfs to xml          *"
    echo "************************************"
    echo "                                    "
    ## convert each to xml if possible
    DIR="data/long_term_cost_care"
    for i in $(ls $DIR/*.pdf); do
        SRC="${i}"
        DST="${i%.*}.xml"
        BN=$(basename ${i})
        echo "converting ${BN} to xml"
        pdftohtml -xml -q $SRC $DST
    done
}

# parsing converted xml files for output data
function parse_xml {
    echo "                                    "
    echo "************************************"
    echo "*  parsing xml files for info      *"
    echo "************************************"
    echo "                                    "
    ## convert each to xml if possible
    DIR="data/long_term_cost_care"
    OUTNAME="parsed_pdf_info.csv"
    python long_term_cost_care.py parse_xml --fdir $DIR --outname $OUTNAME
}

# simple help text
function help {
    echo "usage: $(basename "$0") {run|get_pdfs|pdfs_to_xml} -- various"
    echo "commands for downloading and acquiring data related to nursing"
    echo "home comparisons"
    echo ""
    echo "cmd options:"
    echo "  help        - generate this help text"
    echo "  run         - get_pdfs && pdfs_to_xml && parse_xml"
    echo "  get_pdfs    - download all Cost Report files from www2.illinois.gov/"
    echo "  pdfs_to_xml - convert downloaded pdfs to xml files"
    echo "  parse_xml   - parse the converted xmls for our desired data"
    exit
}

# The whole shebang
function run {
    get_pdfs && pdfs_to_xml && parse_xml
}


# script cmd line hooks -------------------------------------------------------

# usage / vars
if [ -z "$1" ]; then
    help
fi

CMD=$1

if [[ $1 =~ ^(-h|--help|help)$ ]]; then
    help
elif [[ $1 =~ ^(run|get_files|pdfs_to_xml|parse_xml)$ ]]; then
    "$@"
else
    echo "Invalid subcommand $1" >&2
    exit 1
fi
