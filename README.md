# DDL-DC
Entity Resolution for DDL


About:

The data that is being used for this entity resolution project is from the White House Vistitor logs. 
        https://open.whitehouse.gov/dataset/White-House-Visitor-Records-Requests/p86s-ychb



Project Overview:

To use dedupe in the classic sense of multi-name instance resolution. We will figure out which are the best attributes for the training data for the dedupe tool to be maximally effective with the smallest err rate. 

Attributes:

These are the 4 attributes chosen for the dedupe training set:
        1) NAMELAST
        2) NAMEFIRST
        3) APPT_START_TIME
        4) MEETING_LOC
