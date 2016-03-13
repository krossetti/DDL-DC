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
- go over some of the useful libraries    

## About `dedupe`
- what it is   
- how it works   
- how to install it   

## Testing out `dedupe`
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

## About the dataset
- where to get it: https://open.whitehouse.gov/dataset/White-House-Visitor-Records-Requests/p86s-ychb    

![Data snapshot](https://open.whitehouse.gov/dataset/White-House-Visitor-Records-Requests/p86s-ychb)

- how to load it into Python    
- what the features are    
- how to get the data into shape for analysis    

## Tailoring the code
- what you need to modify in the `dedupe` examples to get the code to work for the WH dataset    

## Active learning
- screen shot of active learning process in command line    
- discuss what is going on under the hood    
- mention how this could be made even better?   

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
