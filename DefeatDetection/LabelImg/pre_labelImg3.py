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
import thumbGeneration as th

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
  
def Generate_img_xml_namedict(inputPath):
    imgPath = os.path.join(inputPath,"org")
    xmlPath = os.path.join(inputPath,"xml")
    if os.path.exists(imgPath) != True or os.path.exists(xmlPath) != True:
        return False
    
    if os.path.exists(os.path.join(imgPath,"img_xml_namedict.txt"))==True:
        os.remove(os.path.join(imgPath,"img_xml_namedict.txt"))
    imglist = os.listdir(imgPath)
    xmllist = os.listdir(xmlPath)
    
    fb = open(os.path.join(inputPath,"img_xml_namedict.txt"),"w")
    
    if len(imglist)==len(xmllist):
        for index,imgname in enumerate(imglist):
            fb.write(imgname)
            fb.write(" ")
            fb.write(xmllist[index].replace(".XML",".xml"))
            fb.write("\n")
    else:
        return False
            
    fb.close()
    return True
  
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
    imageName = image_pre + ".JPG"
    xmlPath = srcRootPath+xmlSubPath
    imagePath = xmlPath.replace("xml","org",1) 
    imagefullname = os.path.join(imagePath,imageName)
    
    return [imagePath,imagefullname,xmlPath]
    
def filesConfigs(srcRootPath,xmlSubFileName):    
   
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
        
    #2.计算labelImg输入参数
    [imagePath,imagefullname,xmlPath] = ParseArgvs(srcRootPath,xmlSubFileName)
        
    predefClassFilePath = os.path.join(workPath,"predefClass.txt" )    
    
    
    #生成img_xml_namedict.txt文件
    img_xml_txtpath = os.path.join(os.path.dirname(imagePath),"img_xml_namedict.txt")
    if os.path.exists(img_xml_txtpath) != True:
        Generate_img_xml_namedict(os.path.dirname(img_xml_txtpath))
    
    img_xml_namedict = {}
    if os.path.exists(imagefullname) == True:        
        img_xml_txtpath = os.path.join(os.path.dirname(imagePath),"img_xml_namedict.txt")
        if os.path.exists(img_xml_txtpath) == True:            
            img_xml_txt = open(img_xml_txtpath,"r")
            for line in img_xml_txt:
                line = line.strip("\n")
                names = line.split(" ")
                imgName = names[0]
                xmlName = names[1]
                img_xml_namedict[imgName] = xmlName
    else:
        print("There is no file!")
    
    labelImg_argv = [imagefullname,predefClassFilePath,xmlPath,img_xml_namedict]
    argv_org = [sys.argv[1],sys.argv[2],sys.argv[3]]
    #print(labelImg_argv)
    #print(argv_org)
    
    #通过参数调用labelImg
    try:
        if len(labelImg_argv) == 4 and len(argv_org) == 3:
                sys.exit(labelImg.main(labelImg_argv,argv_org))
        else:
            sys.exit(labelImg.main())

   
    finally:   
        print("success!")       
 
    
if __name__ == '__main__':
    if len(sys.argv) == 4 or len(sys.argv) == 5 or len(sys.argv) == 7:
        filesConfigs(srcRootPath,xmlSubFileName)
    else:
        sys.exit(labelImg.main([sys.argv[0]]))

