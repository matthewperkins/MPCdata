import xlsxwriter
import numpy as np
import pandas as pd
import re
import os
import datetime
import itertools
    
class MPCData(object):
    def __init__(self):
        self.StartDate = None
        self.EndDate = None
        self.Subject = None
        self.Experiment = None
        self.Group = None
        self.Box = None
        self.StartTime = None
        self.EndTime = None
        self.MSN = None
        self.StartDateTime = None
        self.ScalarVars = {}
        self.ArrayVars = {}

# pull out lick times 
rx_dict = {
    'StartDate': re.compile(r'^Start Date: (?P<StartDate>.*)\n'),
    'EndDate': re.compile(r'^End Date: (?P<EndDate>.*)\n'),
    'StartTime': re.compile(r'^Start Time: (?P<StartTime>.*)\n'),
    'EndTime': re.compile(r'^End Time: (?P<EndTime>.*)\n'),
    'Subject': re.compile(r'^Subject: (?P<Subject>.*)\n'),
    'Experiment': re.compile(r'^Experiment: (?P<Experiment>.*)\n'),
    'Group': re.compile(r'^Group: (?P<Group>.*)\n'),
    'Box': re.compile(r'^Box: (?P<Box>.*)\n'),
    'MSN': re.compile(r'^MSN: (?P<MSN>.*)\n'),
    'SCALAR': re.compile(r'(?P<name>[A-Z]{1}): *(?P<value>\d+\.\d*)\n'),
    'ARRAY': re.compile(r'(?P<name>[A-Z]{1}):\n'),
    'ARRAYidx': re.compile(r'^ *(?P<index>[0-9]*):(?P<list>.*)\n')
    }
    
def _parse_line(line):
    """
    Do a regex search against all defined regexes and
    return the key and match result of the first matching regex

    """

    for key, rx in rx_dict.items():
        match = rx.search(line)
        if match:
            return key, match
    # if there are no matches
    return None, None

def parse_MPC(filepath):
    """
    Parse text at given filepath

    Parameters
    ----------
    filepath : str
        Filepath for file_object to be parsed

    Returns
    -------
    data : MPCData Object
        Parsed data

    """

    data = MPCData()  # create an empty list to collect the data
    MPCDateStringRe = re.compile(r'\s*(?P<hour>[0-9]+):(?P<minute>[0-9]{2}):(?P<second>[0-9]{2})')
    # open the file and read through it line by line
    with open(filepath, 'r') as file_object:
        line = file_object.readline()
        while line:
            # at each line check for a match with a regex
            key, match = _parse_line(line)

            # extract start date
            if key == 'StartDate':
                data.StartDate = datetime.datetime.strptime(match.group(key), 
                                                            "%m/%d/%y").date()
            # extract end date
            if key == 'EndDate':
                data.EndDate = datetime.datetime.strptime(match.group(key), 
                                                            "%m/%d/%y").date()
            # extract start time
            if key == 'StartTime':
                (h,m,s) = [int(MPCDateStringRe.search(match.group(key)).group(g)) for g in ['hour',
                                                                                            'minute',
                                                                                            'second']]
                data.StartTime = datetime.time(h,m,s)
            # extract end time
            if key == 'EndTime':
                (h,m,s) = [int(MPCDateStringRe.search(match.group(key)).group(g)) for g in ['hour',
                                                                                            'minute',
                                                                                            'second']]
                data.EndTime = datetime.time(h,m,s)   
            # extract Subject
            if key == 'Subject':
                data.Subject = match.group(key)   
            
            # extract Experiment
            if key == 'Experiment':
                data.Experiment = match.group(key)   
            
            # extract Group
            if key == 'Group':
                data.Group = match.group(key)   
                
            # extract Box
            if key == 'Box':
                data.Box = match.group(key)   
            
            # extract MSN
            if key == 'MSN':
                data.MSN = match.group(key)   
            
            # extract scalars
            if key == 'SCALAR':
                data.ScalarVars[match.group('name')] = float(match.group('value'))   
            
            # identify an array
            if key == 'ARRAY':
                #print('This is the beginning of an Array, ', line)
                # have now have to step through the array
                # just pre-index a big array
                tmp_array = np.zeros((1000000,))
                subline = file_object.readline()
                #print("THis is the first line of the array, ", subline)
                while subline:
                    m = rx_dict['ARRAYidx'].search(subline)
                    if (m):
                        idx = int(float(m.group('index')))
                        items = np.array([float(l) for l in m.group('list').split()])
                        tmp_array[idx:idx+len(items)] = items
                    else:
                        # have to rewind
                        #print("This is one line beyond the last line of the array", subline)
                        file_object.seek(file_tell)
                        break
                    file_tell = file_object.tell()
                    subline = file_object.readline()
                data.ArrayVars[match.group('name')] = tmp_array[0:idx+len(items)] 
            line = file_object.readline()
        
        data.StartDateTime = datetime.datetime.combine(data.StartDate, data.StartTime)

        # create a pandas DataFrame from the list of dicts
        #data = pd.DataFrame(data)
        # set the School, Grade, and Student number as the index
        #data.set_index(['School', 'Grade', 'Student number'], inplace=True)
        # consolidate df to remove nans
        #data = data.groupby(level=data.index.names).first()
        # upgrade Score from float to integer
        #data = data.apply(pd.to_numeric, errors='ignore')
    return data

def MPC_to_xlsx(MPC_file_path):
    fname = MPC_file_path
    data = parse_MPC(fname)
    FNre = re.compile(r'(?P<FN>^.*)MPCIV.txt$')
    m = FNre.search(fname)
    if (m):
        FN = m.group('FN')
    else:
        FN = fname

    # Create a workbook and add a headersheet.
    workbook = xlsxwriter.Workbook("%s.xlsx" % FN)
    headersheet = workbook.add_worksheet('Header')

    row = 0
    col = 0
    headersheet.write(row, col, "Start Date")
    headersheet.write(row, col+1, data.StartDate.strftime("%m/%d/%Y"))

    row+=1
    headersheet.write(row, col, "End Date")
    headersheet.write(row, col+1, data.EndDate.strftime("%m/%d/%Y"))

    row+=1
    headersheet.write(row, col, "Start Time")
    headersheet.write(row, col+1, data.StartTime.strftime("%H:%M:%S"))

    row+=1
    headersheet.write(row, col, "End Time")
    headersheet.write(row, col+1, data.EndTime.strftime("%H:%M:%S"))

    for k in ['Subject', 'Experiment', 'Group', 'Box', 'MSN']:
        headersheet.write(row,col,k)
        headersheet.write(row,col+1,getattr(data, k))
        row+=1

    scalarsheet = workbook.add_worksheet('ScalarVariables')
    row = 0
    for k,v in data.ScalarVars.items():
        scalarsheet.write(row,col,k)
        scalarsheet.write(row,col+1,v)
        row+=1

    arraysheet = workbook.add_worksheet('ArrayVariables')
    row = 0
    col = 0

    for k,v in data.ArrayVars.items():
        arraysheet.write(row,col,k)
        # naive appoarch, don't use numpy functions
        for (i,num) in enumerate(v):
            arraysheet.write(i+1,col,num)
        col+=1

    workbook.close()

