# DDL-DC
Entity Resolution for DDL


#About:

The data that is being used for this entity resolution project is from the White House Visitor logs.
        https://open.whitehouse.gov/dataset/White-House-Visitor-Records-Requests/p86s-ychb



#Project Overview:

To use `dedupe` in the classic sense of multi-name instance resolution. We will figure out which are the best attributes for the training data for the `dedupe` tool to be maximally effective with the smallest err rate.

#Attributes:

These are the 5 attributes chosen for the `dedupe` training set:

        1) NAMELAST    

        2) NAMEFIRST    

        3) APPT_START_TIME    

        4) MEETING_LOC    

        5) APPT_MADE_DATE    

Other fields to consider for experimentation:    
 - __uin__?    
 - __apptmade__?    
 - __apptend__?    
 - __visitee_namelast__?    
 - __description__?    


Trying to solve 2 different problems:
- Resolving duplication errors _within_ an event.    
- Record linkage _across_ events.
