# -*- coding: utf-8 -*-
"""
Created on Sat Oct 27 16:47:34 2018

@author: cjy
"""


from __future__ import division
import os
import sys
from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont
import xml.dom.minidom
#import numpy as np
#import random
#import time
#import datetime

"""

Usage:

  # cut Pic by xml:(you'd better place images and xmls together)

  python cutPic.py cropNum inputPath (outputPath)
 

"""


def main():
    #设定命令行参数个数
    ImgPath = ""
    AnnoPath = ""
    OutputPath = ""

    #print(sys.argv)
    if len(sys.argv) != 2 and len(sys.argv) != 3 and len(sys.argv) != 4:
        print('Usage: python inputPath outputPath')
        exit(1)
    elif len(sys.argv) == 2:    
        ImgPath = sys.argv[1]
        AnnoPath = sys.argv[1]
        OutputPath = sys.argv[1]
    elif len(sys.argv) == 3:   
        ImgPath = sys.argv[1]
        AnnoPath = sys.argv[1]
        OutputPath = sys.argv[2]
    else:
        ImgPath = sys.argv[1]
        AnnoPath = sys.argv[2]
        OutputPath = sys.argv[3]
    multiGenerationTaET("C:/Users/nnir/Desktop/window/org","C:/Users/nnir/Desktop/window/xml","C:/Users/nnir/Desktop/window/output")


def GenerationThumbAndErrThumb(imageFilename,xmlFilename,outputPath,quality):
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
    img.save(outputThumb,quality = quality)  #只进行质量压缩   #,quality=10
        
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
            color = "blue"
            objectNumByCates[2] = objectNumByCates[2]+1
        elif(objectname == "sundries"):
            color = "blue"
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
    outputErrThumb = outputErrThumbPath + "/" + xmlf_pre + "_a" + str(objectNumByCates[0]) + "_b" + str(objectNumByCates[1]) + "_c" + str(objectNumByCates[2]) + "_d" + str(objectNumByCates[3]) + "_N" +str(objectNumByCates[4]) +".JPG"
    thumbImg.save(outputErrThumb)
    return outputErrThumb

def GenerationErrThumb(imageFilename,xmlFilename,outputPath,D_Num,quality):
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
    if os.path.exists(outputThumb) !=True:
        img.save(outputThumb,quality=quality)  #只进行质量压缩   #,quality=10
        
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
            color = "blue"
            objectNumByCates[2] = objectNumByCates[2]+1
        elif(objectname == "sundries"):
            color = "blue"
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
    outputErrThumb = outputErrThumbPath + "/" + xmlf_pre + "_a" + str(objectNumByCates[0]) + "_b" + str(objectNumByCates[1]) + "_c" + str(objectNumByCates[2]) + "_d" + str(objectNumByCates[3]) + "_N" +str(objectNumByCates[4]) + "_D"+str(D_Num)+".JPG"
    thumbImg.save(outputErrThumb)
    return outputErrThumb

def GenerationErrThumb2(imageFilename,xmlFilename,outputPath,D_Num,quality):
    xmlpath,xmlfile = os.path.split(xmlFilename)
    xmlf_pre, ext = os.path.splitext(xmlfile)    
    
    rootPath = os.path.dirname(os.path.dirname(imageFilename))
    outputThumbPath = os.path.join(rootPath,'th')
    if os.path.exists(outputThumbPath)!=True:
        os.mkdir(outputThumbPath)
        
    outputErrThumbPath = outputPath
    if os.path.exists(outputErrThumbPath)!=True:
        os.mkdir(outputErrThumbPath)
        
    outputThumb = outputThumbPath + "/" + xmlf_pre + ".JPG"
    
    DomTree = xml.dom.minidom.parse(xmlFilename)  # 打开xml文档
    annotation = DomTree.documentElement  # 得到xml文档对象    
    
    namelist = annotation.getElementsByTagName('name')
    bndboxlist = annotation.getElementsByTagName('bndbox')
    
    img = Image.open(imageFilename)    
    if os.path.exists(outputThumb) !=True:
        img.save(outputThumb,quality=quality)  #只进行质量压缩   #,quality=10
        
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
            color = "blue"
            objectNumByCates[2] = objectNumByCates[2]+1
        elif(objectname == "sundries"):
            color = "blue"
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
    outputErrThumb = outputErrThumbPath + "/" + xmlf_pre + "_a" + str(objectNumByCates[0]) + "_b" + str(objectNumByCates[1]) + "_c" + str(objectNumByCates[2]) + "_d" + str(objectNumByCates[3]) + "_N" +str(objectNumByCates[4]) + "_D"+str(D_Num)+".JPG"
    thumbImg.save(outputErrThumb)
    return outputErrThumb


def multiGenerationTaET(ImgPath,AnnoPath,OutputPath):
    xmllist = os.listdir(AnnoPath)
    for xmlf in xmllist:
        xmlf_pre, ext = os.path.splitext(xmlf)
        if ext!=".XML" and ext!=".xml":
            continue
        image_pre = ""
        sub_xmlf = xmlf_pre.split('_')
        for sub_index,sub in enumerate(sub_xmlf):
            if(sub_index == 0):
                image_pre = sub
            elif (sub_index == len(sub_xmlf)-1):
                continue
            else:
                image_pre = image_pre + '_' +sub
        print(image_pre)
        image = image_pre + ".JPG"
        
        imageFilename = ImgPath + "/" + image
        xmlFilename = AnnoPath + "/" + xmlf
        GenerationThumbAndErrThumb(imageFilename,xmlFilename,OutputPath)

        
if __name__ == "__main__":
    main()
    
