#!/usr/bin/python
# dedupeWH.py
#
#
# Title:        Dedupe the White House Visitors for DDRL Entity Resolution Project
# Author:       Rebecca Bilbro
# Version:      1.0
# Date:         last updated 4/18/16
# Organization: District Data Labs

# Based on https://github.com/datamade/dedupe-examples/blob/master/pgsql_example/pgsql_example.py
#####################################################################
# Imports
#####################################################################
import dedupe
import os
import re
import collections
import time
import logging
import optparse

import psycopg2 as psy
import psycopg2.extras
from unidecode import unidecode

#####################################################################
# PostgreSQL Connection and Fixtures
#####################################################################
settings_file = 'postgres_settings'
training_file = 'postgres_training.json'
con = psy.connect(dbname='whitehouse', user='Tinkerbell', host='localhost', password='')
con2 = psy.connect(dbname='whitehouse', user = 'Tinkerbell', host='localhost', password='')
c = con.cursor(cursor_factory=psy.extras.RealDictCursor)



optp = optparse.OptionParser()
optp.add_option('-v', '--verbose', dest='verbose', action='count',
                help='Increase verbosity (specify multiple times for more)'
                )
(opts, args) = optp.parse_args()
log_level = logging.WARNING
if opts.verbose == 1:
    log_level = logging.INFO
elif opts.verbose >= 2:
    log_level = logging.DEBUG
logging.getLogger().setLevel(log_level)

start_time = time.time()

MAILING_SELECT = 'SELECT lastname,firstname, apptmade, apptstart, apptend, meeting_loc FROM visitors_cl'


if os.path.exists(settings_file):
    print 'reading from', settings_file
    with open(settings_file) as sf :
        deduper = dedupe.StaticDedupe(sf)

else:
    fields = [
        {'field' : 'lastname', 'type': 'String'},
        {'field' : 'firstname', 'type': 'String'},
        {'field' : 'apptmade', 'type': 'String', 'has missing' : True},
        {'field' : 'apptstart', 'type': 'String', 'has missing' : True},
        {'field' : 'apptend', 'type': 'String', 'has missing' : True},
        {'field' : 'meeting_loc', 'type': 'String', 'has missing' : True},
        ]

    deduper = dedupe.Dedupe(fields)

    deduper.sample(data_d, 150000)

    if os.path.exists(training_file):
        print 'reading labeled examples from ', training_file
        with open(training_file) as tf :
            deduper.readTraining(tf)

    print 'starting active labeling...'

    dedupe.consoleLabel(deduper)

    deduper.train()

    with open(training_file, 'w') as tf :
        deduper.writeTraining(tf)

    with open(settings_file, 'w') as sf :
        deduper.writeSettings(sf)

print 'blocking...'

threshold = deduper.threshold(data_d, recall_weight=2)

print 'clustering...'
clustered_dupes = deduper.match(data_d, threshold)

print '# duplicate sets', len(clustered_dupes)

c2 = con2.cursor()
c2.execute('SELECT * FROM visitors_cl')
data = c2.fetchall()

full_data = []

cluster_membership = collections.defaultdict(lambda : 'x')
for cluster_id, (cluster, score) in enumerate(clustered_dupes):
    for record_id in cluster:
        for row in data:
            if record_id == int(row[0]):
                row = list(row)
                row.insert(0,cluster_id)
                row = tuple(row)
                full_data.append(row)

columns = "SELECT column_name FROM information_schema.columns WHERE table_name = 'visitors_cl'"
c2.execute(columns)
column_names = c2.fetchall()
column_names = [x[0] for x in column_names]
column_names.insert(0,'cluster_id')

c2.execute('DROP TABLE IF EXISTS deduped_table')
field_string = ','.join('%s varchar(200)' % name for name in column_names)
c2.execute('CREATE TABLE deduped_table (%s)' % field_string)
con2.commit()

num_cols = len(column_names)
mog = "(" + ("%s,"*(num_cols -1)) + "%s)"
args_str = ','.join(c2.mogrify(mog,x) for x in full_data)
values = "("+ ','.join(x for x in column_names) +")"
c2.execute("INSERT INTO deduped_table %s VALUES %s" % (values, args_str))
con2.commit()
con2.close()
con.close()

print 'ran in', time.time() - start_time, 'seconds'
