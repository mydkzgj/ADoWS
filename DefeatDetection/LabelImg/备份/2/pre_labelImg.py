# -*- coding: utf-8 -*-
"""
Created on Sat Dec  1 13:46:46 2018

@author: cjy
"""

import sys
import os
import shutil
import labelImg


imagePath = ""
predefClassFilePath = "" 
savePath = ""


exePath = ""
srcRootPath = ""
xmlSubFileName = ""
workPath = ""

#srcRootPath = "D:/myWork/clear/"
#xmlSubFileName = "20181115412/20181115/1019/1/xml/1019_1_0_1_2018_20181127163317.XML"
#workPath = ""

if len(sys.argv) != 4:
    print('Usage: normal')
    #exit(1)
else:
    exePath = sys.argv[0]
    srcRootPath = sys.argv[1]
    xmlSubFileName = sys.argv[2]
    InspectingOfficer = sys.argv[3]
    #savePath = sys.argv[3]
    '''
    exePath = sys.argv[0]
    imagePath = sys.argv[1]
    predefClassFilePath = sys.argv[2]
    savePath = sys.argv[3]
    '''
#workPath = exePath.replace("pre_labelImg.exe","")
workPath = os.path.dirname(exePath)

def filesConfigs():     
    (xmlSubPath,xmlfilename) = os.path.split(xmlSubFileName)    
    sub_xmlf = xmlfilename.split("_")
    image_pre = ""
    for sub_index,sub in enumerate(sub_xmlf):
        if(sub_index == 0):
            image_pre = sub
        elif(sub_index == len(sub_xmlf) - 1):
            continue
        else:
            image_pre = image_pre + "_" +sub
    imagefilename = image_pre + ".JPG"
    
    imagePath = srcRootPath + xmlSubPath.replace("xml","org",1) 
    imagefullname = imagePath + "/" + imagefilename
    predefClassFilePath = workPath + "/predefClass.txt" 
    savePath = srcRootPath.replace("clear","repair") + xmlSubPath
    
    print(imagefullname)
    print(predefClassFilePath)
    print(savePath)
    
    #创建保存路径
    if os.path.exists(savePath)!=True:
        os.makedirs(savePath)
    shutil.copy(srcRootPath + xmlSubFileName,savePath)
    
    origin_xml_name = savePath + "/" + xmlfilename
    changed_xml_name = savePath + "/" + image_pre + ".XML"
    if os.path.exists(changed_xml_name) == True:
        os.remove(changed_xml_name)
    os.rename(origin_xml_name,changed_xml_name)
    
    argv = [sys.argv[0],imagefullname,predefClassFilePath,savePath]
    argv2 = []
    if len(sys.argv) == 4:
        argv2 = [sys.argv[1],sys.argv[2],sys.argv[3]]
    #argv2 = ["E:/myWork/clear","20181115412/20181115/1019/1/xml/1019_1_0_2_20181127163317_15890459863.xml","5p2O54Wc"]
    try:
        if len(argv2) == 3:
            sys.exit(labelImg.main(argv,argv2))
        else:
            sys.exit(labelImg.main(argv))
    #except:
    #    print('die')        
    finally:       
        os.rename(changed_xml_name,origin_xml_name)    
 
    
if __name__ == '__main__':
    if len(sys.argv) == 4:
        filesConfigs()
    else:
        sys.exit(labelImg.main([sys.argv[0]]))

