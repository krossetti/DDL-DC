# Basics of Entity Resolution with Python and Dedupe
_by Kyle Rossetti and Rebecca Bilbro_


## Introduction    
### What is entity resolution?    
Entity resolution (ER) is the task of disambiguating records that correspond to real world entities across and within datasets. The applications of entity resolution are tremendous, particularly for public sector and federal datasets related to health, transportation, finance, law enforcement, and antiterrorism.  

Unfortunately, the problems associated with entity resolution are equally big &mdash; as the volume and velocity of data grow, inference across networks and semantic relationships between entities becomes more and more difficult. Data quality issues, schema variations, and idiosyncratic data collection traditions can all complicate these problems even further. When combined, such challenges amount to a substantial barrier to organizations’ ability to fully understand their data, let alone make effective use of predictive analytics to optimize targeting, thresholding, and resource management.  

### Naming your problem
Let us first consider what an entity is. Much as the key step in machine learning is to determine 'what is an instance', the key step in entity resolution is to determine 'what is an entity?' Taking a step back from the data realm, let's define an entity as a unique thing &mdash;  a person, a business, a product &mdash; that has a set of attributes that describe it &mdash; a name, an address, a shape, a title, a price, etc. But that single entity may have multiple references across data sources, like a person with two different email addresses, a company with two different phone numbers, or a product listed on two different websites, with slightly different descriptions. How can we tell that these multiple references point to the same entity? What happens when there are even more than two or three or ten references to the same entity, each slightly different? How can we determine which is the canonical version? What do we do with the duplicates? And if we want to ask questions about all the unique people, or businesses, or products in our dataset, how can we produce a final version of that dataset that is unique on entity? These questions are precisely why entity resolution is such a common issue in large data sets, albeit one that frequently goes unnamed.

Ironically, one of the problems in entity resolution is that even though it goes by a lot of different names, many people who struggle with entity resolution do not know the name of their problem. The three primary tasks involved in entity resolution are deduplication, record linkage, and canonicalization:    

 1. Deduplication (eliminating duplicate &mdash; exact &mdash; copies of repeated data)    
 2. Record linkage (identifying records that reference the same entity across different sources)    
 3. Canonicalization (converting data with more than one possible representation into a standard form)    

Entity resolution is not a new problem, but thanks to Python and new machine learning libraries, entity resolution is an increasingly achievable objective. This post will explore some basic approaches to entity resolution using one of those tools &mdash; the Python `dedupe` library.


## About Dedupe
[Dedupe](https://pypi.python.org/pypi/dedupe/1.4.3) is a library that uses machine learning to perform deduplication and entity resolution quickly on structured data. It isn't the only tool available in Python for doing entity resolution tasks, but it is the only one (as far as we know) that conceives of entity resolution as it's primary task. In addition to removing duplicate entries from within a single dataset, Dedupe can also do record linkage across disparate datasets. Dedupe also scales fairly well &mdash; in this post we demonstrate using the library with a smallish dataset of a few thousand records and a very large dataset of several million.

### How Dedupe works    
Effective deduplication relies largely on domain expertise. This is for two main reasons: firstly because domain experts through their experiences develop a set of heuristics that enable them to conceptualize what a canonical version of a record _should_ look like, even if they've never seen it in practice. Secondly, domain experts instinctively recognize which record subfields are most likely to uniquely identify a record; they just know where to look. As such, Dedupe works by engaging the user in labeling the data via a command line interface, and using machine learning on the resulting training data to predict similar or matching records within unseen data.    

### Blocking, affine gap distance, and active learning    
Let's imagine that our dataset is a list of people represented by attributes like names, addresses, personal characteristics and preferences.

__PLACEHOLDER IMAGE - INSERT BUSINESS CASE EXAMPLE HERE__    
![Imaginary people data for deduplication](figures/people_data.png)

Our goal, then, is to deduplicate the list to ensure that only one record exists for each person. Features like names, phone numbers, and zipcodes are probably going to be more useful than state, age, or favorite food. When comparing records, rather than treating each record as a single long string, Dedupe cleverly exploits the structure of the input data to instead compare the records _field by field_. The advantage of this approach is more pronounced when certain feature vectors of records are much more likely to assist in identifying matches than are other attributes. Dedupe lets the user nominate the features they believe will be most useful:   

```python
fields = [
    {'field' : 'Firstname', 'type': 'String'},
    {'field' : 'Lastname', 'type': 'String'},
    {'field' : 'Zip', 'type': 'Exact', 'has missing' : True},
    {'field' : 'Phone', 'type': 'String', 'has missing' : True},
    ]
```    

Dedupe scans the data to create tuples of records that it will propose to the user to label as being either matches, not matches, or possible matches. These `uncertainPairs` are identified using a combination of __blocking__ , __affine gap distance__ and __active learning__.

Blocking is used to reduce the number of overall record comparisons that need to be made. Dedupe's method of blocking involves engineering subsets of feature vectors (these are called 'predicates') that can be compared across records. In the case of our people dataset above, the predicates might be things like:     
  - the first three digits of the phone number    
  - the full name    
  - the first five characters of the name    
  - a random 4-gram within the city name     

__diagram to visualize blocking and predicates__

Records are then grouped ('blocked') by matching predicates, so that only records with matching predicates will be compared to each other during the active learning phase. The blocks are developed by computing the edit distance between predicates across records. Dedupe uses a distance metric called affine gap distance, which is a variation on Hamming distance that makes subsequent consecutive deletions or insertions cheaper.

__diagram to explain affine gap distance__    


The relative weight of these different feature vectors can be learned during the active learning process and expressed numerically to ensure that features that will be most predictive of matches will be 'heavier' in the overall matching schema. As the user labels more and more tuples, Dedupe gradually relearns the weights, recalculates the edit distances between records, and updates its list of the most uncertain pairs to propose to the user for labeling.

Once the user has generated enough labels, the learned weights are used to calculate the probability that each pair of records within a block is a duplicate or not.  In order to scale the pairwise matching up to larger tuples of matched records (in the case that entities may appear more than twice within a document), Dedupe uses hierarchical clustering with centroidal linkage. Records within some threshold distance of a centroid will be grouped together. The final result is an annotated version of the original dataset that now includes a centroid label for each record.    

## Testing out `dedupe`
Getting started with Dedupe is easy, and the developers have provided a [convenient repo](https://github.com/datamade/dedupe-examples) with examples that you can use and iterate on. Let's start by walking through the csv_example.py from the `dedupe-examples`. To get `dedupe` running, we'll need to install Unidecode, Future, and Dedupe.    

In your terminal (we recommend doing so inside a [virtual environment](https://districtdatalabs.silvrback.com/how-to-develop-quality-python-code)):    

```bash
git clone https://github.com/DistrictDataLabs/dedupe-examples.git
cd dedupe-examples

pip install unidecode
pip install future
pip install dedupe
```

Then we'll run the csv_example.py file to see what dedupe can do:    

```bash
python csv_example.py
```

## Active learning

You can see that `dedupe` is a command line application that will prompt the user to engage in active learning by showing pairs of entities and asking if they are the same or different.


```bash
Do these records refer to the same thing?
(y)es / (n)o / (u)nsure / (f)inished
```

Active learning is the so-called 'special sauce' behind Dedupe. As in most supervised machine learning tasks, the challenge is to get labelled data that the model can learn from. The active learning phase in Dedupe is essentially an extended user-labelling session, which can be short if you have a small dataset, and can take longer if your dataset is big. You are presented with 4 options;

![Dedupe snapshot](figures/dedupeEX.png)

You can experiment with typing the 'y', 'n' and 'u' keys to flag duplicates for active learning. When you are finished, enter 'f' to quit.

 - (y)es:    confirms that the two references are to the same entity    
 - (n)o:     labels the two references as not the same entity    
 - (u)nsure: does not label the two references as the same entity or as different entities      
 - (f)inished: ends the active learning session and triggers the supervised learning phase    


![Dedupe snapshot](figures/dedupeEX2.png)

As you can see in the example above, some comparisons are very easy to decide. The first contains zero for zero hits on all four attributes being examined, so the verdict is most certainly a non-match. On the second, we have a 3/4 exact match, with the fourth being fuzzy in that one entity contains a piece of the matched entity; Ryerson vs Chicago Public Schools Ryerson. A human would be able to to discern these as two references to the same entity, and we can label it as such to enable the supervised learning that comes after the active learning.

The csv_example also includes an [evaluation script](https://github.com/datamade/dedupe-examples/blob/master/csv_example/csv_evaluation.py) that will enable you to determine how successfully you were able to resolve the entities. It's important to note that the blocking, active learning and supervised learning portions of the deduplicaton process are very dependent on the dataset attributes that the user nominates for selection. In the csv_example, the script nominates the following four attributes:

```python
fields = [
    {'field' : 'Site name', 'type': 'String'},
    {'field' : 'Address', 'type': 'String'},
    {'field' : 'Zip', 'type': 'Exact', 'has missing' : True},
    {'field' : 'Phone', 'type': 'String', 'has missing' : True},
    ]
```

A different combination of attributes would result in a different blocking, a different set of uncertainPairs, a different set of features to use in the active learning phase, and almost certainly a different result. In other words, user experience and domain knowledge factor in heavily at multiple phases of the deduplication process.

## Something a bit harder
In order to try out Dedupe with a more challenging project, we decided to try out deduplicating the White House visitors' log. Our hypothesis was that it would be interesting to be able to answer questions such as "How many times has person X visited the White House during administration Y?" However, in order to do that, it would be necessary to generate a version of the list that was unique on entity. We guessed that there would be many cases where there were multiple references to a single entity, potentially with slight variations in how they appeared in the dataset. We also expected to find a lot of names that seemed similar but in fact referenced different entities.  In other words, a good challenge!

The data set we used was pulled from the [WhiteHouse.gov](https://open.whitehouse.gov/dataset/White-House-Visitor-Records-Requests/p86s-ychb) website, a part of the executive initiative to make federal data more open to the public. This particular set of data is a list of White House visitor record requests from 2006-2010. Here's a snapshot of what the data looks like via the White House API.  
![Data snapshot](figures/visitors.png)

The dataset includes a lot of columns, and for most of the entries, the majority of these fields are blank:

 - NAMELAST  (Last name of entity)    
 - NAMEFIRST (First name of entity)    
 - NAMEMID (Middle name of entity)    
 - UIN (Unique Identification Number)    
 - BDGNBR (Badge Number)    
 - Type of Access (Access type to White House)
 - TOA  (Time of Arrival)  
 - POA    
 - TOD
 - POD
 - APPT_MADE_DATE (When the appointment date was made)
 - APPT_START_DATE (When the appointment date is scheduled to start)
 - APPT_END_DATE (When the appointment date is scheduled to end)
 - APPT_CANCEL_DATE (When the appointment date was canceled)
 - Total_People (Total number of people scheduled to attend)
 - LAST_UPDATEDBY (Who was the last person to update this event)
 - POST	(?)
 - LastEntryDate (When the last update to this instance)
 - TERMINAL_SUFFIX (where was 0)
 - visitee_namelast (The visitee's last name)
 - visitee_namefirst (The visitee's first name)
 - MEETING_LOC (The location of the meeting)
 - MEETING_ROOM	(The room number of the meeting)
 - CALLER_NAME_LAST (?)
 - CALLER_NAME_FIRST	(?)
 - CALLER_ROOM (?)
 - Description (Description of the event or visit)
 - RELEASE_DATE (The date this set of logs were released to the public)


### Loading the data
Using the API, the White House Visitor Log Requests can be exported in a variety of formats to include, .json, .csv, and .xlsx, .pdf, .xlm, and RSS. However, it's important to keep in mind that the dataset contains over 5 million rows. For this reason, we decided to use .csv and grabbed the data using `requests`:

```python
import requests

def getData(url,fname):
    """
    Download the dataset from the webpage.
    """
    response = requests.get(url)
    with open(fname, 'w') as f:
        f.write(response.content)

DATAURL = "https://open.whitehouse.gov/api/views/p86s-ychb/rows.csv?accessType=DOWNLOAD"
ORIGFILE = "fixtures/whitehouse-visitors.csv"

getData(DATAURL,ORIGFILE)
```

Once downloaded, we can clean it up and load it into a database for more secure and stable storage.

## Tailoring the code
Next we'll discuss what is needed to tailor a `dedupe` example to get the code to work for the White House visitors log dataset. The main challenge with this dataset is it's sheer size. First we'll need to import a few modules and connect to our database:    

```python
import csv
import psycopg2
from dateutil import parser
from datetime import datetime

conn = None

DATABASE = your_db_name
USER = your_user_name
HOST = your_hostname
PASSWORD = your_password

try:
    conn = psycopg2.connect(database=DATABASE, user=USER, host=HOST, password=PASSWORD)
    print "I've connected"
except:
    print "I am unable to connect to the database"
cur = conn.cursor()
```

The other challenge with our dataset are the numerous missing values and datetime formatting irregularities. We wanted to be able to use the datetime strings to help with entity resolution, so we wanted to get the formatting to be as consistent as possible. The following script handles both the datetime parsing and the missing values by combining Python's `dateutil` module and PostgreSQL's fairly forgiving 'varchar' type.

This function takes the csv data in as input, parses the datetime fields we're interested in ('lastname','firstname','uin','apptmade','apptstart','apptend', 'meeting_loc'.), and outputs a database table that retains the desired columns (keep in mind this will take a while to run).        

```python
def dateParseSQL(nfile):
    cur.execute('''CREATE TABLE IF NOT EXISTS visitors_er
                  (visitor_id SERIAL PRIMARY KEY,
                  lastname    varchar,
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
                        row[field] = dt.toordinal()  # We also tried dt.isoformat()
                    except:
                        continue
            sql = "INSERT INTO visitors_er(lastname,firstname,uin,apptmade,apptstart,apptend,meeting_loc) \
                   VALUES (%s,%s,%s,%s,%s,%s,%s)"
            cur.execute(sql, (row[0],row[1],row[3],row[10],row[11],row[12],row[21],))
            conn.commit()
    print "All done!"


dateParseSQL(ORIGFILE)
```

About 60 of our rows had ASCII characters, which we dropped using this SQL command:

```sql
delete from visitors where firstname ~ '[^[:ascii:]]' OR lastname ~ '[^[:ascii:]]';
```

For our deduplication script, we modified the [PostgreSQL example](https://github.com/datamade/dedupe-examples/blob/master/pgsql_example/pgsql_example.py) as well as [Dan Chud](https://twitter.com/dchud)'s [adaptation of the script](https://github.com/dchud/osha-dedupe/blob/master/pgdedupe.py) for the OSHA dataset.


```python
import tempfile
import argparse
import csv
import os

import dedupe
import psycopg2
from psycopg2.extras import DictCursor
```


Initially we wanted to try to use the datetime fields to deduplicate the entities, but `dedupe` was not a big fan of the datetime fields, whether in isoformat or ordinal, so we ended up nominating the following fields:    

```python
KEY_FIELD = 'visitor_id'
SOURCE_TABLE = 'visitors'

FIELDS =  [{'field': 'firstname', 'variable name': 'firstname',
               'type': 'String','has missing': True},
              {'field': 'lastname', 'variable name': 'lastname',
               'type': 'String','has missing': True},
              {'field': 'uin', 'variable name': 'uin',
               'type': 'String','has missing': True},
              {'field': 'meeting_loc', 'variable name': 'meeting_loc',
               'type': 'String','has missing': True}
              ]
```

We modified a function Dan wrote to generate the predicate blocks:    

```python
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
```

And we adapted the method from the dedupe-examples repo to handle the active learning, supervised learning, and clustering steps:    

```python
def findDupes(args):
    deduper = dedupe.Dedupe(FIELDS)

    with psycopg2.connect(database=args.dbname,
                          host='localhost',
                          cursor_factory=DictCursor) as con:
        with con.cursor() as c:
            c.execute('SELECT COUNT(*) AS count FROM %s' % SOURCE_TABLE)
            row = c.fetchone()
            count = row['count']
            sample_size = int(count * args.sample)

            print 'Generating sample of %s records' % sample_size
            with con.cursor('deduper') as c_deduper:
                c_deduper.execute('SELECT visitor_id,lastname,firstname,uin,meeting_loc FROM %s' % SOURCE_TABLE)
                temp_d = dict((i, row) for i, row in enumerate(c_deduper))
                deduper.sample(temp_d, sample_size)
                del(temp_d)

            if os.path.exists(args.training):
                print 'Loading training file from %s' % args.training
                with open(args.training) as tf:
                    deduper.readTraining(tf)

            print 'Starting active learning'
            dedupe.convenience.consoleLabel(deduper)

            print 'Starting training'
            deduper.train(ppc=0.001, uncovered_dupes=5)

            print 'Saving new training file to %s' % args.training
            with open(args.training, 'w') as training_file:
                deduper.writeTraining(training_file)

            deduper.cleanupTraining()

            print 'Creating blocking_mapp table'
            c.execute("""
                DROP TABLE IF EXISTS blocking_mapp
                """)
            c.execute("""
                CREATE TABLE blocking_mapp
                (block_key VARCHAR(200), %s INTEGER)
                """ % KEY_FIELD)

            for field in deduper.blocker.index_fields:
                print 'Selecting distinct values for "%s"' % field
                c_index = con.cursor('index')
                c_index.execute("""
                    SELECT DISTINCT %s FROM %s
                    """ % (field, SOURCE_TABLE))
                field_data = (row[field] for row in c_index)
                deduper.blocker.index(field_data, field)
                c_index.close()

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

    findDupes(args)
```

## Active learning observations

We observed a lot of uncertainty during the active learning phase, mostly because of how enormous the dataset is.  This was particularly pronounced with names that seemed more common to us and that sounded more domestic, since those are much more commonly occurring in this dataset (is "Michael Grant" == "Michael Grant"?). We noticed that there were a lot of variations in the way that middle names were captured; sometimes they were concatonated with the first name, other times with the last name. We also observed what seemed to be many nicknames, or that could have been references to separate entities: "KIM ASKEW" and "KIMBERLEY ASKEW" vs. "Kathy Edwards" and "Katherine Edwards" (and yes, `dedupe` does preserve variations in case). On the other hand, since nicknames generally appear only in people's first names, when we did see a short version of a first name paired with an unusual or rare last name, we were more confident in labelling those as a match. Other things that made the labelling easier were clearly gendered names (e.g. "Brian Murphy" vs. "Briana Murphy"), which helped us to identify separate entities in spite of very small differences in the strings. Some names appeared to be clear misspellings, which also made us more confident in our labelling two references as matches for a single entity  ("Davifd Culp" vs. "David Culp"). There were also a few potential "easter eggs" in the dataset, which we suspect might actually be aliases ("Jon Doe" and "Ben Jealous").

One of the things we discovered upon multiple runs of the active learning process is that the number of fields that the user nominates to Dedupe for use have a great impact on the kinds of predicate blocks that are generated during the initial blocking phase, and thus the comparisons that are presented to the trainer during the active learning phase. In one of our runs, we used only the last name, first name, and meeting location fields. Some of the comparisons were easy:      

```bash
lastname : KUZIEMKO
firstname : ILYANA
meeting_loc : WH

lastname : KUZIEMKO
firstname : ILYANA
meeting_loc : WH

Do these records refer to the same thing?
(y)es / (n)o / (u)nsure / (f)inished
```

Some were hard:    
```bash
lastname : Desimone
firstname : Daniel
meeting_loc : OEOB

lastname : DeSimone
firstname : Daniel
meeting_loc : WH

Do these records refer to the same thing?
(y)es / (n)o / (u)nsure / (f)inished
```

## Results

What we realized from this is that there are actually two different kinds of duplicates that appear in our dataset. The first kind of duplicate is one that generated via (likely mistaken) duplicate visitor request forms. We noticed that these duplicated tended to be proximal to each other in terms of visitor_id number, have the same meeting location and the same 'uin' (which confusingly, is not a unique guest identifier but appears to be assigned to every visitor within a unique tour group). The second kind of duplicate is what we think of as the 'frequent flier' &mdash; people who seem to spend a lot of time at the White House like staffers and other political appointees.

### Within visit duplicates


### Across visit duplicates ('frequent fliers')
- what do the results look like after active learning & how to interpret them    
- how many duplicates were identified? (give examples)    
- any errors? (and how could we make changes to prevent those kinds of errors?)    


## Conclusion
Look forward to several upcoming blogs on string matching algorithms, data preparation, and entity identification...



## Recommended Reading
- [A Primer on Entity Resolution by Benjamin Bengfort](http://www.slideshare.net/BenjaminBengfort/a-primer-on-entity-resolution)  
- [Entity Resolution for Big Data: A Summary of the KDD 2013 Tutorial Taught by Dr. Lise Getoor and Dr. Ashwin Machanavajjhala](http://www.datacommunitydc.org/blog/2013/08/entity-resolution-for-big-data)    
- [A Theory for Record Linkage by Ivan P. Fellegi and Alan B. Sunter](http://courses.cs.washington.edu/courses/cse590q/04au/papers/Felligi69.pdf)   
- etc.
