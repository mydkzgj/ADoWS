# -*- coding: utf-8 -*-
"""
Created on Sat Dec 15 14:28:16 2018

@author: cjy
"""

from __future__ import division
import os
import sys
from PIL import Image
import xml.dom.minidom
#import numpy as np
import random
import numpy as np
import cv2 as cv

"""

Usage:

  # cut Pic by xml:(you'd better place images and xmls together)

  python CutsGeneration.py cropNum inputPath (outputPath) (CutNormalFlag)
  
  # for example:
  
  python E:/楼面检测项目/software/CutsGeneration_normal.py 2 E:/myWork/clear/20181115412/20181115/1019/1/1 E:/myWork/clear/20181115412/20181115/1019/1/2

  # Introduction:
  
  从原始大图上裁剪包含缺陷的特定尺寸大小的样本
  
  # Notes：
  
  用于项目或普通都可以（xml与图片是否同名）
  
  所有的匹配应该以xml，json这种为主，以他们的名字去寻找图片
  
  cropNum 是指剪裁扩增个数
  
  CutNormalFlag 是控制是否进行Normal检测的表示位 

  需要配合ClassStatic.txt使用  0表示不需要与第一个做样本均衡，1表示需要做样本均衡，2表示是负样本做特别处理,3表示不生成该类
"""

    

prefix_str ='''<?xml version="1.0" ?>
<annotation>
    <folder>{}</folder>
    <filename>{}</filename>
    <path>{}</path>
    <source>
       <database>Unknown</database>
    </source>
    <size>
       <width>{}</width>
       <height>{}</height>
       <depth>3</depth>
    </size>
    <segmented>0</segmented>
    '''
    
suffix = '</annotation>'
 
new_head = '''<object>
       <name>{}</name>
       <pose>Unspecified</pose>
       <truncated>0</truncated>
       <difficult>0</difficult>
       <bndbox>       
          <xmin>{}</xmin>
          <ymin>{}</ymin>
          <xmax>{}</xmax>
          <ymax>{}</ymax>
       </bndbox>
    </object>
'''

#注：此处默认图像与xml文件名不相同，xml有后缀
def FindImagePreAcorrdingXMLPre(xml_pre):    
    image_pre = ""
    sub_xmlf = xml_pre.split('_')
    for sub_index,sub in enumerate(sub_xmlf):
        if(sub_index == 0):
            image_pre = sub
        elif (sub_index == len(sub_xmlf)-1):
            continue
        else:
            image_pre = image_pre + '_' +sub
    #print(image_pre)
    return image_pre    


# 判断两个矩形是否相交
def box_inter(box1,box2):    
    # box=(xA,yA,xB,yB)
    x01, y01, x02, y02 = box1
    x11, y11, x12, y12 = box2

    lx = abs((x01 + x02) / 2 - (x11 + x12) / 2)
    ly = abs((y01 + y02) / 2 - (y11 + y12) / 2)
    sax = abs(x01 - x02)
    sbx = abs(x11 - x12)
    say = abs(y01 - y02)
    sby = abs(y11 - y12)

    if lx <= (sax + sbx) / 2 and ly <= (say + sby) / 2:
        return True
    else:
        return False

#以下这两个函数必须建立在矩形框相交的前提下才行，否则报错
#计算两个矩形框的交集
def cal_inter(box1,box2):
    # box=(xA,yA,xB,yB)    
    x01, y01, x02, y02 = box1
    x11, y11, x12, y12 = box2
    col=min(x02,x12)-max(x01,x11)
    row=min(y02,y12)-max(y01,y11)
    intersection=col*row    
    return intersection

#计算两个矩形框的IOU
def cal_IOU(box1,box2):
    # box=(xA,yA,xB,yB)    
    x01, y01, x02, y02 = box1
    x11, y11, x12, y12 = box2
    col=min(x02,x12)-max(x01,x11)
    row=min(y02,y12)-max(y01,y11)
    intersection=col*row
    area1=(x02-x01)*(y02-y01)
    area2=(x12-x11)*(y12-y11)
    IOU=intersection/(area1+area2-intersection)
    return IOU

'''
def solve_coincide(box1,box2):
    # box=(xA,yA,xB,yB)    
    if mat_inter(box1,box2)==True:
        x01, y01, x02, y02 = box1
        x11, y11, x12, y12 = box2
        col=min(x02,x12)-max(x01,x11)
        row=min(y02,y12)-max(y01,y11)
        intersection=col*row
        area1=(x02-x01)*(y02-y01)
        area2=(x12-x11)*(y12-y11)
        coincide=intersection/(area1+area2-intersection)
        return coincide
    else:
        return False
'''
    
def adjustCropLength(imgH,imgW,bBox,cropBaseLength):
    x1 = bBox[0]
    y1 = bBox[1]
    x2 = bBox[2]
    y2 = bBox[3]
    cropLength = cropBaseLength       
    bBoxW = x2-x1+1 
    bBoxH = y2-y1+1
    while bBoxW >= cropLength:
        cropLength = cropLength + 10   
    while bBoxH >= cropLength:
        cropLength = cropLength + 10           
    if(cropLength > imgH or cropLength > imgW):
        cropLength = min(imgH,imgW)
    if(cropLength < bBoxW or cropLength < bBoxH):   #如果目标框还是大于crop框，那就不需要剪裁，直接跳到下一个框吧
        return False
    else:
        return cropLength            


#统计每一类的样本个数，给出基于基础cropNum的class-wise cNum
#读取ClassStatistic.txt中的信息
#每一类别后面可跟4种数字：0,1,2,3
#0,1表示该类是否进入样本均衡的统计中
#2表示该类是负样本类
#3表示不生成该类
def ClassStatistics(xmlPath,configPath,baseCropNum):
    #1.制作词典保存每一类对应的数量
    CR = open(os.path.join(configPath,"ClassStatistic.txt"),"r")
    Category = []
    CategorySta = []
    preset_CropN = []
    for line in CR:        
        lineN = line.strip('\n')        
        lineSub = lineN.split(" ")
        Category.append(lineSub[0])
        CategorySta.append(int(lineSub[1]))
        if len(lineSub)== 3:  #如果flag后面跟正整数则最终cropNum为这个数
            preset_CropN.append(int(lineSub[2]))
        else:
            preset_CropN.append(-1)
    CR.close()  
    #Category = ["break","crack","rebar","sundries","normal"]
    #CategorySta = [1,1,0,0,1]
    CategoryNum = {}
    for i in range(len(Category)):
        CategoryNum[Category[i]] = 0
    
    #2.遍历xml文件夹中的文件
    xmllist = os.listdir(xmlPath)
    for xmlf in xmllist:
        xmlf_pre, ext = os.path.splitext(xmlf)
        if ext!=".XML" and ext!=".xml":
            continue
    
        xmlFullpath = os.path.join(xmlPath,xmlf)
 
        print(xmlFullpath)
        DomTree = xml.dom.minidom.parse(xmlFullpath)  # 打开xml文档
        annotation = DomTree.documentElement  # 得到xml文档对象
 
        namelist = annotation.getElementsByTagName('name')
        for i in range(len(namelist)):
            objectname = namelist[i].childNodes[0].data
            CategoryNum[objectname] = CategoryNum[objectname] + 1    

    
    print("CategoryNum:",CategoryNum)
    CropNum = {}
    for i in range(len(Category)):
        if CategorySta[i] == 1:
            if CategoryNum[Category[i]]!=0:
                CropNum[Category[i]] = int(baseCropNum *(CategoryNum[Category[0]]/CategoryNum[Category[i]]))  
            else:
                CropNum[Category[i]] = 0
            if CropNum[Category[i]]<1:
                CropNum[Category[i]] = 1
        elif CategorySta[i] == 2:
            if CategoryNum[Category[i]]!=0:
                CropNum[Category[i]] = baseCropNum *(CategoryNum[Category[0]]/CategoryNum[Category[i]])
            else:
                CropNum[Category[i]] = 0
            if CropNum[Category[i]] >= 1:
                CropNum[Category[i]] = int(CropNum[Category[i]])   
        elif CategorySta[i] == 3:
            CropNum[Category[i]] = 0
        else:
            CropNum[Category[i]] = baseCropNum
            if CropNum[Category[i]]<1:
                CropNum[Category[i]] = 1
    
    for index,pCN in enumerate(preset_CropN):
        if pCN > 0:
            print(pCN)
            CropNum[Category[index]] = pCN
            
            
    
    print("CropNum:",CropNum)
    CN = open(os.path.join(xmlPath,"CropNum.txt"),"w")
    CN.write("CategoryNum:\n")
    CN.write(str(CategoryNum)+"\n")
    CN.write("CropNum:\n")
    CN.write(str(CropNum)+"\n")
    return CropNum


def DirectionExtension(Mask,top,down,left,right):    
    SingleDEMask = []
    if top == 1:
        NewMask = np.ones(Mask.shape,np.uint8)*255
        for j in range(Mask.shape[1]):   #逐列扫描
            for i in reversed(range(Mask.shape[0])):     #反序搜索这一列
                if Mask[i,j] == 0:
                    NewMask[0:i,j:j+1] = np.zeros((i,1),np.uint8)                     
                    break
        SingleDEMask.append(NewMask)
    
    if down == 1:
        NewMask = np.ones(Mask.shape,np.uint8)*255
        for j in range(Mask.shape[1]):   #逐列扫描
            for i in range(Mask.shape[0]):     #正序搜索这一列
                if Mask[i,j] == 0:
                    NewMask[i:Mask.shape[0],j:j+1] = np.zeros((Mask.shape[0]-i,1),np.uint8)                     
                    break
        SingleDEMask.append(NewMask)
        
    if left == 1:
        NewMask = np.ones(Mask.shape,np.uint8)*255
        for i in range(Mask.shape[0]):   #逐行扫描
            for j in reversed(range(Mask.shape[1])):     #反序搜索这一列
                if Mask[i,j] == 0:
                    NewMask[i:i+1,0:j] = np.zeros((1,j),np.uint8) 
                    break
        SingleDEMask.append(NewMask)

        
    if right == 1:
        NewMask = np.ones(Mask.shape,np.uint8)*255
        for i in range(Mask.shape[0]):   #逐列扫描
            for j in range(Mask.shape[1]):     #反序搜索这一列
                if Mask[i,j] == 0:
                    NewMask[i:i+1,j:Mask.shape[1]] = np.zeros((1,Mask.shape[1]-j),np.uint8)                     
                    break
        SingleDEMask.append(NewMask)
    
    outputMask = np.ones(Mask.shape,np.uint8)*255
    for m in SingleDEMask:
        outputMask = outputMask & m
        
    return outputMask

#将重叠框合并，MainBoxIndexes中至少有一个元素
def MergeOverlapBoxes(bbCoordinateList,MainBoxIndexes):
    MainObjectBox = [bbCoordinateList[MainBoxIndexes[0]][0],bbCoordinateList[MainBoxIndexes[0]][1],bbCoordinateList[MainBoxIndexes[0]][2],bbCoordinateList[MainBoxIndexes[0]][3]]
    for boxIndex in MainBoxIndexes: 
        MainObjectBox[0] = min(MainObjectBox[0],bbCoordinateList[boxIndex][0])
        MainObjectBox[1] = min(MainObjectBox[1],bbCoordinateList[boxIndex][1])
        MainObjectBox[2] = max(MainObjectBox[2],bbCoordinateList[boxIndex][2])
        MainObjectBox[3] = max(MainObjectBox[3],bbCoordinateList[boxIndex][3])            
    
    return MainObjectBox

#crop图像左上角点的初始选择范围生成，重叠目标合并，附近框情况记录  
def AnalysisNearBoxes(bbCoordinateList,imgH,imgW,MainBoxIndexes,MainObjectBox,cropLength):   #分析在MainObjectBox主目标框周围有没有其他框以及重叠框    
    LTmaskLT = [max(MainObjectBox[2]-cropLength+1,0),max(MainObjectBox[3]-cropLength+1,0)]  #左上角点取值掩膜的左上角顶点
    LTmaskRD = [min(MainObjectBox[0],(imgW-1)-cropLength+1),min(MainObjectBox[1],(imgH-1)-cropLength+1)] #左上角点取值掩膜的右下角顶点   
    LTBox = [LTmaskLT[0],LTmaskLT[1],LTmaskRD[0],LTmaskRD[1]]      
        
    CoverBox = [LTmaskLT[0],LTmaskLT[1],LTmaskRD[0]+cropLength-1,LTmaskRD[1]+cropLength-1]  #所有可能的框的覆盖面积的并集的bBox表示 
        
    near_bBoxList = []  #与CoverBox框相交的bBox放置到near(附近)bBoxKList中
    overlap_bBoxList = []  #与MainObjectBox框相交的bBox放置到overlap(重叠)bBoxKList中
    overlap_indexList = []
    for anotherboxIndex in range(0, len(bbCoordinateList)): 
        if anotherboxIndex in MainBoxIndexes:
            continue
        else:              
            #如果有其他框与CoverBox有交集
            if box_inter(CoverBox,bbCoordinateList[anotherboxIndex]) == True:
                #如果还与MainObjectBox相交
                if box_inter(MainObjectBox,bbCoordinateList[anotherboxIndex]) == True:
                    overlap_bBoxList.append(bbCoordinateList[anotherboxIndex]) 
                    overlap_indexList.append(anotherboxIndex)
                else:
                    near_bBoxList.append(bbCoordinateList[anotherboxIndex]) 
    return LTBox,CoverBox,near_bBoxList,overlap_bBoxList,overlap_indexList



def GenerateCandidatePoints(bbCoordinateList,imgH,imgW,boxIndex,cropLength):
    #crop图像左上角点的初始选择范围生成，重叠目标合并，附近框情况记录  
    MainBoxIndexes = []   
    overlap_indexList = [boxIndex]
        
    while len(overlap_indexList) !=0:
        MainBoxIndexes = MainBoxIndexes + overlap_indexList
        MainObjectBox = MergeOverlapBoxes(bbCoordinateList,MainBoxIndexes)
        #需要重新调整一下cropLength
        cropLength = adjustCropLength(imgH,imgW,MainObjectBox,cropLength)
        if cropLength == False:
            return False,False,False,False,False
        LTBox,CoverBox,near_bBoxList,overlap_bBoxList,overlap_indexList = AnalysisNearBoxes(bbCoordinateList,imgH,imgW,MainBoxIndexes,MainObjectBox,cropLength)
        
    #当没有重叠框时，可以往下进行
    LTmaskLT = [LTBox[0],LTBox[1]]
    LTmaskRD = [LTBox[2],LTBox[3]]
    #crop窗左上角点可选位置相对坐标的掩膜
    #print(MainObjectBox)
    #print(cropLength)
    #print(LTBox)
    LTmask = np.ones((LTmaskRD[1]-LTmaskLT[1]+1,LTmaskRD[0]-LTmaskLT[0]+1),np.uint8)*255         
    #crop窗所有可能覆盖的位置
    CoverMask = np.ones((LTmaskRD[1]-LTmaskLT[1]+cropLength,LTmaskRD[0]-LTmaskLT[0]+cropLength),np.uint8)*255
    
    #如果有临近的bBox，那么需要对初始LTmask进行修正
    if len(near_bBoxList) != 0 :  #如果没有与MainObjectBox重叠的
        for bBox in near_bBoxList:
            area_bBox = (bBox[2]-bBox[0])*(bBox[3]-bBox[1])
            inter = cal_inter(bBox,CoverBox)
            interRatio = inter/area_bBox
            #print(interRatio)
            #包含的  LT可以取在边界上
            #不包含的  不可以取在与CoverBox相交的边界上
            #简化的话就都不可以取在边界上###目前选取这条
            if interRatio == 1:  #即nearBox包含在CoverBox中  由于numpy取子集不包含终止列或行，   左上角坐标+1，最终子区域不包含边界           
                CoverMask[bBox[1]-LTmaskLT[1]+1:bBox[3]-LTmaskLT[1],bBox[0]-LTmaskLT[0]+1:bBox[2]-LTmaskLT[0]] = np.zeros((bBox[3]-bBox[1]-1,bBox[2]-bBox[0]-1),np.uint8)
            else:  #即nearBox与CoverBox相交但不包含
                #计算相交部分的bBox
                interbBoxLT = [max(bBox[0],CoverBox[0]),max(bBox[1],CoverBox[1])]
                interbBoxRD = [min(bBox[2],CoverBox[2]),min(bBox[3],CoverBox[3])]    
                
                borderL = 1 if interbBoxLT[0] == CoverBox[0] else 0
                borderT = 1 if interbBoxLT[1] == CoverBox[1] else 0
                borderR = 1 if interbBoxRD[0] == CoverBox[2] else 0
                borderD = 1 if interbBoxRD[1] == CoverBox[3] else 0                        
                
                interbBox = [interbBoxLT[0],interbBoxLT[1],interbBoxRD[0],interbBoxRD[1]]
                CoverMask[interbBox[1]-LTmaskLT[1]+1-borderT:interbBox[3]-LTmaskLT[1]+borderD,interbBox[0]-LTmaskLT[0]+1-borderL:interbBox[2]-LTmaskLT[0]+borderR] = np.zeros((interbBox[3]-interbBox[1]+borderD+borderT-1,interbBox[2]-interbBox[0]+borderR+borderL-1),np.uint8)
                
        #将CoverMask做分块处理，将其映射到LTmask里
        subMaskBox = []   #左上角开始顺时针
        CenterObjectBox = [LTmaskRD[0]+1,LTmaskRD[1]+1,LTmaskLT[0]+cropLength-1-1,LTmaskLT[1]+cropLength-1-1]  #为了让subMask[0]等于LTmask（由于numpy取子集不包含终止列或行）  #注应该按照LTmask分块，而不是按照MainObjectBox分块,这二者并不等价

        subMaskBox.append([CoverBox[0]-CoverBox[0],CoverBox[1]-CoverBox[1],CenterObjectBox[0]-CoverBox[0],CenterObjectBox[1]-CoverBox[1]])       #左上角  0
        subMaskBox.append([CenterObjectBox[0]-CoverBox[0],CoverBox[1]-CoverBox[1],CenterObjectBox[2]-CoverBox[0],CenterObjectBox[1]-CoverBox[1]])   #正上方  1
        subMaskBox.append([CenterObjectBox[2]-CoverBox[0],CoverBox[1]-CoverBox[1],CoverBox[2]-CoverBox[0],CenterObjectBox[1]-CoverBox[1]])       #右上角  2
        subMaskBox.append([CenterObjectBox[2]-CoverBox[0],CenterObjectBox[1]-CoverBox[1],CoverBox[2]-CoverBox[0],CenterObjectBox[3]-CoverBox[1]])   #正右方  3
        subMaskBox.append([CenterObjectBox[2]-CoverBox[0],CenterObjectBox[3]-CoverBox[1],CoverBox[2]-CoverBox[0],CoverBox[3]-CoverBox[1]])       #右下方  4
        subMaskBox.append([CenterObjectBox[0]-CoverBox[0],CenterObjectBox[3]-CoverBox[1],CenterObjectBox[2]-CoverBox[0],CoverBox[3]-CoverBox[1]])   #正下方  5
        subMaskBox.append([CoverBox[0]-CoverBox[0],CenterObjectBox[3]-CoverBox[1],CenterObjectBox[0]-CoverBox[0],CoverBox[3]-CoverBox[1]])       #左下方  6
        subMaskBox.append([CoverBox[0]-CoverBox[0],CenterObjectBox[1]-CoverBox[1],CenterObjectBox[0]-CoverBox[0],CenterObjectBox[3]-CoverBox[1]])   #正左方  7
        
        subMask = []
        for sMBox in subMaskBox:
            subMask.append(CoverMask[sMBox[1]:sMBox[3],sMBox[0]:sMBox[2]])
        
        for subIndex in range(len(subMask)):
            if subIndex == 0 or subIndex == 2 or subIndex == 4 or subIndex == 6:
                sM = subMask[subIndex]    
                if subIndex == 0:
                    sM = DirectionExtension(sM,1,0,1,0)
                elif subIndex == 2:
                    sM = DirectionExtension(sM,1,0,0,1)
                elif subIndex == 4:
                    sM = DirectionExtension(sM,0,1,0,1)
                elif subIndex == 6:
                    sM = DirectionExtension(sM,0,1,1,0)
                subMask[subIndex] = sM
                LTmask = LTmask & subMask[subIndex]            
                #cv.imshow(str(subIndex),sM)                
                
            elif subIndex == 1 or subIndex == 5:
                #膨胀
                sM = subMask[subIndex]                                  
                kernel = cv.getStructuringElement(cv.MORPH_RECT, (2*sM.shape[1]+1,1))  # 矩形结构
                sM = ~cv.dilate(~sM, kernel) 
                #将大小转为LTmask的大小
                if sM.shape[1]<LTmask.shape[1]:
                    sM = cv.copyMakeBorder(sM,0,0,0,LTmask.shape[1]-sM.shape[1],cv.BORDER_REPLICATE)
                else:
                    sM = sM[0:sM.shape[0],0:LTmask.shape[1]]
                subMask[subIndex] = sM
                LTmask = LTmask & subMask[subIndex]
                #cv.imshow(str(subIndex),sM) 
                
            elif subIndex == 3 or subIndex == 7:
                #膨胀
                sM = subMask[subIndex] 
                kernel = cv.getStructuringElement(cv.MORPH_RECT, (1,2*sM.shape[0]+1))  # 矩形结构   
                sM = ~cv.dilate(~sM, kernel) 
                #将大小转为LTmask的大小
                if sM.shape[0]<LTmask.shape[0]:
                    sM = cv.copyMakeBorder(sM,LTmask.shape[0]-sM.shape[0],0,0,0,cv.BORDER_REPLICATE)
                else:
                    sM = sM[0:LTmask.shape[0],0:sM.shape[1]]
                subMask[subIndex] = sM
                LTmask = LTmask & subMask[subIndex]
                #cv.imshow(str(subIndex),sM) 
            
    #cv.imshow("CoverMask",CoverMask)    
    #cv.imshow("LTmask",LTmask)
    #cv.waitKey(0)        
        
    #将LTmask的点转化为向量
    LTvector = np.where(LTmask==255)  
    CL = cropLength
    print("cropLength:"+str(CL))   
    print("LTvectorLength:"+str(len(LTvector[0])))  
    return LTBox,LTmask,LTvector,CL,MainObjectBox


#依靠xml文件从High Resolution Image中剪切小样本(正方形)
def CutFromHRImgByXml(xmlFPath,imageFPath,outputPath,cropBaseLength,cropNum,CutNormalFlag):      
    #输出路径分为两个，一个按类别分，一个为总集
    SaveCategriesPath = outputPath+"/Categories/"
    if not os.path.exists(SaveCategriesPath):
        os.makedirs(SaveCategriesPath) 

    SaveAllPath = outputPath + "/Sets/All/"
    if not os.path.exists(SaveAllPath):
        os.makedirs(SaveAllPath)   
        
    SaveWithoutNormalPath = outputPath + "/Sets/WithoutNormal/"
    if not os.path.exists(SaveWithoutNormalPath):
        os.makedirs(SaveWithoutNormalPath)  
        
    #SaveTrainPath = outputPath + "/Sets/Train/"
    #if not os.path.exists(SaveTrainPath):
    #    os.makedirs(SaveTrainPath) 

        
    #1.读取xml文件获取所需信息
    DomTree = xml.dom.minidom.parse(xmlFPath)  # 打开xml文档
    annotation = DomTree.documentElement  # 得到xml文档对象 
    #filenamelist = annotation.getElementsByTagName('filename')  # [<DOM Element: filename at 0x381f788>]
    #filename = filenamelist[0].childNodes[0].data  # 获取XML节点值  
    
    #将boundingbox按种类分别放入两个List中
    bbCoordinateList=[] 
    normal_bbCoordinateList=[]     
    categoryList=[] 
    namelist = annotation.getElementsByTagName('name')
    bndboxlist = annotation.getElementsByTagName('bndbox')    
  
    for boxIndex in range(0, len(bndboxlist)): 
        x1_list = bndboxlist[boxIndex].getElementsByTagName('xmin')  # 寻找有着给定标签名的所有的元素
        x1 = int(x1_list[0].childNodes[0].data)
        y1_list = bndboxlist[boxIndex].getElementsByTagName('ymin')
        y1 = int(y1_list[0].childNodes[0].data)
        x2_list = bndboxlist[boxIndex].getElementsByTagName('xmax')
        x2 = int(x2_list[0].childNodes[0].data)
        y2_list = bndboxlist[boxIndex].getElementsByTagName('ymax')
        y2 = int(y2_list[0].childNodes[0].data) 
        
        objectname = namelist[boxIndex].childNodes[0].data
        if objectname != "normal":   #可以加上 cropNum[objectname]!=0
            categoryList.append(objectname)
            bbCoordinateList.append([x1,y1,x2,y2])
        else:
            normal_bbCoordinateList.append([x1,y1,x2,y2])
    
    #2.读取图片及其相关信息
    img = Image.open(imageFPath)     
    imgW=img.size[0]
    imgH=img.size[1]   
    p,image = os.path.split(imageFPath)
    image_pre,ext = os.path.splitext(image)
    


    #3.依照xml剪切出每个object，并可进行随机crop    
    #3.1剪切所有非normal检测框
    for boxIndex in range(0, len(bbCoordinateList)):
        #(1).从List中读取数据并计算简易衍生参数
        x1= bbCoordinateList[boxIndex][0]     
        y1= bbCoordinateList[boxIndex][1]     
        x2= bbCoordinateList[boxIndex][2]     
        y2= bbCoordinateList[boxIndex][3]          
        objectname = categoryList[boxIndex]        
        print(image + "  Box No."+str(boxIndex) +"  "+objectname)
               
        #保存路径        
        savePath = os.path.join(SaveCategriesPath,objectname)    #创建保存路径，按类别放置（主类别，可能混有其他类别）   
        
        #(2).根据目标框的大小调整裁剪框        
        #cropLength = adjustCropLength(imgH,imgW,bbCoordinateList[boxIndex],cropBaseLength)
        #if cropLength == False:
        #    continue     
        #print("cropLength:"+str(cropLength))         
        LTBox,LTmask,LTvector,cropLength,MainObjectBox = GenerateCandidatePoints(bbCoordinateList,imgH,imgW,boxIndex,cropBaseLength)    
        if cropLength == False:
            continue
        
        #如果没有得到候选点，则调整cropLength
        failedFlag = 0
        Min_CropLength = min(MainObjectBox[2]-MainObjectBox[0]+1,MainObjectBox[3]-MainObjectBox[1]+1)
        while len(LTvector[0]) == 0:
            if cropLength>Min_CropLength:
                cropLength = cropLength -1
                #print("cropLength:"+str(cropLength))
                LTBox,LTmask,LTvector,cropLengthTemp,MainObjectBox = GenerateCandidatePoints(bbCoordinateList,imgH,imgW,boxIndex,cropLength)
            else:
                failedFlag = 1
                break
        if failedFlag == 1:
            continue
        
        #如果有满足要求的点，则从中取点进行crop
                
        if len(LTvector[0])!= 0:
            for j in range(cropNum[objectname]):
                LTVindex = random.randint(0,len(LTvector[0])-1)
                cropLTpoint = [LTvector[1][LTVindex],LTvector[0][LTVindex]]
                if j == 0:
                    bBoxCenter=[int((x1+x2)/2),int((y1+y2)/2)]  #bBox中心坐标（取整） 
                    cropHalfLength=int(cropLength/2)
                    CenterToLT = [bBoxCenter[0]-cropHalfLength-LTBox[0],bBoxCenter[1]-cropHalfLength-LTBox[1]]
                    if CenterToLT[1]>0 and CenterToLT[0]>0 and CenterToLT[1]<LTmask.shape[1] and CenterToLT[0]<LTmask.shape[0]:
                        if LTmask[CenterToLT[1],CenterToLT[0]] == 255:
                            cropLTpoint = [CenterToLT[0],CenterToLT[1]]
                
                
                cropBox=[LTBox[0]+cropLTpoint[0],LTBox[1]+cropLTpoint[1],LTBox[0]+cropLTpoint[0]+cropLength,LTBox[1]+cropLTpoint[1]+cropLength]
                 
                head_str = "" + new_head.format(objectname,x1-cropBox[0], y1-cropBox[1], x2-cropBox[0], y2-cropBox[1])
                #确定其他在crop框里的bBox
                for anotherboxIndex in range(0, len(bbCoordinateList)): 
                    if anotherboxIndex==boxIndex:
                        continue
                    else:
                        a_x1= bbCoordinateList[anotherboxIndex][0]
                        a_y1= bbCoordinateList[anotherboxIndex][1]
                        a_x2= bbCoordinateList[anotherboxIndex][2]
                        a_y2= bbCoordinateList[anotherboxIndex][3]
                        a_objectname = namelist[anotherboxIndex].childNodes[0].data
                        #如果有其他框与CropBox有交集
                        if box_inter(cropBox,bbCoordinateList[anotherboxIndex]) == True:
                            interR = cal_inter(bbCoordinateList[anotherboxIndex],cropBox)/((bbCoordinateList[anotherboxIndex][2]-bbCoordinateList[anotherboxIndex][0])*(bbCoordinateList[anotherboxIndex][3]-bbCoordinateList[anotherboxIndex][1]))                            
                            if interR==1:
                                head_str = head_str + new_head.format(a_objectname,a_x1-cropBox[0], a_y1-cropBox[1], a_x2-cropBox[0], a_y2-cropBox[1])
                            
                cropedImg = img.crop(cropBox)
                
                #保存
                if not os.path.exists(savePath):
                    os.makedirs(savePath)         
                
                cropImgName=image_pre+'_{}_crop{}.JPG'.format(boxIndex,j)
                cropSaveXml = prefix_str.format(objectname,cropImgName,savePath + '/'+cropImgName,cropLength,cropLength) + head_str + suffix
                cropedImg.save(savePath + '/' + cropImgName)
                open(savePath + '/' + image_pre +'_{}_crop{}.XMl'.format(boxIndex,j), 'w').write(cropSaveXml)
                
                cropedImg.save(SaveAllPath + cropImgName)
                open(SaveAllPath + image_pre +'_{}_crop{}.XMl'.format(boxIndex,j), 'w').write(cropSaveXml)
                
                cropedImg.save(SaveWithoutNormalPath + cropImgName)
                open(SaveWithoutNormalPath + image_pre +'_{}_crop{}.XMl'.format(boxIndex,j), 'w').write(cropSaveXml)
                
                #cropedImg.save(SaveTrainPath + cropImgName)
                #open(SaveTrainPath + image_pre +'_{}_crop{}.XMl'.format(boxIndex,j), 'w').write(cropSaveXml)
    
    
    #3.2剪切所有normal检测框                        
    if CutNormalFlag == 1:
        #遍历所有normal检测框
        for boxIndex in range(0, len(normal_bbCoordinateList)): 
            x1= normal_bbCoordinateList[boxIndex][0]  
            y1= normal_bbCoordinateList[boxIndex][1]  
            x2= normal_bbCoordinateList[boxIndex][2]
            y2= normal_bbCoordinateList[boxIndex][3]              
        
            objectname = "normal"
            savePath = os.path.join(SaveCategriesPath,objectname)    
            
            print(image + "  Box No."+str(boxIndex) +"  "+objectname)
            center=[int((x1+x2)/2),int((y1+y2)/2)]
            
            #根据目标框的大小调整裁剪框
            cropLength = adjustCropLength(imgH,imgW,normal_bbCoordinateList[boxIndex],cropBaseLength)
            if cropLength == False:
                continue     
            print("cropLength:"+str(cropLength))         
            
            cropHalfLength=int(cropLength/2)        
                
            #crop图像左上角点的选择范围        
            xRange=[max(x2-cropLength+1,0),min(x1,imgW-1-cropLength+1)]
            yRange=[max(y2-cropLength+1,0),min(y1,imgH-1-cropLength+1)]
        
            cropLTpoint=[]     #LeftTop        
            if cropNum[objectname]>=1:
                normalCropNum = cropNum[objectname]
            else:
                normalCropNum = 1 if random.random()< cropNum[objectname] else 0
            
            for j in range(0, normalCropNum): 
                if (xRange[0]>=xRange[1]) or (yRange[0]>=yRange[1]):
                    break
                if j==0 and center[0]-cropHalfLength >= xRange[0] and center[0]-cropHalfLength <= xRange[1] and center[1]-cropHalfLength>=yRange[0] and center[1]-cropHalfLength<=yRange[1]:    
                    cropLTpoint=[center[0]-cropHalfLength,center[1]-cropHalfLength]
                else:
                    cropLTpoint=[random.randint(xRange[0],xRange[1]),random.randint(yRange[0],yRange[1])]
                #可能会出现重复的结果，后续改进记录
                cropBox=[cropLTpoint[0],cropLTpoint[1],cropLTpoint[0]+cropLength,cropLTpoint[1]+cropLength]

                #再次遍历所有检测框，确定是否有其他非normal框在crop窗口内     
                for anotherboxIndex in range(0, len(bbCoordinateList)): 
                    a_x1= bbCoordinateList[anotherboxIndex][0]    
                    a_y1= bbCoordinateList[anotherboxIndex][1]   
                    a_x2= bbCoordinateList[anotherboxIndex][2] 
                    a_y2= bbCoordinateList[anotherboxIndex][3]     
                    a_objectname = categoryList[anotherboxIndex]
                    if ( (a_x1>=cropBox[0] and a_x1<=cropBox[2] and a_y1>=cropBox[1] and a_y1<=cropBox[3]) or
                        (a_x2>=cropBox[0] and a_x2<=cropBox[2] and a_y1>=cropBox[1] and a_y1<=cropBox[3]) or
                        (a_x1>=cropBox[0] and a_x1<=cropBox[2] and a_y2>=cropBox[1] and a_y2<=cropBox[3]) or
                        (a_x2>=cropBox[0] and a_x2<=cropBox[2] and a_y2>=cropBox[1] and a_y2<=cropBox[3]) ):
                        break
                    else:  #没有其他物体在normal_crop中
                        if anotherboxIndex == len(bbCoordinateList)-1:
                            head_str ='' + new_head.format(objectname,0, 0, cropLength-1, cropLength-1)
                            cropedImg = img.crop(cropBox)
                        
                            #保存
                            if not os.path.exists(savePath):
                                os.makedirs(savePath)
                            
                            cropImgName=image_pre+'_N{}_crop{}.JPG'.format(boxIndex,j)
                            cropSaveXml = prefix_str.format(objectname,cropImgName,savePath + '/'+cropImgName,cropLength,cropLength) + head_str + suffix
                            cropedImg.save(savePath + '/' + cropImgName)
                            open(savePath + '/' + image_pre +'_N{}_crop{}.XMl'.format(boxIndex,j), 'w').write(cropSaveXml)
                        
                            cropedImg.save(SaveAllPath + cropImgName)
                            open(SaveAllPath + image_pre +'_N{}_crop{}.XMl'.format(boxIndex,j), 'w').write(cropSaveXml)
                        
                            #cropedImg.save(SaveTrainPath + cropImgName)
                            #open(SaveTrainPath + image_pre +'_{}_crop{}.XMl'.format(boxIndex,j), 'w').write(cropSaveXml) 


if __name__=="__main__":    
    CutNormalFlag = 0    
    if len(sys.argv) != 5 and len(sys.argv) != 6:
        print('Usage: python baseCropNum inputImagePath inputXmlPath outputPath (CutNormalFlag)')
        exit(1)
    elif len(sys.argv) == 5:
        baseCropNum = int(sys.argv[1])
        inputImagePath = sys.argv[2]
        inputXmlPath = sys.argv[3]
        outputPath = sys.argv[4] 
        CutNormalFlag = 1
    elif len(sys.argv) == 6:
        baseCropNum = int(sys.argv[1])
        inputImagePath = sys.argv[2]
        inputXmlPath = sys.argv[3]
        outputPath = sys.argv[4] 
        CutNormalFlag = 1 if int(sys.argv[5])!=0 else 0
        
    workPath = os.path.dirname(sys.argv[0])
    #inputPath = "D:/ADoWS/Samples/test"#'E:/myWork/clear/20181115412/20181115/1019/1/1'
    #outputPath = "D:/ADoWS/Samples/output"#'E:/myWork/clear/20181115412/20181115/1019/1/2'    
    
    if not os.path.exists(inputImagePath):
        print("Wrong ImagePath")
        exit(1)
    if not os.path.exists(inputXmlPath):
        print("Wrong XmlPath")
        exit(1)
    if not os.path.exists(outputPath):
        os.makedirs(outputPath)   
        
    ImgPath = inputImagePath
    AnnoPath = inputXmlPath
       
    #统计
    #baseCropNum = 10
    CropNum = ClassStatistics(AnnoPath,workPath,baseCropNum) 
    
    xmllist = os.listdir(AnnoPath)
    for xmlf in xmllist:
        xmlf_pre, ext = os.path.splitext(xmlf)
        if ext!=".XML" and ext!=".xml":
            continue
    
        #首先判断xml与JPG是否同名
        if os.path.exists(ImgPath + xmlf_pre + ".JPG"):
            image_pre = xmlf_pre 
            print(image_pre)
        else:
            image_pre = FindImagePreAcorrdingXMLPre(xmlf_pre)
        
        image = image_pre + ".JPG" 
        imageFullpath = ImgPath + image
    
        xmlFullpath = AnnoPath + xmlf
        CutFromHRImgByXml(xmlFullpath,imageFullpath,outputPath,640,CropNum,CutNormalFlag)
