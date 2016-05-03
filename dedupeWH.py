#!/usr/bin/python
# dedupeWH.py
#
#
# Title:        Dedupe the White House Visitors for DDRL Entity Resolution Project
# Author:       Rebecca Bilbro
# Version:      2.0
# Date:         last updated 5/2/16
# Organization: District Data Labs

# Based on https://github.com/datamade/dedupe-examples/tree/master/pgsql_big_dedupe_example
# and https://github.com/dchud/osha-dedupe/blob/master/pgdedupe.py
#####################################################################
# Imports
#####################################################################
import tempfile
import argparse
import csv
import os

import dedupe
import psycopg2
from psycopg2.extras import DictCursor


KEY_FIELD = 'visitor_id'
SOURCE_TABLE = 'visitors'


FIELDS =  [{'field': 'firstname', 'variable name': 'firstname',
               'type': 'String','has missing': True},
              {'field': 'lastname', 'variable name': 'lastname',
               'type': 'String','has missing': True},
              {'field': 'uin', 'variable name': 'uin',
               'type': 'String','has missing': True},
              {'field': 'apptmade', 'variable name': 'apptmade',
               'type': 'String','has missing': True},
            #   {'field': 'apptstart', 'variable name': 'apptstart',
            #    'type': 'String','has missing': True},
              {'field': 'meeting_loc', 'variable name': 'meeting_loc',
               'type': 'String','has missing': True}
              ]


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
                print '%s blocks' % i

        smaller_ids = row['smaller_ids']
        if smaller_ids:
            smaller_ids = lset(smaller_ids.split(','))
        else:
            smaller_ids = lset([])

        records.append((row[KEY_FIELD], row, smaller_ids))

    if records:
        yield records


# @profile
def main(args):
    deduper = dedupe.Dedupe(FIELDS)

    with psycopg2.connect(database=args.dbname,
                          host='localhost',
                          cursor_factory=DictCursor) as con:
        with con.cursor() as c:
            # Generate a sample size
            c.execute('SELECT COUNT(*) AS count FROM %s' % SOURCE_TABLE)
            row = c.fetchone()
            count = row['count']
            sample_size = int(count * args.sample)

            # Create the sample (warning: very memory intensive)
            print 'Generating sample of %s records' % sample_size
            with con.cursor('deduper') as c_deduper:
                c_deduper.execute('SELECT * FROM %s' % SOURCE_TABLE)
                temp_d = dict((i, row) for i, row in enumerate(c_deduper))
                deduper.sample(temp_d, sample_size)
                del(temp_d)

            # Load training data (no problem if it doesn't exist yet)
            if os.path.exists(args.training):
                print 'Loading training file from %s' % args.training
                with open(args.training) as tf:
                    deduper.readTraining(tf)

            # Active learning time
            print 'Starting active learning'
            dedupe.convenience.consoleLabel(deduper)

            print 'Starting training'
            deduper.train(ppc=0.001, uncovered_dupes=5)

            print 'Saving new training file to %s' % args.training
            with open(args.training, 'w') as training_file:
                deduper.writeTraining(training_file)

            deduper.cleanupTraining()

            # Blocking
            print 'Creating blocking_mapp table'
            c.execute("""
                DROP TABLE IF EXISTS blocking_mapp
                """)
            c.execute("""
                CREATE TABLE blocking_mapp
                (block_key VARCHAR(200), %s INTEGER)
                """ % KEY_FIELD)

            # Generate inverted index for each field
            for field in deduper.blocker.index_fields:
                print 'Selecting distinct values for "%s"' % field
                c_index = con.cursor('index')
                c_index.execute("""
                    SELECT DISTINCT %s FROM %s
                    """ % (field, SOURCE_TABLE))
                field_data = (row[field] for row in c_index)
                deduper.blocker.index(field_data, field)
                c_index.close()

            # Generating blocking map
            print 'Generating blocking map'
            c_block = con.cursor('block')
            c_block.execute("""
                SELECT * FROM %s
                """ % SOURCE_TABLE)
            full_data = ((row[KEY_FIELD], row) for row in c_block)
            b_data = deduper.blocker(full_data)

            print 'Inserting blocks into blocking_map'
            csv_file = tempfile.NamedTemporaryFile(prefix='blocks_', delete=False)
            csv_writer = csv.writer(csv_file)
            csv_writer.writerows(b_data)
            csv_file.close()

            f = open(csv_file.name, 'r')
            c.copy_expert("COPY blocking_mapp FROM STDIN CSV", f)
            f.close()

            os.remove(csv_file.name)

            con.commit()

            print 'Indexing blocks'
            c.execute("""
                CREATE INDEX blocking_mapp_key_idx ON blocking_mapp (block_key)
                """)
            c.execute("DROP TABLE IF EXISTS plural_key")
            c.execute("DROP TABLE IF EXISTS plural_block")
            c.execute("DROP TABLE IF EXISTS covered_blocks")
            c.execute("DROP TABLE IF EXISTS smaller_coverage")

            print 'Calculating plural_key'
            c.execute("""
                CREATE TABLE plural_key
                (block_key VARCHAR(200),
                block_id SERIAL PRIMARY KEY)
                """)
            c.execute("""
                INSERT INTO plural_key (block_key)
                SELECT block_key FROM blocking_mapp
                GROUP BY block_key HAVING COUNT(*) > 1
                """)

            print 'Indexing block_key'
            c.execute("""
                CREATE UNIQUE INDEX block_key_idx ON plural_key (block_key)
                """)

            print 'Calculating plural_block'
            c.execute("""
                CREATE TABLE plural_block
                AS (SELECT block_id, %s
                FROM blocking_mapp INNER JOIN plural_key
                USING (block_key))
                """ % KEY_FIELD)

            print 'Adding %s index' % KEY_FIELD
            c.execute("""
                CREATE INDEX plural_block_%s_idx
                    ON plural_block (%s)
                """ % (KEY_FIELD, KEY_FIELD))
            c.execute("""
                CREATE UNIQUE INDEX plural_block_block_id_%s_uniq
                ON plural_block (block_id, %s)
                """ % (KEY_FIELD, KEY_FIELD))

            print 'Creating covered_blocks'
            c.execute("""
                CREATE TABLE covered_blocks AS
                    (SELECT %s,
                            string_agg(CAST(block_id AS TEXT), ','
                            ORDER BY block_id) AS sorted_ids
                     FROM plural_block
                     GROUP BY %s)
                 """ % (KEY_FIELD, KEY_FIELD))

            print 'Indexing covered_blocks'
            c.execute("""
                CREATE UNIQUE INDEX covered_blocks_%s_idx
                    ON covered_blocks (%s)
                """ % (KEY_FIELD, KEY_FIELD))
            print 'Committing'

            print 'Creating smaller_coverage'
            c.execute("""
                CREATE TABLE smaller_coverage AS
                    (SELECT %s, block_id,
                        TRIM(',' FROM split_part(sorted_ids,
                                                 CAST(block_id AS TEXT), 1))
                         AS smaller_ids
                     FROM plural_block
                     INNER JOIN covered_blocks
                     USING (%s))
                """ % (KEY_FIELD, KEY_FIELD))
            con.commit()

            print 'Clustering...'
            c_cluster = con.cursor('cluster')
            c_cluster.execute("""
                SELECT *
                FROM smaller_coverage
                INNER JOIN %s
                    USING (%s)
                ORDER BY (block_id)
                """ % (SOURCE_TABLE, KEY_FIELD))
            clustered_dupes = deduper.matchBlocks(
                    candidates_gen(c_cluster), threshold=0.5)

            print 'Creating entity_map table'
            c.execute("DROP TABLE IF EXISTS entity_map")
            c.execute("""
                CREATE TABLE entity_map (
                    %s INTEGER,
                    canon_id INTEGER,
                    cluster_score FLOAT,
                    PRIMARY KEY(%s)
                )""" % (KEY_FIELD, KEY_FIELD))

            print 'Inserting entities into entity_map'
            for cluster, scores in clustered_dupes:
                cluster_id = cluster[0]
                for key_field, score in zip(cluster, scores):
                    c.execute("""
                        INSERT INTO entity_map
                            (%s, canon_id, cluster_score)
                        VALUES (%s, %s, %s)
                        """ % (KEY_FIELD, key_field, cluster_id, score))

            print 'Indexing head_index'
            c_cluster.close()
            c.execute("CREATE INDEX head_index ON entity_map (canon_id)")
            con.commit()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--dbname', dest='dbname', default='whitehouse',
                        help='database name')
    parser.add_argument('-s', '--sample', default=0.10, type=float,
                        help='sample size (percentage, default 0.10)')
    parser.add_argument('-t', '--training', default='training.json',
                        help='name of training file')
    args = parser.parse_args()


    main(args)
