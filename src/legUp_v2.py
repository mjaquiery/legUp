"""
Updated on Sun Feb 25 15:26 2018
- tkinter library used to enable file selection dialogues for loading data and saving output
- options now specified with a dialogue box rather than a command line
Created on Thu Feb 06 17:29:27 2015

This program takes csv files containing voltage readings
(20,000 of them per file) and removes the extraneous and noisy data leaving
just the key points - those denoting the peak and trough of each spike.

The output is written to a new file.

The output csv file has the following format:
File, mV minimum, mV maximum, Hz

It's been useful to me if not anyone else. 

Please note:
* The lowest range (default 0-50mV) of spike amplitudes is very, very noise-
prone. This means that the data, where it appears, should probably not be 
trusted. 

* This program has very little error handling and is liable to crash without 
explanation if given bad data (such as csv files containing certain data). For
the envisioned use cases it should be okay but no promises are made.

Feel free to use, modify, etc. this code as you see fit.

@author: mj261
"""

import csv, math, os, re, time
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog


""" 
    Function definitions. 
    
    The actual program gets more comments, promise.
    
"""


# writes a list to a file - UNUSED
def writeStuff(aList, anotherList, fileToWriteTo):
    i = 0
    limit = len(aList)
    with open(fileToWriteTo, 'wt', newline = '') as file:
        write = csv.writer(file)
        while i < limit:
            data = [str(aList[i]), str(anotherList[i])]
            write.writerow(data)
            i += 1
             
        file.close()
        return


# returns a list of non-'clean_' CSV files for inspection
def getCSVs(folderPath):
    returnlist = []
    i = 0
    print("Searching for .csv files in " + folderPath)
    for dirpath, dirnames, files in os.walk(folderPath):
        for file in files:
            if re.match('^(?!clean_).+\\.csv$', file): 
                returnlist.append(os.path.join(dirpath, file))
                i += 1                
    print("Found " + str(i) + " files.")
    return returnlist 


# returns two lists, "stimulus" and "response"
# stimulus is a list of points in the 2nd column
# response is a list of ponts in the 1st column
def getDataTuple(aFile):
    retList = []
    with open(aFile, 'rt', encoding='utf-8-sig') as csvfile:
        myfile = csv.reader(csvfile)
        
        for line in myfile:
            tup = float(line[1]), float(line[0])
            retList.append(tup)
            
    return retList


# Extracts the stimulus data
def getStimulusList(tupleList):
    stimulusList = []
    if hasattr(tupleList, '__iter__'):
        for tup in dataList:
            stimulusList.append(tup[0])
            
    return stimulusList


# Extracts the response data
def getResponseList(tupleList):
    responseList = []
    if hasattr(tupleList, '__iter__'):
        for tup in dataList:
            responseList.append(tup[1])
            
    return responseList


# returns the mean of a list of floats
def getMean(aList):
    mean = 0.0
    i = 0
    for value in aList:
        i += 1
        mean += value
        
    return (mean / i)


# takes a list and an average and returns a list with 0s where the first list's
# value is lower than or equal to average and 1s where higher
def getZeroList(aList, aMean):
    retList = []
    for value in aList:
        if value > aMean:
            retList.append(1.0)
        else:
            retList.append(0.0)
            
    return retList


# returns a list where each value has been multiplied by a corresponding value
# in another list
def flatten(aList, zeroList, replaceWith = 0.0):
    i = 0
    limit = len(aList)
    if limit != len(zeroList):
        return
    while i < limit:
        if zeroList[i] == 0.0:
            aList[i] = replaceWith
        else:
            aList[i] = aList[i]
        i += 1
        
    return aList     


# returns aList filled with values smoothed over the last num values
def smooth(aList, numValues = 5):
    stack = []
    outList = []
    for value in aList:
        if len(stack) >= numValues:
            stack.pop(numValues-1)
        stack.insert(0,value)
        outList.append(sum(stack)/len(stack))
        
    return outList


# returns the modal average of a list
def getMode(aList):
    values = {}
    for score in aList:
        if score not in values:
            values[score] = 1
        else:
            values[score] += 1
    
    mode = 0
    for score in values:
        if values[score] > mode:
            mode = score
            
    return mode


# splits a list along the mean, then assigns all values to the mean of their group
def split(aList):
    if len(aList) <= 0:
        return aList
    mean = sum(aList)/len(aList)
    low = []
    high = []
    for value in aList:
        if value > mean:
            high.append(value)
        elif value < mean:
            low.append(value)
            
    lowMode = getMode(low)
    highMode = getMode(high)
    
    i = 0
    limit = len(aList)
    while i < limit:
        if aList[i] > mean:
            aList[i] = highMode
        elif aList[i] < mean:
            aList[i] = lowMode
        i += 1
            
    return aList


# returns a list containing only the high and low points of spikes
def findExtremes(spikelist, average = 0.0):
    
    returnList = []
    i = 0
    pending = average, i
    lastval = average
   # i = 0
    mode = 0 # 1: expecting larger; -1: expecting smaller
    # loop through looking for extreme points
    for lineval in spikelist:
        lineval = float(lineval)
        # find the high point
        if mode == 1:
            if lineval > pending[0]:
                #print("Pending: " + str(lineval)) 
                pending = lineval, i
        # find the low point        
        elif mode == -1:
            if lineval < pending[0]:
                #print("Pending: " + str(lineval))  
                pending = lineval, i
        # work out whether to look for high or low values
        if mode == 0:
            if lineval > average:
                mode = 1
            if lineval < average:
                mode = -1
            pending = lineval, i
        # when crossing the origin switch modes
        elif math.copysign(1.0, (lineval - average)) != math.copysign(1.0, (lastval - average)):
            if pending[0] != average:    
                returnList[pending[1]] = pending[0]
                pending = lineval, i
                
            if mode == -1:
                mode = 1
                #print("Now looking for high point.")
            else:
                mode = -1
                #print("Now looking for low point.")
		
        returnList.append(average)
        lastval = lineval
        i += 1
    
    return returnList


class spike:
    startPoint = 0
    startValue = 0
    endValue = 0
    endPoint = 0
    stimulusLevel = 0
    number = 0
    timeSinceLastSpike = 0
    
    def getDuration(self):
        return (self.endPoint - self.startPoint)
       
    def getAmplitude(self):
        return (math.copysign(self.endValue, 1) + math.copysign(self.startValue, 1))


# finds pairs within a list which constitute spikes and returns a spike object
def getNextSpike(spikeList, listMean, searchFrom, lastSpikeTime, relativeSizeLimit = 0.5, maxDuration = 40):
    mySpike = spike()
    mySpike.startValue = listMean
    i = searchFrom
    limit = i + maxDuration
    defaultOut = False
    if limit > len(spikeList):
        limit = len(spikeList)
    else:
        defaultOut = limit
    while i < limit:
        value = spikeList[i]
        # first non-mean value is our peak
        if value != listMean:
            if mySpike.startValue == listMean:
                mySpike.startValue = value
                mySpike.startPoint = i
            # second non-mean value is our prospective match
            elif value < listMean < mySpike.startValue or value > listMean > mySpike.startValue:
                posval = math.copysign(value - listMean, 1)
                posstart = math.copysign(mySpike.startValue - listMean, 1)
                if posval > posstart * (1-relativeSizeLimit) and posval < posstart * (1+relativeSizeLimit):
                    mySpike.endPoint = i
                    mySpike.endValue = value
                    # calculate timeSinceLastSpike
                    timeSince = mySpike.startPoint - lastSpikeTime
                    if lastSpikeTime == 0:
                        timeSince = 0.0
                    mySpike.timeSinceLastSpike = timeSince
                    return mySpike
            # if it didn't made a spike we can stop
            else:
                return i
                
        i += 1
    
    # if we didn't find a 2nd non-mean point in the list then return False
    return defaultOut


# fills in the stimulus level and number variables for all spikes in aList
def fillValues(aList, stimList):
    i = 1
    for aSpike in aList:
        aSpike.stimulusLevel = stimList[aSpike.startPoint]
        aSpike.number = i
        i += 1


# Writes data in a nice csv format for analysis to output to a spreadsheet
def writeSpikeToCSV(aSpike, fromFile, outputFile):

    headersWritten = os.path.isfile(outputFile)
    
    with open(outputFile, 'at', newline = '') as file:
        write = csv.writer(file)
        # Write the headers
        if headersWritten == False:
            write.writerow(["File", "Spike #", "Stimulus", "Peak Point", "Amplitude", "Duration (ms)", "Time Since Last Spike"])
            
        rowToWrite = [fromFile, aSpike.number, aSpike.stimulusLevel, aSpike.startPoint+1,
                      aSpike.getAmplitude(), aSpike.getDuration()/2, aSpike.timeSinceLastSpike]
        write.writerow(rowToWrite)
             
    file.close()
    
    
# If the file already exists get a new name for the output file
def promptForFileName(folder, outputFileName):
    while os.path.isfile(os.path.join(folder, outputFileName)):
        print("Output file already exists (\"" + outputFileName + "\")")
        outputFileName = input("Please enter a new name for the output file: ")
        if outputFileName[-4:] != ".csv":
            outputFileName += ".csv"
        if outputFileName[:6] != "clean_":
            outputFileName = "clean_" + outputFileName
    
    return outputFileName


class MyDialog(simpledialog.Dialog):

    def body(self, master):
        self.answered = False
        self.title("legUp")
        simpledialog.Label(master, text="queries -> matt.jaquiery@psy.ox.ac.uk") \
            .grid(row=0, column=1, columnspan=2)
        intro = "Welcome to legUp.\n\n"
        intro += "This program extracts spikes from a series of voltage readings.\n\n"
        intro += "First, you may specify options in this pane. " \
                 "Blank options are replaced with the default (in parentheses).\n"
        intro += "Next, you will be prompted to open a file: select ALL files you want analysed.\n"
        intro += "After selecting input files, you will choose where to save the output.\n"
        intro += "Finally, once the program has completed, you will see a summary of its performance.\n"
        simpledialog.Message(master, text=intro, justify=simpledialog.LEFT, aspect=250) \
            .grid(row=1, columnspan=3)
        simpledialog.Label(master, text="Relative spike size:").grid(row=2, sticky=simpledialog.W)
        simpledialog.Label(master, text="(default = 0.5)").grid(row=2, column=2, sticky=simpledialog.W)
        simpledialog.Label(master, text="Minimum spike duration:").grid(row=3, sticky=simpledialog.W)
        simpledialog.Label(master, text="ms (default = 20)").grid(row=3, column=2, sticky=simpledialog.W)

        self.e1 = simpledialog.Entry(master)
        self.e2 = simpledialog.Entry(master)

        self.e1.grid(row=2, column=1)
        self.e2.grid(row=3, column=1)

        return self.e1  # initial focus

    def apply(self):
        self.answered = True
        self.relativeSizeLimit = self.e1.get() if len(self.e1.get()) else relativeSizeLimit
        self.spikeDurationLimit = self.e2.get() if len(self.e2.get()) else spikeDurationLimit


"""

    Actual program starts here. 
    I know I probably should have done this using object-oriented stuff but 
    hey, this is Python, not C#.

"""    


def printSpike(theSpike):
    print("Spike @", theSpike.startPoint, "- D A", theSpike.getDuration(), theSpike.getAmplitude())


relativeSizeLimit = 0.5  # how different spike deflections can be to be classed as part of the same spike
spikeDurationLimit = 40  # limit spike search to 20ms (40 data points)

# Get options
root = tk.Tk()
root.withdraw()
d = MyDialog(root)

if not d.answered:
    raise SystemExit(0)

relativeSizeLimit = int(d.relativeSizeLimit)
spikeDurationLimit = int(d.spikeDurationLimit) * 2

# Get .csv files to work with
csvs = filedialog.askopenfilenames(parent=root, title="Select raw data files",
                                        filetypes=(("comma-separated values", "*.csv"), ("all files","*.*")))

if not len(csvs) > 0:
    print("No input files provided - exiting.")
    raise SystemExit(0)

# Select save location for output
outputFile = filedialog.asksaveasfilename(title="Save output file as", defaultextension=".csv",
                                       filetypes=(("comma-separated values", "*.csv"), ("all files","*.*")))

if not outputFile:
    print("No output file - exiting.")
    raise SystemExit(0)

# initalise some variables - why do I do this in python? Habit, I guess.
startTime = time.time()  # we'll record the time so we can look really smug at the end
i = 0
stimulusList = []
responseList = []

for myCSV in csvs:    
    i += 1
    # get raw data
    print(i, "getDataLists:", myCSV) 
    dataList = getDataTuple(myCSV) 
    # split data into stimulus/response
    # both lists are 2000 data points long
    stimulusList = getStimulusList(dataList)
    responseList = getResponseList(dataList)
    # find the means
    stimulusMean = getMean(stimulusList)
    responseMean = getMean(responseList)
    # find the stimulus values above average
    zeroList = getZeroList(stimulusList, stimulusMean)
    # zero out the data where stimulus is below average
    #stimulusList = flatten(stimulusList, zeroList, stimulusMean)
    #responseList = flatten(responseList, zeroList, responseMean)
    #stimulusList = smooth(stimulusList, 10)
    stimulusList = split(stimulusList)
    # clean spike data (with zeros for cleaned values)
    responseList = findExtremes(responseList, responseMean)
    print("Generating spike list")
    spikes = []
    n = 0
    lastOnset = 0.0
    limit = len(responseList)
    while n < limit:
        aSpike = getNextSpike(responseList, responseMean, n, lastOnset)
        if not aSpike:
            break
        elif not isinstance(aSpike, spike):
            n = aSpike
        else:
            spikes.append(aSpike)
            lastOnset = aSpike.endPoint
            n = aSpike.endPoint + 1

    fillValues(spikes, stimulusList)            
            
    for aSpike in spikes:        
        writeSpikeToCSV(aSpike, os.path.basename(myCSV), outputFile)
        
    print("Done.")
    #if i == 33:
    #    for theSpike in spikes:
     #       if theSpike.getAmplitude() > 0.1:
     #           printSpike(theSpike)
    #writeStuff(responseList, stimulusList, folder+"/clean_"+os.path.basename(myCSV))

endTime = time.time()
elapsedTime = str(endTime - startTime)
# the payoff of the professional look - job and time-to-complete
msg = f"Success.\n\nSettings:\nRelative spike size: {relativeSizeLimit}\n" \
      f"Min spike duration: {spikeDurationLimit/2}ms\nFiles processed: {str(i)}\nTime taken: {elapsedTime[:4]}s\n\n" \
      f"Output saved in {outputFile}\n"
msg += f"\nThank you for using legUp."
messagebox.showinfo("Summary", msg)
