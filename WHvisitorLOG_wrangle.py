#!/usr/bin/env python
"""
This code wrangles the White House visitor logs into normalized data to
push into the DB. The attributes being modified are parsing the DATE & TIME into
separate fields

"""
##########################################################################
## required imports
##########################################################################

import datetime # required for
import dateutil # required for normalization of the date
import psycopg2 #required to access psql db
import csv 



#db parameters
DB = 'WhiteHouse.Visitors'
user = 'postgres'
password = 'psqlpass'
host = 'localhost'
port = '5432'

##########################################################################
## Functions
##########################################################################

#connect to the db
conn_str="host={} port={} dbname={} user={} password={}".format(host, port, DB, user, password)
conn=psycopg2.connect(conn_str)
c=conn.cursor()


##########################################################################
## Execution
##########################################################################

if __name__ == '__main__':
    main()
