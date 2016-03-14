#!/usr/bin/python
# dateparse.py
#
#
# Title:        Date Time Parser for Entity Resolution Project
# Author:       Rebecca Bilbro
# Version:      1.0
# Date:         last updated 3/13/16
# Organization: District Data Labs


"""
Date/time parsing tools to assist with entity resolution project.
"""
import csv
import requests
from datetime import datetime
from dateutil import parser


#####################################################################
# Ingestion Tools
#####################################################################
def getData(url,fname):
    """
    Download the dataset from the webpage.
    """
    response = requests.get(url)
    with open(fname, 'w') as f:
        f.write(response.content)

#####################################################################
# Parsing
#####################################################################
DATEFIELDS = [10,11,12]

def dateParse(nfile,ofile):
    """
    Take the raw file as input.
    Parse the three datetime fields we care about.
    Create a clean file for entity resolution with just the fields:
    'lastname','firstname','uin','apptmade','apptstart','apptend'
    """
    with open(ofile, 'w') as outfile:
        writer = csv.writer(outfile, delimiter=',')
        writer.writerow(['lastname','firstname','uin','apptmade','apptstart','apptend'])
        with open(nfile, 'rb') as infile:
            reader = csv.reader(infile, delimiter=',')
            next(reader, None)
            for row in reader:
                for field in DATEFIELDS:
                    if row[field] != '':
                        try:
                            dt = parser.parse(row[field])
                            row[field] = dt.isoformat()
                        except:
                            continue
                writer.writerow([row[0],row[1],row[3],row[10],row[11],row[12]])

if __name__ == '__main__':
    DATAURL = "https://open.whitehouse.gov/api/views/p86s-ychb/rows.csv?accessType=DOWNLOAD"
    ORIGFILE = "fixtures/whitehouse-visitors.csv"
    # If you don't already have the data, uncomment the line below - be warned it will take a while!
    # getData(DATAURL,ORIGFILE)

    # To parse the date time fields - this will also take a while!
    CLEANFILE = "fixtures/whitehouse-visitors-cl.csv"
    dateParse(ORIGFILE,CLEANFILE)
