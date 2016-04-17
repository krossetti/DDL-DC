# Basics of Entity Resolution with Python and Dedupe
_by Kyle Rossetti and Rebecca Bilbro_

## Introduction    
### What is entity resolution?    
Entity resolution is the task of disambiguating records that correspond to real world entities across and within datasets. The applications of entity resolution are tremendous, particularly for public sector and federal datasets related to health, transportation, finance, law enforcement, and antiterrorism.  

Unfortunately, the problems associated with entity resolution are equally tremendous -- as the volume and velocity of data grow, inference across networks and semantic relationships between entities becomes more and more difficult. Data quality issues, schema variations, and idiosyncratic data collection traditions can all complicate these problems even further. When combined, such challenges amount to a substantial barrier to organizations’ ability to fully understand their data, let alone make effective use of predictive analytics to optimize targeting, thresholding, and resource management.  

The three primary tasks involved in entity resolution are deduplication, record linkage, and canonicalization:    
1. Deduplication    
2. Record linkage    
3. Canonicalization    

This post will explore some basic approaches to entity resolution using the Python `dedupe` library.

## Tools for entity resolution in Python
Open source [projects](http://stats.stackexchange.com/questions/136755/popular-named-entity-resolution-software)    

Some of the useful libraries you can `pip install`:    

### String Matching
  1. [`gensim`](https://pypi.python.org/pypi/gensim/0.12.4) - a Python library for topic modeling, document indexing and similarity retrieval with large corpora.    
  2. [`dedupe`](https://pypi.python.org/pypi/dedupe/1.4.3) - Datamade's Python library that uses machine learning to perform deduplication and entity resolution quickly on structured data.     
  3. [`affinegap`](https://pypi.python.org/pypi/affinegap/1.9) - Datamade's Cython implementation of the affine gap string distance.   
  4. [`python-Levenshtein`](https://pypi.python.org/pypi/python-Levenshtein/0.12.0) - library for computing string edit distances and similarities.   
  5. [`fuzzywuzzy`](https://pypi.python.org/pypi/fuzzywuzzy/0.10.0) - a fuzzy matching implementation that uses Levenshtein Distance to help calculate differences between strings.    
  6. [`fuzzy`](https://pypi.python.org/pypi/Fuzzy/1.1) - a python library implementing common phonetic algorithms quickly.    
  7. [`editdistance`](https://pypi.python.org/pypi/editdistance) - a simple implementation of Levenshtein distance with C++ and Cython.    
  8. [`pyjarowinkler`](https://pypi.python.org/pypi/pyjarowinkler/1.7) - compute the similarity score between two strings using Jaro-Winkler distance.     

### More Distance Metrics
  1. [scipy](https://www.scipy.org/) - a Python-based ecosystem of open-source software for mathematics, science, and engineering. It includes a broad suite of [distance metrics](http://docs.scipy.org/doc/scipy/reference/spatial.distance.html) including Euclidean, Minkowski, Manhattan (taxi cab), Jaccard, and cosine distance.   
  2. [Or implement them yourself in pure Python](https://dataaspirant.com/2015/04/11/five-most-popular-similarity-measures-implementation-in-python/)

## About Dedupe
Dedupe is a Python library that employs machine learning techniques to perform deduplication and entity resolution  on structured data. In addition to removing duplicate entries from within a single dataset, Dedupe can also do record linkage across disparate datasets.

__discuss scaling__    

### How Dedupe works    
Effective deduplication relies largely on domain expertise. This is for two main reasons: firstly because domain experts through their experiences develop a set of heuristics that enable them to conceptualize what a canonical version of a record _should_ look like, even if they've never seen it in practice. Secondly, domain experts instinctively recognize which record subfields are most likely to uniquely identify a record; they just know where to look. As such, Dedupe works by engaging the user in labeling the data via a command line interface, and using machine learning on the resulting training data to predict similar or matching records within unseen data.    

### Blocking, affine gap distance, and active learning    
Let's imagine that our dataset is a list of people represented by attributes like names, addresses, personal characteristics and preferences.

__this is a placeholder image - we should make a better one to illustrate these concepts__    
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

Records are then grouped ('blocked') by matching predicates, so that only records with matching predicates will be compared to each other during the active learning phase. The blocks are developed by computing the edit distance between predicates across records. Dedupe uses a distance metric called affine gap distance, which is a variation on Hamming distance that makes subsequent consecutive deletions or insertions cheaper.

__diagram to explain affine gap distance__    

The relative weight of these different feature vectors can be learned during the active learning process and expressed numerically to ensure that features that will be most predictive of matches will be 'heavier' in the overall matching schema. As the user labels more and more tuples, Dedupe gradually relearns the weights, recalculates the edit distances between records, and updates its list of the most uncertain pairs to propose to the user for labeling.

Once the user has generated enough labels, the learned weights are used to calculate the probability that each pair of records within a block is a duplicate or not.  In order to scale the pairwise matching up to larger tuples of matched records (in the case that entities may appear more than twice within a document), Dedupe uses hierarchical clustering with centroidal linkage. Records within some threshold distance of a centroid will be grouped together. The final result is an annotated version of the original dataset that now includes a centroid label for each record.    

## Testing out `dedupe`
_Start by walking people through the csv_example.py from the `dedupe-examples` repo_

Let's experiment with using the `dedupe` library to try cleaning up our file. To get `dedupe` running, we'll need to install Unidecode, Future, and Dedupe.    

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

You can see that `dedupe` is a command line application that will prompt the user to engage in active learning by showing pairs of entities and asking if they are the same or different.

```bash
Do these records refer to the same thing?
(y)es / (n)o / (u)nsure / (f)inished
```

You can experiment with typing the 'y', 'n' and 'u' keys to flag duplicates for active learning. When you are finished, enter 'f' to quit.

## Active learning
- screen shot of active learning process in command line    
- discuss what is going on under the hood    
- mention how this could be made even better?   

## About the dataset
- where to get it:     
https://open.whitehouse.gov/dataset/White-House-Visitor-Records-Requests/p86s-ychb    
- what it looks like    
![Data snapshot](figures/visitors.png)
- how to load it into Python    
- what the features are    
- how to get the data into shape for analysis    

## Tailoring the code
_Move to using the PostgreSQL example from the `dedupe-examples` repo_
- what you need to modify in the `dedupe` examples to get the code to work for the WH dataset    

## Results
- what do the results look like after active learning & how to interpret them    
- how many duplicates were identified? (give examples)    
- any errors? (and how could we make changes to prevent those kinds of errors?)    

## Conclusion

## Recommended Reading
- [A Primer on Entity Resolution by Benjamin Bengfort](http://www.slideshare.net/BenjaminBengfort/a-primer-on-entity-resolution)  
- [Entity Resolution for Big Data: A Summary of the KDD 2013 Tutorial Taught by Dr. Lise Getoor and Dr. Ashwin Machanavajjhala](http://www.datacommunitydc.org/blog/2013/08/entity-resolution-for-big-data)    
- [A Theory for Record Linkage by Ivan P. Fellegi and Alan B. Sunter](http://courses.cs.washington.edu/courses/cse590q/04au/papers/Felligi69.pdf)   
- etc.
