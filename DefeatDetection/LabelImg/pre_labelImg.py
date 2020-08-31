# -*- coding: utf-8 -*-
"""
Created on Sat Dec  1 13:46:46 2018

@author: cjy
"""

import sys
import os
import shutil
import labelImg
import thumbGeneration

imagePath = ""
predefClassFilePath = "" 
savePath = ""


exePath = ""
srcRootPath = ""
xmlSubFileName = ""
InspectingOfficer = ""
srcRootPath2 = ""
xmlSubFileName2 = ""
InspectingOfficer2 = ""
workPath = ""

#srcRootPath = "D:/myWork/clear/"
#xmlSubFileName = "20181115412/20181115/1019/1/xml/1019_1_0_1_2018_20181127163317.XML"
#workPath = ""

'''
srcRootPath = "D:/myWork/clear/"
xmlSubFileName = "20181115412/20181115/1019/1/xml/1019_1_0_1_2018_20181127163317.XML"
InspectingOfficer = "5Zac5rSL5rSL"
srcRootPath2 = "D:/myWork/clear/"
xmlSubFileName2 = "20181115412/20181115/1019/1/xml/1019_1_0_2_2019_20181127205735.XML"
InspectingOfficer2 = "5Zac5rSL5rSL"
'''
if len(sys.argv) != 4 and len(sys.argv) != 7:
    print('Usage: normal')
    #exit(1)
elif len(sys.argv) == 4:
    exePath = sys.argv[0]
    srcRootPath = sys.argv[1]
    xmlSubFileName = sys.argv[2]
    InspectingOfficer = sys.argv[3]
else:
    exePath = sys.argv[0]
    srcRootPath = sys.argv[1]
    xmlSubFileName = sys.argv[2]
    InspectingOfficer = sys.argv[3]
    
    srcRootPath2 = sys.argv[4]
    xmlSubFileName2 = sys.argv[5]
    InspectingOfficer2 = sys.argv[6]
    #savePath = sys.argv[3]
    '''
    exePath = sys.argv[0]
    imagePath = sys.argv[1]
    predefClassFilePath = sys.argv[2]
    savePath = sys.argv[3]
    '''
#workPath = exePath.replace("pre_labelImg.exe","")
workPath = os.path.dirname(exePath)
  

def ParseArgvs(srcRootPath,xmlSubFileName):
    (xmlSubPath,xmlfilename) = os.path.split(xmlSubFileName) 
    (xml_pre,xml_ext) = os.path.splitext(xmlfilename)
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
    shutil.copy(imagefullname,savePath)
    
    origin_JPG_name = savePath + "/" + imagefilename
    changed_JPG_name = savePath + "/" + xml_pre + ".JPG"
    if os.path.exists(changed_JPG_name) == True:
        os.remove(changed_JPG_name)
    os.rename(origin_JPG_name,changed_JPG_name)
    
    return changed_JPG_name,predefClassFilePath,savePath

def filesConfigs(): 
    argv = []
    argv_org = []
    changed_JPG_name = []
    argv2 = []
    argv2_org = []
    changed_JPG_name2 = []
    savePath = []
    savePath2 = []
    if len(sys.argv) == 4:
        (changed_JPG_name,predefClassFilePath,savePath) = ParseArgvs(srcRootPath,xmlSubFileName) 
        argv = [sys.argv[0],changed_JPG_name,predefClassFilePath,savePath]
        argv_org = [sys.argv[1],sys.argv[2],sys.argv[3]]        

    if len(sys.argv) == 7:
        (changed_JPG_name,predefClassFilePath,savePath) = ParseArgvs(srcRootPath,xmlSubFileName) 
        argv = [sys.argv[0],changed_JPG_name,predefClassFilePath,savePath]
        argv_org = [sys.argv[1],sys.argv[2],sys.argv[3]]      
        
        (changed_JPG_name2,predefClassFilePath2,savePath2) = ParseArgvs(srcRootPath2,xmlSubFileName2)
        argv2 = [sys.argv[0],changed_JPG_name2,predefClassFilePath2,savePath2]
        argv2_org = [sys.argv[4],sys.argv[5],sys.argv[6]]
    
    
    #argv_org = ["D:/myWork/clear/","20181115412/20181115/1019/1/xml/1019_1_0_1_2018_20181127163317.XML","5Zac5rSL5rSL"]
    
    #argv2_org = ["D:/myWork/clear/","20181115412/20181115/1019/1/xml/1019_1_0_2_2019_20181127205735.XML","5Zac5rSL5rSL"]
   
    try:
        if len(argv_org) == 3:
            if len(argv2_org) == 3:
                sys.exit(labelImg.main(argv,argv_org,argv2,argv2_org))
            else:
                sys.exit(labelImg.main(argv,argv_org))
        else:
            sys.exit(labelImg.main())

    #except:
    #    print('die')        
    finally:       
        #os.rename(changed_JPG_name,origin_JPG_name)  
        if os.path.exists(changed_JPG_name) ==True:
            thumbGeneration.GenerationThumbAndErrThumb2(changed_JPG_name,srcRootPath.replace("clear","repair")+xmlSubFileName,savePath)
            os.remove(changed_JPG_name)
            if os.path.exists(savePath+"/th") ==True:
                shutil.rmtree(savePath+"/th")
        if os.path.exists(changed_JPG_name2) ==True:
            os.remove(changed_JPG_name2)
        if os.path.exists(srcRootPath.replace("clear","repair")+xmlSubFileName2) ==True:
            os.remove(srcRootPath.replace("clear","repair")+xmlSubFileName2)
           
        
 
    
if __name__ == '__main__':
    if len(sys.argv) == 4 or len(sys.argv) == 7:
        filesConfigs()
    else:
        sys.exit(labelImg.main([sys.argv[0]]))

