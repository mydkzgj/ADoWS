# -*- coding: utf-8 -*-
"""
Created on Thu Nov 15 15:04:58 2018

@author: nnir
"""

from threading import Timer
from datetime import datetime
import shutil
import sys
import os

exePath = ""
workPath = ""
rootPath = ""
reserveMaskFlag = 0
if len(sys.argv) != 2 and len(sys.argv) != 3:
    print('Usage: python rootpath reserveMaskFlag')
    exit(1)
elif len(sys.argv) == 2:
    exePath = sys.argv[0]
    rootPath = sys.argv[1]
    workPath = os.path.dirname(exePath)
elif len(sys.argv) == 3:
    exePath = sys.argv[0]
    rootPath = sys.argv[1]
    reserveMaskFlag = 1 if int(sys.argv[2])==1 else 0
    workPath = os.path.dirname(exePath)

#python D:/ADoWS/Code/specific/Detection/TimingDetection.py D:/myWork/clear 1

class MyTimer( object ):

    def __init__( self, start_time, interval, callback_proc, args=None, kwargs=None ):

        self.__timer = None
        self.__start_time = start_time
        self.__interval = interval
        self.__callback_pro = callback_proc
        self.__args = args if args is not None else []
        self.__kwargs = kwargs if kwargs is not None else {}

    def exec_callback( self, args=None, kwargs=None ):
        self.__callback_pro( *self.__args, **self.__kwargs )
        self.__timer = Timer( self.__interval, self.exec_callback )
        self.__timer.start()

    def start( self ):
        interval = self.__interval - ( datetime.now().timestamp() - self.__start_time.timestamp() )
        #print( interval )
        self.__timer = Timer( interval, self.exec_callback )
        self.__timer.start()

    def cancel( self ):
        self.__timer.cancel() 
        self.__timer = None

'''
class AA:
    def hello( self, name, age ):
        print( "[%s]\thello %s: %d\n" % ( datetime.now().strftime("%Y%m%d %H:%M:%S"), name, age ) )
'''

class TD:
    def readLog(self,logPath):
        readLogName=os.path.join(logPath,"working.txt")
        writeLogName=os.path.join(logPath,"worked.txt")
        tempReadLogName = os.path.join(logPath,"workingtemp.txt")
        readLog= open(readLogName,'r')
        writeLog = open(writeLogName,'a')
        #tempReadLog=open(tempReadLogName,'w')
        firstline = readLog.readline()
        secondline = readLog.readline()
        thirdline = readLog.readline()        
        readLog.close()
        
        #print(firstline)
        #print(secondline)      
        
        print( "Time: %s" % ( datetime.now().strftime("%Y%m%d %H:%M:%S")))
        if(firstline!=''):
            
            print(firstline)
            finishfile = open(os.path.join(workPath,'FinishFlag.txt'),'w') 
            finishfile.write("0")
            finishfile.close()            
            #cmdline="Detection.exe "+firstline.strip('\n')+" C:/Users/nnir/Desktop/software/SavedModel/wall_inference_graph"+" D:/tensorflow/LackDetection/data"#+" >>log.txt"   #用pythonw 程序后台跑，无法停止
            if os.path.exists(os.path.join(workPath,"Detection.exe"))==True:
                cmdline=os.path.join(workPath,"Detection.exe")+" "+firstline.strip('\n')+" D:/ADoWS/DetectionAbnormity/ModelInUse"+" D:/ADoWS/DetectionAbnormity/Data" + " 640"+" 0.5"+" 0.5"+" D:/ADoWS/DetectionWindow/ModelInUse"+" D:/ADoWS/DetectionWindow/Data"+ " 0.25"+" 0.5"#+" >>log.txt"   #用pythonw 程序后台跑，无法停止
            else:
                cmdline="python "+os.path.join(workPath,"Detection.py")+" "+firstline.strip('\n')+" D:/ADoWS/DetectionAbnormity/ModelInUse"+" D:/ADoWS/DetectionAbnormity/Data" + " 640"+" 0.5"+" 0.5"+" D:/ADoWS/DetectionWindow/ModelInUse"+" D:/ADoWS/DetectionWindow/Data"+ " 0.25"+" 0.5"#+" >>log.txt"   #用pythonw 程序后台跑，无法停止
            os.system(cmdline)            
            finishfile = open(os.path.join(workPath,'FinishFlag.txt'),'r') 
            finishflag = finishfile.readline()
            finishfile.close()
            

            
            if(finishflag == "1"):
                if reserveMaskFlag == 0:
                    #删除临时文件夹
                    outputMASKpath = os.path.join(firstline.strip('\n'),"mask")
                    if os.path.exists(outputMASKpath)==True:
                        shutil.rmtree(outputMASKpath)
                
                readLog= open(readLogName,'r')
                tempReadLog=open(tempReadLogName,'w')
                lineIndex=0
                for line in readLog:
                    lineIndex = lineIndex+1
                    if(lineIndex==1):
                        continue
                    if(lineIndex==2 and secondline =="end\n"):
                        writeLog.write(thirdline)
                        continue
                    if(lineIndex==3 and secondline =="end\n"):
                        continue
                    tempReadLog.write(line)
                    
                tempReadLog.close() 
                readLog.close()
                os.remove(readLogName)
                os.rename(tempReadLogName,readLogName)
                writeLog.close()   
        else:
            print("No Task\n")    
            
            
            

if __name__ == "__main__":    
    td = TD()
    start = datetime.now().replace( minute=3, second=0, microsecond=0 )
    tmr = MyTimer( start, 10, td.readLog, [ rootPath] )
    tmr.start()
    tmr.cancel()


'''

import os
import sys
import time
import sched 

schedule = sched.scheduler ( time.time, time.sleep )

def func(string1):  
    cmdline="python Detection.py "+string1#+" >>log.txt"   #用pythonw 程序后台跑，无法停止
    print(cmdline)

schedule.enter(2,0,func,("test1"))
schedule.run()  

rootPath = ""
if len(sys.argv) != 2:
    print('Usage: python input_name output_name')
    exit(1)
else:
    rootPath = sys.argv[1]
'''