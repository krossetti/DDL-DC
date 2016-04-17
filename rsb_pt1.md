## Tools for entity resolution in Python
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
Dedupe is a Python library that employs machine learning techniques to perform deduplication and entity resolution  on structured data. In addition to removing duplicate entries from within a single dataset, Dedupe can also do record linkage across disparate datasets. __discuss scaling__

### How Dedupe works    
Effective deduplication relies largely on domain expertise. This is for two main reasons: firstly because domain experts through their experiences develop a set of heuristics that enable them to conceptualize what a canonical version of a record _should_ look like, even if they've never seen it in practice. Secondly, domain experts instinctively recognize which record subfields are most likely to uniquely identify a record; they know where to look. As such, Dedupe works by engaging the user in labeling the data via a command line interface, and using the resulting training data to develop a ruleset to identify similar or matching records within unseen data.    

When comparing records, rather than treating each record as a single long string, Dedupe cleverly exploits the structure of the input data to instead compare the records _field by field_. Dedupe scans the data to create tuples of records that it will propose to the user to label as being either matches, not matches, or possible matches. These `uncertainPairs` are identified using a combination of __blocking__ , __affine gap distance__ and __active learning__.  

### Blocking, affine gap distance, and active learning    
Blocking is a method for reducing the number of overall record comparisons that need to be made. Dedupe's method of blocking involves engineering subsets of feature vectors (these are called 'predicates') that can be compared across records. Records are then grouped ('blocked') by matching predicates, so that only records with matching predicates will be compared to each other. The blocks are developed by computing the edit distance between predicates across records. Dedupe using a distance metric called affine gap distance, is a variation on Hamming distance that makes subsequent consecutive deletions or insertions cheaper.

The advantages of these approaches are more pronounced when certain feature vectors of records are much more likely to assist in identifying matches than are other attributes. For example, let's imagine that our dataset is a list of people represented by attributes like names, addresses, personal characteristics and preferences.

![Imaginary people data for deduplication](figures/people_data.png)

Our goal then is to deduplicate the list to ensure that only one record exists for each person. Features like names, phone numbers, and zipcodes are probably going to be more useful than state, age, or favorite food. Dedupe lets the user nominate the features they believe will be most useful:   

```python
fields = [
    {'field' : 'Firstname', 'type': 'String'},
    {'field' : 'Lastname', 'type': 'String'},
    {'field' : 'Zip', 'type': 'Exact', 'has missing' : True},
    {'field' : 'Phone', 'type': 'String', 'has missing' : True},
    ]
```    

The relative weight of these different feature vectors can be learned during the active learning process and expressed numerically to ensure that features that will be most predictive of matches will be 'heavier' in the overall matching schema. As the user labels more and more tuples, Dedupe gradually relearns the weights, recalculates the edit distances between records, and updates its list of the most uncertain pairs to propose to the user for labeling.
