import xlsxwriter
import numpy as np
import pandas as pd
import re
import os
import datetime
    
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

    def to_xlsx(self,out_path):
        # Create a workbook and add a headersheet.
        workbook = xlsxwriter.Workbook(out_path)
        headersheet = workbook.add_worksheet('Header')

        row = 0
        col = 0
        headersheet.write(row, col, "Start Date")
        headersheet.write(row, col+1, self.StartDate.strftime("%m/%d/%Y"))

        row+=1
        headersheet.write(row, col, "End Date")
        headersheet.write(row, col+1, self.EndDate.strftime("%m/%d/%Y"))

        row+=1
        headersheet.write(row, col, "Start Time")
        headersheet.write(row, col+1, self.StartTime.strftime("%H:%M:%S"))

        row+=1
        headersheet.write(row, col, "End Time")
        headersheet.write(row, col+1, self.EndTime.strftime("%H:%M:%S"))

        for k in ['Subject', 'Experiment', 'Group', 'Box', 'MSN']:
            headersheet.write(row,col,k)
            headersheet.write(row,col+1,getattr(self, k))
            row+=1

        scalarsheet = workbook.add_worksheet('ScalarVariables')
        row = 0
        for k,v in self.ScalarVars.items():
            scalarsheet.write(row,col,k)
            scalarsheet.write(row,col+1,v)
            row+=1

        arraysheet = workbook.add_worksheet('ArrayVariables')
        row = 0
        col = 0

        for k,v in self.ArrayVars.items():
            arraysheet.write(row,col,k)
            # naive appoarch, don't use numpy functions
            for (i,num) in enumerate(v):
                arraysheet.write(i+1,col,num)
            col+=1

        workbook.close()

      
# pull out lick times 
rx_dict = {
    'StartDate': re.compile(r'^Start Date: (?P<StartDate>.*)\r\n'),
    'EndDate': re.compile(r'^End Date: (?P<EndDate>.*)\r\n'),
    'StartTime': re.compile(r'^Start Time: (?P<StartTime>.*)\r\n'),
    'EndTime': re.compile(r'^End Time: (?P<EndTime>.*)\r\n'),
    'Subject': re.compile(r'^Subject: (?P<Subject>.*)\r\n'),
    'Experiment': re.compile(r'^Experiment: (?P<Experiment>.*)\r\n'),
    'Group': re.compile(r'^Group: (?P<Group>.*)\r\n'),
    'Box': re.compile(r'^Box: (?P<Box>.*)\r\n'),
    'MSN': re.compile(r'^MSN: (?P<MSN>.*)\r\n'),
    'SCALAR': re.compile(r'(?P<name>[A-Z]{1}): *(?P<value>\d+\.\d*)\r\n'),
    'ARRAY': re.compile(r'(?P<name>[A-Z]{1}):\r\n'),
    'ARRAYidx': re.compile(r'^ *(?P<index>[0-9]*):(?P<list>.*)\r\n'),
    'STARTOFDATA': re.compile(r'\r\r\n')
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
    Need to set this up to parse multiple boxes in one file?
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

    MPCDateStringRe = re.compile(r'\s*(?P<hour>[0-9]+):(?P<minute>[0-9]{2}):(?P<second>[0-9]{2})')
    # open the file and read through it line by line
    with open(filepath, 'r', newline = '\n') as file_object:
        # if the file has multiple boxes in it, return a list of MPC objects
        MPCDataList = []
        line = file_object.readline()
        while line:
            # at each line check for a match with a regex
            key, match = _parse_line(line)

            # start of data is '\r\r\n'
            if key=='STARTOFDATA':
                data = MPCData()  # create a new data object
                MPCDataList.append(data)
    
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
                # date should be already read
                data.StartDateTime = datetime.datetime.combine(data.StartDate, data.StartTime)

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
                data.Box = int(match.group(key))
            
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
    return MPCDataList
