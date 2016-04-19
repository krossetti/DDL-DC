#!/usr/bin/python
# dateparse.py
#
#
# Title:        Date Time Parser for Entity Resolution Project
# Author:       Rebecca Bilbro
# Version:      3.0
# Date:         last updated 4/19/16
# Organization: District Data Labs


"""
Date/time parsing tools to assist with entity resolution project.
"""
import csv
import time
import psycopg2
import requests
from datetime import datetime
from dateutil import parser

#####################################################################
# Connect to PostgreSQL
#####################################################################
conn = None
try:
    conn = psycopg2.connect(database='whitehouse', user='Tinkerbell', host='localhost', password='')
    print "I've connected"
except:
    print "I am unable to connect to the database"
cur = conn.cursor()



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

def dateParseCSV(nfile,ofile):
    """
    Take the raw file as input.
    Parse the three datetime fields we care about.
    Create a clean file for entity resolution with just the fields:
    'lastname','firstname','uin','apptmade','apptstart','apptend', 'meeting_loc'
    """
    with open(ofile, 'w') as outfile:
        writer = csv.writer(outfile, delimiter=',')
        writer.writerow(['lastname','firstname','uin','apptmade','apptstart','apptend','meeting_loc'])
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
                writer.writerow([row[0],row[1],row[3],row[10],row[11],row[12],row[21]])

def dateParseSQL(nfile):
    """
    Reads in data from csv and parses the datetime fields we're interested in:
    'lastname','firstname','uin','apptmade','apptstart','apptend', 'meeting_loc'.

    Creates a new table in the database with just those fields for use in the
    entity resolution task.
    """
    cur.execute('''CREATE TABLE IF NOT EXISTS visitors_er
                  (lastname   varchar,
                  firstname   varchar,
                  uin         varchar,
                  apptmade    varchar,
                  apptstart   varchar,
                  apptend     varchar,
                  meeting_loc varchar);''')
    conn.commit()
    with open(nfile, 'rU') as infile:
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
            sql = "INSERT INTO visitors_er(lastname,firstname,uin,apptmade,apptstart,apptend,meeting_loc) \
                   VALUES (%s,%s,%s,%s,%s,%s,%s)"
            cur.execute(sql, (row[0],row[1],row[3],row[10],row[11],row[12],row[21],))
            conn.commit()
    print "All done!"



if __name__ == '__main__':
    ## If you don't already have the data, uncomment the line below - be warned it will take a while!
    DATAURL = "https://open.whitehouse.gov/api/views/p86s-ychb/rows.csv?accessType=DOWNLOAD"
    ORIGFILE = "fixtures/whitehouse-visitors.csv"
    # start_time = time.time()
    # getData(DATAURL,ORIGFILE)
    # print 'ran in', time.time() - start_time, 'seconds'


    ## To parse the date time fields and output to csv - this will also take a while!
    CLEANFILE = "fixtures/whitehouse-visitors-cl.csv"
    # start_time = time.time()
    # dateParse(ORIGFILE,CLEANFILE)
    # print 'ran in', time.time() - start_time, 'seconds'


    ## To parse the date time fields and output to a new PostgreSQL table - this will also take a while!
    start_time = time.time()
    dateParseSQL(ORIGFILE)
    print 'ran in', time.time() - start_time, 'seconds'
