import os
import numpy as np

def getFilterDict():
    filterDict = {}
    rootDir = "./database/tags"
    for dirName, subdirList, fileList in os.walk(rootDir):
        if(dirName != rootDir):
            break
        for fname in fileList:
            if fname.find('_') == -1:
                labelName = fname.split('.')[0]
                if(labelName == "README"):
                    continue
                validArray = np.loadtxt(rootDir + "/" + fname)
                filterDict[labelName] = validArray
    return filterDict