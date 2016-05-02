#!/usr/bin/python
# dedupeWH.py
#
#
# Title:        Dedupe the White House Visitors for DDRL Entity Resolution Project
# Author:       Rebecca Bilbro
# Version:      2.0
# Date:         last updated 4/25/16
# Organization: District Data Labs

# Based on https://github.com/datamade/dedupe-examples/tree/master/pgsql_big_dedupe_example
#####################################################################
# Imports
#####################################################################
import os
import csv
import tempfile
import time
import logging
import optparse
import locale

import psycopg2
import psycopg2.extras

import dedupe

#####################################################################
# PostgreSQL Connection and Fixtures
#####################################################################
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

settings_file = 'wh_psql_settings'
training_file = 'wh_psql_training.json'

start_time = time.time()

con = psycopg2.connect(dbname='whitehouse', user='Tinkerbell', host='localhost', password='')
con2 = psycopg2.connect(dbname='whitehouse', user = 'Tinkerbell', host='localhost', password='')
c = con.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

VISITOR_SELECT = 'SELECT * FROM visitors_er'


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

    cur = con.cursor('visitor_select')

    cur.execute(VISITOR_SELECT)
    temp_d = dict((i, row) for i, row in enumerate(cur))

    deduper.sample(temp_d, 75000)
    del temp_d

    if os.path.exists(training_file):
        print 'reading labeled examples from ', training_file
        with open(training_file) as tf :
            deduper.readTraining(tf)

    print 'starting active labeling...'

    dedupe.convenience.consoleLabel(deduper)

    with open(training_file, 'w') as tf:
        deduper.writeTraining(tf)

    deduper.train(maximum_comparisons=500000000, recall=0.90)

    with open(settings_file, 'w') as sf :
        deduper.writeSettings(sf)

    deduper.cleanupTraining()

print 'blocking...'

print 'creating blocking_map database'
c.execute("DROP TABLE IF EXISTS blocking_map")
c.execute("CREATE TABLE blocking_map "
          "(block_key VARCHAR(200), visitor_id INTEGER)")

print 'creating inverted index'

for field in deduper.blocker.index_fields:
    c2 = con.cursor('c2')
    c2.execute("SELECT DISTINCT %s FROM visitors_er" % field)
    field_data = (row[field] for row in c2)
    deduper.blocker.index(field_data, field)
    c2.close()

print 'writing blocking map'

c3 = con.cursor('visitor_select2')
c3.execute(VISITOR_SELECT)
full_data = ((row['visitor_id'], row) for row in c3)
b_data = deduper.blocker(full_data)

csv_file = tempfile.NamedTemporaryFile(prefix='blocks_', delete=False)
csv_writer = csv.writer(csv_file)
csv_writer.writerows(b_data)
c3.close()
csv_file.close()

f = open(csv_file.name, 'r')
c.copy_expert("COPY blocking_map FROM STDIN CSV", f)
f.close()

os.remove(csv_file.name)

con.commit()

print 'prepare blocking table. this will probably take a while ...'

logging.info("indexing block_key")
c.execute("CREATE INDEX blocking_map_key_idx ON blocking_map (block_key)")

c.execute("DROP TABLE IF EXISTS plural_key")
c.execute("DROP TABLE IF EXISTS plural_block")
c.execute("DROP TABLE IF EXISTS covered_blocks")
c.execute("DROP TABLE IF EXISTS smaller_coverage")

logging.info("calculating plural_key")
c.execute("CREATE TABLE plural_key "
          "(block_key VARCHAR(200), "
          " block_id SERIAL PRIMARY KEY)")

c.execute("INSERT INTO plural_key (block_key) "
          "SELECT block_key FROM blocking_map "
          "GROUP BY block_key HAVING COUNT(*) > 1")

logging.info("creating block_key index")
c.execute("CREATE UNIQUE INDEX block_key_idx ON plural_key (block_key)")

logging.info("calculating plural_block")
c.execute("CREATE TABLE plural_block "
          "AS (SELECT block_id, visitor_id "
          " FROM blocking_map INNER JOIN plural_key "
          " USING (block_key))")

logging.info("adding visitor_id index and sorting index")
c.execute("CREATE INDEX plural_block_visitor_id_idx ON plural_block (visitor_id)")
c.execute("CREATE UNIQUE INDEX plural_block_block_id_visitor_id_uniq "
          " ON plural_block (block_id, visitor_id)")


logging.info("creating covered_blocks")
c.execute("CREATE TABLE covered_blocks "
          "AS (SELECT visitor_id, "
          " string_agg(CAST(block_id AS TEXT), ',' ORDER BY block_id) "
          "   AS sorted_ids "
          " FROM plural_block "
          " GROUP BY visitor_id)")

c.execute("CREATE UNIQUE INDEX covered_blocks_visitor_id_idx "
          "ON covered_blocks (visitor_id)")

con.commit()

logging.info("creating smaller_coverage")
c.execute("CREATE TABLE smaller_coverage "
          "AS (SELECT visitor_id, block_id, "
          " TRIM(',' FROM split_part(sorted_ids, CAST(block_id AS TEXT), 1)) "
          "      AS smaller_ids "
          " FROM plural_block INNER JOIN covered_blocks "
          " USING (visitor_id))")

con.commit()

def candidates_gen(result_set):
    lset = set

    block_id = None
    records = []
    i = 0
    for row in result_set:
        if row['block_id'] != block_id:
            if records:
                yield records

            block_id = row['block_id']
            records = []
            i += 1

            if i % 10000 == 0:
                print i, "blocks"
                print time.time() - start_time, "seconds"

        smaller_ids = row['smaller_ids']

        if smaller_ids:
            smaller_ids = lset(smaller_ids.split(','))
        else:
            smaller_ids = lset([])

        records.append((row['visitor_id'], row, smaller_ids))

    if records:
        yield records


c4 = con.cursor('c4')
c4.execute("SELECT visitor_id, lastname, firstname, "
           "uin, apptmade, apptstart, "
           "apptend, meeting_loc, block_id, smaller_ids "
           "FROM smaller_coverage "
           "INNER JOIN visitors_er "
           "USING (visitor_id) "
           "ORDER BY (block_id)")

print 'clustering...'
clustered_dupes = deduper.matchBlocks(candidates_gen(c4),
                                      threshold=0.5)

c.execute("DROP TABLE IF EXISTS entity_map")

print 'creating entity_map database'
c.execute("CREATE TABLE entity_map "
          "(visitor_id INTEGER, canon_id INTEGER, "
          " cluster_score FLOAT, PRIMARY KEY(visitor_id))")

csv_file = tempfile.NamedTemporaryFile(prefix='entity_map_', delete=False)
csv_writer = csv.writer(csv_file)


for cluster, scores in clustered_dupes:
    cluster_id = cluster[0]
    for visitor_id, score in zip(cluster, scores) :
        csv_writer.writerow([visitor_id, cluster_id, score])

c4.close()
csv_file.close()

f = open(csv_file.name, 'r')
c.copy_expert("COPY entity_map FROM STDIN CSV", f)
f.close()

os.remove(csv_file.name)

con.commit()

c.execute("CREATE INDEX head_index ON entity_map (canon_id)")
con.commit()

print '# duplicate sets'
print len(clustered_dupes)

c.close()
con.close()

print 'ran in', time.time() - start_time, 'seconds'
