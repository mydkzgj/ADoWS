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

'''
srcRootPath = "D:/myWork/clear/"
xmlSubFileName = "20181115412/20181115/1019/1/xml/1019_1_0_1_2018_20181127163317.XML"
InspectingOfficer = "5Zac5rSL5rSL"
srcRootPath2 = "D:/myWork/clear/"
xmlSubFileName2 = "20181115412/20181115/1019/1/xml/1019_1_0_2_2019_20181127205735.XML"
InspectingOfficer2 = "5Zac5rSL5rSL"
'''
#python pre_labelImg2.py D:/myWork/clear/ 20181115412/20181115/1019/1/xml/1019_1_0_1_2018_20181127163317.XML 5Zac5rSL5rSL D:/myWork/clear/20181115412/20181115/1019/1/org/1019_1_0_2_2018.JPG

'''
def GenerationThumbAndErrThumb2(imageFilename,xmlFilename,outputPath):
    xmlpath,xmlfile = os.path.split(xmlFilename)
    xmlf_pre, ext = os.path.splitext(xmlfile)    
    
    outputThumbPath = outputPath + '/' + 'th'
    if os.path.exists(outputThumbPath)!=True:
        os.mkdir(outputThumbPath)
        
    outputErrThumbPath = outputPath + '/' + 'err'
    if os.path.exists(outputErrThumbPath)!=True:
        os.mkdir(outputErrThumbPath)
        
    outputThumb = outputThumbPath + "/" + xmlf_pre + ".JPG"
    
    DomTree = xml.dom.minidom.parse(xmlFilename)  # 打开xml文档
    annotation = DomTree.documentElement  # 得到xml文档对象    
    
    namelist = annotation.getElementsByTagName('name')
    bndboxlist = annotation.getElementsByTagName('bndbox')
    
    img = Image.open(imageFilename)    
    img.save(outputThumb,quality=10)  #只进行质量压缩
        
    thumbImg = Image.open(outputThumb)     
    thumbdraw = ImageDraw.Draw(thumbImg)  #创建绘制对象
    
    objectNum = 0      
    objectNumByCates = []  #分别为每一类计数，除了normal
    for i in range(5):
        objectNumByCates.append(0)
    #遍历所有检测框
    for boxIndex in range(0, len(bndboxlist)): 
        x1_list = bndboxlist[boxIndex].getElementsByTagName('xmin')  # 寻找有着给定标签名的所有的元素
        x1 = int(x1_list[0].childNodes[0].data)
        y1_list = bndboxlist[boxIndex].getElementsByTagName('ymin')
        y1 = int(y1_list[0].childNodes[0].data)
        x2_list = bndboxlist[boxIndex].getElementsByTagName('xmax')
        x2 = int(x2_list[0].childNodes[0].data)
        y2_list = bndboxlist[boxIndex].getElementsByTagName('ymax')
        y2 = int(y2_list[0].childNodes[0].data)        

        objectNum = objectNum + 1
        
        
        objectname = namelist[boxIndex].childNodes[0].data
        if(objectname == "break"):
            color = "blue"
            objectNumByCates[0] = objectNumByCates[0]+1
        elif(objectname == "crack"):
            color = "red"
            objectNumByCates[1] = objectNumByCates[1]+1
        elif(objectname == "rebar"):
            color = "blue"  #green
            objectNumByCates[2] = objectNumByCates[2]+1
        elif(objectname == "sundries"):
            color = "blue"  #yellow
            objectNumByCates[3] = objectNumByCates[3]+1
        elif(objectname == "normal"):
            color = "white"
            objectNumByCates[4] = objectNumByCates[4]+1
            continue
        #绘制矩形
        #thumbdraw.rectangle((x1, y1, x2, y2), None, 'red',10)  #green
        thumbdraw.line([(x1,y1),(x2,y1),(x2,y2),(x1,y2),(x1,y1)], color, width = 15)        
        font = ImageFont.truetype("consola.ttf", 60, encoding="unic")#设置字体        
        thumbdraw.text((x1, y2), objectname, color, font)  #fuchsia
    
    #带标注的缩略图保存
    outputErrThumb = outputErrThumbPath + "/" + xmlf_pre + "_a" + str(objectNumByCates[0]) + "_b" + str(objectNumByCates[1]) + "_c" + str(objectNumByCates[2]) + "_d" + str(objectNumByCates[3]) +".JPG"
    thumbImg.save(outputErrThumb)
    return outputErrThumb
'''



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
    imagefullname = imagePath + "/" + imagefilename
    predefClassFilePath = os.path.join(workPath,"predefClass.txt" )
    savePath = srcRootPath.replace("clear","repairTemp") + xmlSubPath  
    
    #CJY at 2018.12.18  创建最终保存路径
    savePathfinally = srcRootPath.replace("clear","repair") + xmlSubPath   
    #if os.path.exists(savePathfinally)!=True:
      #  os.makedirs(savePathfinally)
    
    
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
    
    return changed_JPG_name,predefClassFilePath,savePath,savePathfinally

def filesConfigs(): 
    argv = []
    argv_org = []
    changed_JPG_name = ""
    argv2 = []
    argv2_org = []
    changed_JPG_name2 = ""
    savePath = ""
    savePath2 = ""
    savePathfinally = ""
    savePathfinally2 = ""
    if len(sys.argv) == 4:
        (changed_JPG_name,predefClassFilePath,savePath,savePathfinally) = ParseArgvs(srcRootPath,xmlSubFileName) 
        argv = [sys.argv[0],changed_JPG_name,predefClassFilePath,savePath]
        argv_org = [sys.argv[1],sys.argv[2],sys.argv[3]]        

    if len(sys.argv) == 5:
        (changed_JPG_name,predefClassFilePath,savePath,savePathfinally) = ParseArgvs(srcRootPath,xmlSubFileName) 
        argv = [sys.argv[0],changed_JPG_name,predefClassFilePath,savePath]
        argv_org = [sys.argv[1],sys.argv[2],sys.argv[3]]  
        
        argv2 = [sys.argv[0],compareImgPath,predefClassFilePath,savePath]
        
    if len(sys.argv) == 7:
        (changed_JPG_name,predefClassFilePath,savePath,savePathfinally) = ParseArgvs(srcRootPath,xmlSubFileName) 
        argv = [sys.argv[0],changed_JPG_name,predefClassFilePath,savePath]
        argv_org = [sys.argv[1],sys.argv[2],sys.argv[3]]      
        
        (changed_JPG_name2,predefClassFilePath2,savePath2,savePathfinally2) = ParseArgvs(srcRootPath2,xmlSubFileName2)
        argv2 = [sys.argv[0],changed_JPG_name2,predefClassFilePath2,savePath2]
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
        #CJY at 2019.3.5 
        if os.path.exists(os.path.join(workPath,"saveFlag.txt")) == True:
            sF = open(os.path.join(workPath,"saveFlag.txt"),"r")
            deleteNum = sF.readline()
            #print(deleteNum)
            sF.close()
            os.remove(os.path.join(workPath,"saveFlag.txt"))
            #创建最终保存路径
            if os.path.exists(savePathfinally)!=True:
                  os.makedirs(savePathfinally)
            #生成缩略图
            outputErrThumb = th.GenerationThumbAndErrThumb(changed_JPG_name,srcRootPath.replace("clear","repairTemp")+xmlSubFileName,savePath)
            ETpre, ext = os.path.splitext(outputErrThumb)
            ETpre = ETpre + "_D" + deleteNum   #加入删除个数的记录
            outputErrThumb2 = ETpre + ext
            os.rename(outputErrThumb,outputErrThumb2)
            outputErrThumb = outputErrThumb2
            
            #搬移（缩略图+xml）
            if os.path.exists(outputErrThumb) ==True:
                shutil.copy(outputErrThumb,savePathfinally)
            if os.path.exists(srcRootPath.replace("clear","repairTemp")+xmlSubFileName) ==True:
                shutil.copy(srcRootPath.replace("clear","repairTemp")+xmlSubFileName,savePathfinally)
            
        #删除Temp文件夹
        TempPath =  srcRootPath.replace("clear","repairTemp")
        #print("Temp:",TempPath)
        if os.path.exists(TempPath) ==True:
            #shutil.rmtree(srcRootPath.replace("clear","repairTemp"))
            for root, dirs, files in os.walk(TempPath, topdown=False):
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
            os.rmdir(TempPath)   
        
        
        """
        #os.rename(changed_JPG_name,origin_JPG_name)  
        if os.path.exists(changed_JPG_name) ==True:
            #import thumbGeneration
            #outputErrThumb = thumbGeneration.GenerationThumbAndErrThumb2(changed_JPG_name,srcRootPath.replace("clear","repairTemp")+xmlSubFileName,savePath)
            outputErrThumb = GenerationThumbAndErrThumb2(changed_JPG_name,srcRootPath.replace("clear","repairTemp")+xmlSubFileName,savePath)
            
            if os.path.exists(savePathfinally)!=True:
                  os.makedirs(savePathfinally)
            if os.path.exists(outputErrThumb) ==True:
                shutil.copy(outputErrThumb,savePathfinally)
                os.remove(outputErrThumb)
            if os.path.exists(srcRootPath.replace("clear","repairTemp")+xmlSubFileName) ==True:
                shutil.copy(srcRootPath.replace("clear","repairTemp")+xmlSubFileName,savePathfinally)
                os.remove(srcRootPath.replace("clear","repairTemp")+xmlSubFileName)
            os.remove(changed_JPG_name)
            if os.path.exists(savePath+"/th") ==True:
                shutil.rmtree(savePath+"/th")
                
        if os.path.exists(changed_JPG_name2) ==True and changed_JPG_name2!="":
            os.remove(changed_JPG_name2)
        if os.path.exists(srcRootPath.replace("clear","repairTemp")+xmlSubFileName2) ==True and xmlSubFileName2!="":
            os.remove(srcRootPath.replace("clear","repairTemp")+xmlSubFileName2)         
        
        if os.path.exists(srcRootPath.replace("clear","repairTemp")) ==True:
            shutil.rmtree(srcRootPath.replace("clear","repairTemp"))
        """
        
 
    
if __name__ == '__main__':
    if len(sys.argv) == 4 or len(sys.argv) == 5 or len(sys.argv) == 7:
        filesConfigs()
    else:
        sys.exit(labelImg.main([sys.argv[0]]))

