# -*- coding: utf-8 -*-
"""
Created on Tue Dec 18 08:57:59 2018

@author: cjy
"""


import sys
import os
import shutil
import labelImg

from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont
import xml.dom.minidom
#import thumbGeneration as th

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
#python pre_labelImg2.py D:/myWork/clear/ 20181115412/20181115/1019/1/xml/1019_1_0_1_2018_20181127163317.XML 5Zac5rSL5rSL D:/myWork/clear/20181115412/20181115/1019/1/org/1019_1_0_2_2018.JPG





if len(sys.argv) != 4 and len(sys.argv)!=5 and len(sys.argv) != 7:
    print('Usage: normal')
    #exit(1)
elif len(sys.argv) == 4:
    exePath = sys.argv[0]
    srcRootPath = sys.argv[1]
    xmlSubFileName = sys.argv[2]
    InspectingOfficer = sys.argv[3]
elif len(sys.argv) == 5:
    exePath = sys.argv[0]
    srcRootPath = sys.argv[1]
    xmlSubFileName = sys.argv[2]
    InspectingOfficer = sys.argv[3]
    
    compareImgPath = sys.argv[4]

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
    imagefullname = os.path.join(imagePath,imagefilename)
    predefClassFilePath = os.path.join(workPath,"predefClass.txt" )
    xmlfullname = os.path.join(srcRootPath,xmlSubFileName)
    savePath = srcRootPath.replace("clear","repair") + xmlSubPath  
    
    #将xml文件进行搬移到savePath,并将xmlfullname替换成新名字
    #创建保存路径
    if os.path.exists(savePath)!=True:
        os.makedirs(savePath)
    shutil.copy2(xmlfullname,savePath)
    xmlfullname = os.path.join(savePath,xmlfilename)    
    
    #创建i_x_namedict
    i_x_namedict={}
    i_x_namedict[imagefilename] = xmlfilename.replace(".XML",".xml")
    
    print(imagefullname)
    print(predefClassFilePath)
    print(savePath)    
    
    return imagefullname,predefClassFilePath,savePath,i_x_namedict

def ParseArgvs2(srcRootPath,xmlSubFileName):
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
    imagefullname = os.path.join(imagePath,imagefilename)
    predefClassFilePath = os.path.join(workPath,"predefClass.txt" )
    xmlfullname = os.path.join(srcRootPath,xmlSubFileName)
    savePath = srcRootPath.replace("clear","compair") + xmlSubPath  
    
    #将xml文件进行搬移到savePath,并将xmlfullname替换成新名字
    #创建保存路径
    if os.path.exists(savePath)!=True:
        os.makedirs(savePath)
    shutil.copy2(xmlfullname,savePath)
    xmlfullname = os.path.join(savePath,xmlfilename)    
    
    #创建i_x_namedict
    i_x_namedict={}
    i_x_namedict[imagefilename] = xmlfilename.replace(".XML",".xml")
    
    print(imagefullname)
    print(predefClassFilePath)
    print(savePath)    
    
    return imagefullname,predefClassFilePath,savePath,i_x_namedict

def filesConfigs(srcRootPath,xmlSubFileName,srcRootPath2,xmlSubFileName2): 
    #1.先将两个输入路径规整（分隔符）
    templist = srcRootPath.split("/")
    srcRootPath = templist[0]
    for index,folder in enumerate(templist):   
        if index == 0:
            continue
        srcRootPath = srcRootPath+"\\"+folder    
    
    templist = xmlSubFileName.split("/")
    xmlSubFileName = templist[0]
    for index,folder in enumerate(templist):   
        if index == 0:
            continue
        xmlSubFileName = os.path.join(xmlSubFileName,folder)  
    
    argv = []
    argv_org = []
    argv2 = []
    argv2_org = []


    if len(sys.argv) == 4:
        (imagefullname,predefClassFilePath,savePath,i_x_namedict) = ParseArgvs(srcRootPath,xmlSubFileName) 
        argv = [imagefullname,predefClassFilePath,savePath,i_x_namedict]
        argv_org = [sys.argv[1],sys.argv[2],sys.argv[3]]        

    if len(sys.argv) == 5:
        (imagefullname,predefClassFilePath,savePath,i_x_namedict) = ParseArgvs(srcRootPath,xmlSubFileName) 
        argv = [imagefullname,predefClassFilePath,savePath,i_x_namedict]
        argv_org = [sys.argv[1],sys.argv[2],sys.argv[3]]
        
        argv2 = [compareImgPath,predefClassFilePath,savePath,{}]
        
    if len(sys.argv) == 7:
        (imagefullname,predefClassFilePath,savePath,i_x_namedict) = ParseArgvs(srcRootPath,xmlSubFileName) 
        argv = [imagefullname,predefClassFilePath,savePath,i_x_namedict]
        argv_org = [sys.argv[1],sys.argv[2],sys.argv[3]] 
        
        (imagefullname2,predefClassFilePath2,savePath2,i_x_namedict2) = ParseArgvs2(srcRootPath2,xmlSubFileName2)
        argv2 = [imagefullname2,predefClassFilePath2,savePath2,i_x_namedict2]
        argv2_org = [sys.argv[4],sys.argv[5],sys.argv[6]]
    
    
    #argv_org = ["D:/myWork/clear/","20181115412/20181115/1019/1/xml/1019_1_0_1_2018_20181127163317.XML","5Zac5rSL5rSL"]
    
    #argv2_org = ["D:/myWork/clear/","20181115412/20181115/1019/1/xml/1019_1_0_2_2019_20181127205735.XML","5Zac5rSL5rSL"]
   
    try:
        if len(argv_org) == 3:
            if len(argv2_org) == 3:
                sys.exit(labelImg.main(argv,argv_org,argv2,argv2_org))
            elif len(argv2) == 4:
                sys.exit(labelImg.main(argv,argv_org,argv2,argv2_org))
            else:
                sys.exit(labelImg.main(argv,argv_org))
        else:
            sys.exit(labelImg.main())

    #except:
    #    print('die')        
    
    finally:                
        comPath =  srcRootPath.replace("clear","compair")
        if os.path.exists(comPath) ==True:
            #shutil.rmtree(srcRootPath.replace("clear","repairTemp"))
            for root, dirs, files in os.walk(comPath, topdown=False):
                #print("root: ", root, "  dirs: ", dirs, "  files: ",files)
                '''
                root:  foo/bar/baz/empty/test   dirs:  []   files:  []
                root:  foo/bar/baz/empty   dirs:  ['test']   files:  []
                root:  foo/bar/baz   dirs:  ['empty']   files:  ['test_bak.txt', 'test.txt']
                '''
                #continue
                for name in files:
                    os.remove(os.path.join(root, name))
                for name in dirs:
                    os.rmdir(os.path.join(root, name))
            os.rmdir(comPath)
        
        print("done")
        
 
    
if __name__ == '__main__':
    if len(sys.argv) == 4 or len(sys.argv) == 5 or len(sys.argv) == 7:
        filesConfigs(srcRootPath,xmlSubFileName,srcRootPath2,xmlSubFileName2)
    else:
        sys.exit(labelImg.main())

