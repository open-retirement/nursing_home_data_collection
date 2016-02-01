#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module: long_term_cost_care.py
Author: zlamberty
Created: 2015-08-18

Description:
    scripts for getting all pdfs of nursing home reports available on
    http://www2.illinois.gov/hfs/MedicalProvider/CostReports/Pages/2013LongTermCareCostReports.aspx

    and parsing them for useful info

Usage:
    <usage>

"""

import argparse
import csv
import logging
import logging.config
import os
import requests
import yaml

from lxml import html, etree


# ----------------------------- #
#   Module Constants            #
# ----------------------------- #

URL = "http://www.illinois.gov/hfs/MedicalProviders/CostReports/Pages/2014LongTermCareCostReports.aspx"
HERE = os.path.dirname(os.path.realpath(__file__))
DATA_DIR = os.path.join(HERE, 'data', 'long_term_cost_care')
logger = logging.getLogger("long_term_cost_care")
LOGCONF = os.path.join(HERE, 'logging.yaml')
with open(LOGCONF, 'rb') as f:
    logging.config.dictConfig(yaml.load(f))


# ----------------------------- #
#   Main routine                #
# ----------------------------- #

def make_wget_script(url=URL, fdir=DATA_DIR):
    # grab url and look for pdf hrefs
    resp = requests.get(url)
    pdfurls = find_pdf_urls(resp)

    # we will download all files into local data fdir
    if not os.path.isdir(fdir):
        os.makedirs(fdir)

    with open('wget_pdfs.sh', 'wb') as f:
        for u in pdfurls:
            fname = u.split('/')[-1]
            outname = os.path.join(fdir, fname)
            f.write('echo downloading {}...\n'.format(u))
            f.write('wget -q "{}" -O {}\n'.format(u, outname.replace(' ', '_')))

    os.chmod('wget_pdfs.sh', 0755)


def find_pdf_urls(resp):
    x = html.fromstring(resp.text)
    return x.xpath('//div[@class="link-item"]/a/@href')


def parse_xml(fdir=DATA_DIR, outname=None):
    """ given a directory fdir, grab all xml files within and parse for
        "meaningful" information (tbd later)

    """
    flist = [
        os.path.join(fdir, f) for f in os.listdir(fdir)
        if os.path.isfile(os.path.join(fdir, f))
        and os.path.splitext(f)[-1] == '.xml'
    ]

    parsedInfo = []
    for f in flist:
        bname = os.path.basename(f)
        logger.info('parsing {}'.format(bname))

        pi = {}
        pi['fname'] = bname

        pi['rn_hours'] = None
        pi['rn_wage'] = None
        pi['total_hours'] = None
        pi['idph_id'] = None
        pi['facility_name'] = None
        pi['medicare'] = None
        pi['medicaid'] = None
        pi['private_pay'] = None

        x_parser = etree.XMLParser(encoding='utf-8', recover=True)

        # Commented out to handle errors (previously was fromstring())
        #with open(f, 'rb') as fin:
        #    x = etree.parse(fin.read(), x_parser)
        x = etree.parse(f, x_parser)

        textnodes = x.xpath('/pdf2xml/page/text/b')
        if len(textnodes) < 50:
            textnodes = x.xpath('/pdf2xml/page/text')
        for (i, textnode) in enumerate(textnodes):
            try:
                t = textnode.text.strip()
            except:
                continue

            if t in ['Registered Nurses', '3 Registered Nurses']:
                try:
                    # next node is either the corresponding row end value (3) or
                    # the number of hrs worked by RNs
                    nextval = textnodes[i + 1].text.replace(',', '')

                    if nextval == '3':
                        pi['rn_hours'] = 0.0
                        pi['rn_wage'] = 0.0
                    else:
                        pi['rn_hours'] = float(nextval)

                        # 4 nodes down is the hourly wage
                        pi['rn_wage'] = float(textnodes[i + 4].text)
                except:
                    pass

            elif t == '14 TOTALS':
                try:
                    # iterate until you find the singular "14" value; then take
                    # step back
                    j = 1
                    subt = textnodes[i + j].text.strip()
                    while subt not in ['14', 'C. Percent Occupancy. (Column 5, line 14 divided by total licensed']:
                        j += 1
                        subt = textnodes[i + j].text.strip()

                    pi['total_hours'] = float(
                        textnodes[i + j - 1].text.replace(',', '')
                    )
                except:
                    pass

            elif t == 'IDPH License ID Number:':
                try:
                    # next node is the id
                    pi['idph_id'] = textnodes[i + 1].text.replace(',', '')
                except:
                    pass

            elif t == 'Facility Name:':
                try:
                    # next node is the fac name
                    pi['facility_name'] = textnodes[i + 1].text
                except:
                    pass

            elif t == 'Medicaid - Net Inpatient Revenue':
                nextval = textnodes[i + 1].text.replace(',', '')

                if nextval == '$':
                    valafter = textnodes[i + 2].text.replace(',', '')
                    if valafter  == '44':
                        pi['medicaid'] = 0
                    else:
                        pi['medicaid'] = valafter
                elif nextval == '44':
                    pi['medicaid'] = 0
                else:
                    pi['medicaid'] = nextval

            elif t == 'Private Pay - Net Inpatient Revenue':
                nextval = textnodes[i + 1].text.replace(',', '')

                if nextval == '$':
                    valafter = textnodes[i + 2].text.replace(',', '')
                    if valafter  == '45':
                        pi['private_pay'] = 0
                    else:
                        pi['private_pay'] = valafter
                elif nextval == '45':
                    pi['private_pay'] = 0
                else:
                    pi['private_pay'] = nextval

            elif t == 'Medicare - Net Inpatient Revenue':
                nextval = textnodes[i + 1].text.replace(',', '')

                if nextval == '$':
                    valafter = textnodes[i + 2].text.replace(',', '')
                    if valafter  == '46':
                        pi['medicare'] = 0
                    else:
                        pi['medicare'] = valafter
                elif nextval == '46':
                    pi['medicare'] = 0
                else:
                    pi['medicare'] = nextval

        parsedInfo.append(pi)

    if outname:
        with open(outname, 'wb') as f:
            c = csv.DictWriter(f, fieldnames=parsedInfo[0].keys())
            c.writeheader()
            c.writerows(parsedInfo)

    return parsedInfo


# ----------------------------- #
#   Command line                #
# ----------------------------- #

def parse_args():
    """ Take a log file from the commmand line """
    parser = argparse.ArgumentParser()
    subcmds = parser.add_subparsers(dest="ltcc_cmd", help="Type of command to run")

    wgetsh = "create an executible shell script to wget all pdfs into a local directory"
    wget = subcmds.add_parser("make_wget", help=wgetsh)

    urlhelp = "the url with pdf hrefs (sane default, won't print because it's too long)"
    wget.add_argument("--url", help=urlhelp, default=URL)

    parsexml = "parse the xml files for pre-identified meaningful quantities"
    pxml = subcmds.add_parser("parse_xml", help=parsexml)

    fdir = "The directory of the xml files we will parse"
    pxml.add_argument("--fdir", help=fdir, default=DATA_DIR)
    outname = "The path to the csv file with the parsed results"
    pxml.add_argument("--outname", help=outname, required=True)

    return parser.parse_args()


if __name__ == '__main__':

    args = parse_args()

    if args.ltcc_cmd == 'make_wget':
        make_wget_script()
    elif args.ltcc_cmd == 'parse_xml':
        parse_xml(fdir=args.fdir, outname=args.outname)
