# -*- coding: utf-8 -*-
"""
Created on Thu Nov 29 16:34:09 2018

@author: cjy
"""

from xml.dom.minidom import Document
from xml.dom.minidom import parse
import numpy as np
import cv2 as cv


def RectFusion(Rect1,Rect2):
    x1= min(Rect1[0],Rect2[0])
    y1= min(Rect1[1],Rect2[1])
    x2= max(Rect1[2],Rect2[2])
    y2= max(Rect1[3],Rect2[3])
    Rect =[x1,y1,x2,y2]
    return Rect

#使用RectFusionOnce3  记录score
def SingleXmlRectFusion(xmlPath, maskFileName=None, useMaskFlag=0):
    DOMTree = parse(xmlPath)      
    annotation = DOMTree.documentElement    
 
    #得到xml的一些基本信息
    folder_list = annotation.getElementsByTagName('folder')
    folder=folder_list[0].childNodes[0].data
    filename_list = annotation.getElementsByTagName('filename')
    filename=filename_list[0].childNodes[0].data
    path_list = annotation.getElementsByTagName('path')
    path = path_list[0].childNodes[0].data
    width_list = annotation.getElementsByTagName('width')
    width = width_list[0].childNodes[0].data
    height_list = annotation.getElementsByTagName('height')
    height=height_list[0].childNodes[0].data
    depth_list = annotation.getElementsByTagName('depth')
    depth=depth_list[0].childNodes[0].data
    
    BasicInformation=[folder,filename,path,width,height,depth]    

    #得到类别列表namelist和检测框列表bndlist
    name_list = annotation.getElementsByTagName('name')
    NameList = []
    for Name in name_list:
        NameList.append(Name.childNodes[0].data)
    
    bndbox = annotation.getElementsByTagName('bndbox')
    RectList = []    
    #遍历所有检测框,将其对应的x1,y1,x2,y2存入RectList中
    for boxIndex in range(0, len(bndbox)): 
        x1_list = bndbox[boxIndex].getElementsByTagName('xmin')  # 寻找有着给定标签名的所有的元素
        x1 = int(x1_list[0].childNodes[0].data)
        y1_list = bndbox[boxIndex].getElementsByTagName('ymin')
        y1 = int(y1_list[0].childNodes[0].data)
        x2_list = bndbox[boxIndex].getElementsByTagName('xmax')
        x2 = int(x2_list[0].childNodes[0].data)
        y2_list = bndbox[boxIndex].getElementsByTagName('ymax')
        y2 = int(y2_list[0].childNodes[0].data)        
        RectList.append([x1,y1,x2,y2])
        
    score_list = annotation.getElementsByTagName('score')
    ScoreList = []
    for Score in score_list:
        ScoreList.append(Score.childNodes[0].data)

    if useMaskFlag == 1:  #使用Mask进行二次筛选
        if maskFileName is not None:
            RectList, NameList, ScoreList = screenBBoxByMask(RectList, NameList, ScoreList, maskFileName,)

    OverlapNumList = [1] * len(RectList)
        
    NewRectList = []
    NewRectNameList = []
    NewScoreList = []
    NewOverlapNumList = []
    
    Last_Length = -1
    while(len(NewRectList)!=Last_Length):
        #print("RectList",len(RectList))
        Last_Length = len(NewRectList)
        # 此处可以选择合并方式
        [NewRectList,NewRectNameList,NewScoreList,NewOverlapNumList]=RectFusionOnce4(RectList,NameList,ScoreList,OverlapNumList,int(BasicInformation[3]),int(BasicInformation[4]))
        RectList = NewRectList
        NameList = NewRectNameList
        ScoreList = NewScoreList
        OverlapNumList = NewOverlapNumList

    # 依据重叠的框个数进行筛选
    """
    total_num = len(NewRectList)
    for i, ONum in enumerate(reversed(NewOverlapNumList)):
        if ONum < 2:
            index = total_num - i - 1
            NewRectList.pop(index)
            NewRectNameList.pop(index)
            NewScoreList.pop(index)
            NewOverlapNumList.pop(index)
    """

    # 再次使用窗户mask进行筛选
    """
    if useMaskFlag == 1:  #使用Mask进行二次筛选
        if maskFileName is not None:
            NewRectList, NewRectNameList, NewScoreList = screenBBoxByMask(NewRectList, NewRectNameList, NewScoreList, maskFileName,)
    #"""
        
    outputXmlPath =xmlPath
    RectWrite(NewRectList,NewRectNameList,NewScoreList,BasicInformation,outputXmlPath)
    #print(NewOverlapNumList)
    #print(NewScoreList)




def screenBBoxByMask(RectList, NameList, ScoreList, maskFileName):
    NRectList = []
    NNameList = []
    NScoreList = []

    mask = cv.imread(maskFileName, cv.IMREAD_GRAYSCALE)
    ret, mask = cv.threshold(mask, 128, 255, cv.THRESH_BINARY)
    # 将墙体区域（白色）扩展——膨胀
    kernel = np.ones((20, 20), np.uint8)
    mask = cv.dilate(mask, kernel)  # 膨胀dilate

    for index, Rect in enumerate(RectList):
        x1 = Rect[0]
        y1 = Rect[1]
        x2 = Rect[2]
        y2 = Rect[3]

        num_split = 5  # bbox几等分采样
        candidates = []
        dx = (x2 - x1) / num_split
        dy = (y2 - y1) / num_split

        for i in range(num_split):
            for j in range(num_split):
                candidates.append([int(y1+i*dy), int(x1+j*dx)])

        no_inter = 1
        for point in candidates:
            if mask[point[0], point[1]] == 0:
                no_inter = 0
                break

        if no_inter == 1:
            NRectList.append(RectList[index])
            NNameList.append(NameList[index])
            NScoreList.append(ScoreList[index])

    return NRectList, NNameList, NScoreList


#Rect融合算法（遍历一次）  版本一：只要矩形框有重叠，就合并他们
def RectFusionOnce(RectList,NameList):
    NewRectList = []
    NewRectNameList = []
    while(len(RectList) != 0):           
        NewRect = RectList[0]
        NewRectName = NameList[0]
        RectList.pop(0)
        NameList.pop(0)
        #判断每一个框Rect是否与NewRectList中的Rect 
        #for R_index,Rect in enumerate(RectList): 
        R_index = -1
        while(R_index < len(RectList)-1):            
            R_index =R_index + 1            
            Rect = RectList[R_index]            
            if(NewRectName != NameList[R_index]):
                continue
            
            if(Rect[0]>=NewRect[0] and Rect[0]<=NewRect[2] and Rect[1]>=NewRect[1] and Rect[1]<=NewRect[3]):
                NewRect=RectFusion(Rect,NewRect)
                RectList.pop(R_index)
                NameList.pop(R_index)
                R_index = R_index -1
                continue
            if(Rect[0]>=NewRect[0] and Rect[0]<=NewRect[2] and Rect[3]>=NewRect[1] and Rect[3]<=NewRect[3]):
                NewRect=RectFusion(Rect,NewRect)
                RectList.pop(R_index)
                NameList.pop(R_index)
                R_index = R_index -1
                continue
            if(Rect[2]>=NewRect[0] and Rect[2]<=NewRect[2] and Rect[1]>=NewRect[1] and Rect[1]<=NewRect[3]):
                NewRect=RectFusion(Rect,NewRect)
                RectList.pop(R_index)
                NameList.pop(R_index)
                R_index = R_index -1
                continue
            if(Rect[2]>=NewRect[0] and Rect[2]<=NewRect[2] and Rect[3]>=NewRect[1] and Rect[3]<=NewRect[3]):
                NewRect=RectFusion(Rect,NewRect)
                RectList.pop(R_index)
                NameList.pop(R_index)
                R_index = R_index -1
                continue
            
            if(NewRect[0]>=Rect[0] and NewRect[0]<=Rect[2] and NewRect[1]>=Rect[1] and NewRect[1]<=Rect[3]):
                NewRect=RectFusion(Rect,NewRect)
                RectList.pop(R_index)
                NameList.pop(R_index)
                R_index = R_index -1
                continue
            if(NewRect[0]>=Rect[0] and NewRect[0]<=Rect[2] and NewRect[3]>=Rect[1] and NewRect[3]<=Rect[3]):
                NewRect=RectFusion(Rect,NewRect)
                RectList.pop(R_index)
                NameList.pop(R_index)
                R_index = R_index -1
                continue
            if(NewRect[2]>=Rect[0] and NewRect[2]<=Rect[2] and NewRect[1]>=Rect[1] and NewRect[1]<=Rect[3]):
                NewRect=RectFusion(Rect,NewRect)
                RectList.pop(R_index)
                NameList.pop(R_index)
                R_index = R_index -1
                continue
            if(NewRect[2]>=Rect[0] and NewRect[2]<=Rect[2] and NewRect[3]>=Rect[1] and NewRect[3]<=Rect[3]):
                NewRect=RectFusion(Rect,NewRect)
                RectList.pop(R_index)
                NameList.pop(R_index)
                R_index = R_index -1
                continue
        
        NewRectList.append(NewRect)
        NewRectNameList.append(NewRectName)
        
    return [NewRectList,NewRectNameList]


#Rect融合算法（遍历一次）  版本二：根据IOU等指标进行融合
def RectFusionOnce2(RectList,NameList,ImgWidth,ImgHeight):
    NewRectList = []
    NewRectNameList = []
    while(len(RectList) != 0):           
        NewRect = RectList[0]
        NewRectName = NameList[0]
        RectList.pop(0)
        NameList.pop(0)
        #判断每一个框Rect是否与NewRectList中的Rect 
        #for R_index,Rect in enumerate(RectList): 
        R_index = -1
        while(R_index < len(RectList)-1):            
            R_index =R_index + 1            
            Rect = RectList[R_index]            
            if(NewRectName != NameList[R_index]):
                continue
            
            [IOU,IOR1,IOR2] = countArg(Rect,NewRect,ImgWidth,ImgHeight)
            if IOU>=0.5 or IOR1>0.6 or IOR2>0.6:             
                NewRect=RectFusion(Rect,NewRect)
                RectList.pop(R_index)
                NameList.pop(R_index)
                R_index = R_index -1
                continue
           
        
        NewRectList.append(NewRect)
        NewRectNameList.append(NewRectName)
        
    return [NewRectList,NewRectNameList]

#Rect融合算法（遍历一次）  版本三：加入scores
def RectFusionOnce3(RectList,NameList,ScoreList,ImgWidth,ImgHeight):
    NewRectList = []
    NewRectNameList = []
    NewScoreList = []
    while(len(RectList) != 0):           
        NewRect = RectList[0]
        NewRectName = NameList[0]
        NewScore = ScoreList[0]
        RectList.pop(0)
        NameList.pop(0)
        ScoreList.pop(0)
        #判断每一个框Rect是否与NewRectList中的Rect 
        #for R_index,Rect in enumerate(RectList): 
        R_index = -1
        while(R_index < len(RectList)-1):            
            R_index =R_index + 1            
            Rect = RectList[R_index]   
            Score = ScoreList[R_index]
            if(NewRectName != NameList[R_index]):
                continue
            
            [IOU,IOR1,IOR2] = countArg(Rect,NewRect,ImgWidth,ImgHeight)
            if IOU>=0.5 or IOR1>0.6 or IOR2>0.6:             
                NewRect = RectFusion(Rect,NewRect)
                NewScore = max(NewScore,Score)
                RectList.pop(R_index)
                NameList.pop(R_index)
                ScoreList.pop(R_index)
                R_index = R_index -1
                continue
           
        
        NewRectList.append(NewRect)
        NewRectNameList.append(NewRectName)
        NewScoreList.append(NewScore)
        
    return [NewRectList,NewRectNameList,NewScoreList]

#Rect融合算法（遍历一次）  版本四：重叠就合并  本质同版本一
# CJY 2020.8.27
def RectFusionOnce4(RectList,NameList,ScoreList, OverlapNumList,ImgWidth,ImgHeight):
    NewRectList = []
    NewRectNameList = []
    NewScoreList = []
    NewOverlapNumList = []
    while(len(RectList) != 0):           
        NewRect = RectList[0]
        NewRectName = NameList[0]
        NewScore = ScoreList[0]
        NewOverlapNum = OverlapNumList[0]
        RectList.pop(0)
        NameList.pop(0)
        ScoreList.pop(0)
        OverlapNumList.pop(0)
        #判断每一个框Rect是否与NewRectList中的Rect 
        #for R_index,Rect in enumerate(RectList): 
        R_index = -1
        while(R_index < len(RectList)-1):            
            R_index =R_index + 1            
            Rect = RectList[R_index]   
            Score = ScoreList[R_index]
            ONum = OverlapNumList[R_index]
            if(NewRectName != NameList[R_index]):
                continue
            
            [IOU,IOR1,IOR2] = countArg(Rect,NewRect,ImgWidth,ImgHeight)
            if IOU>0:             
                NewRect = RectFusion(Rect,NewRect)
                NewScore = max(NewScore,Score)
                NewOverlapNum = NewOverlapNum + ONum
                RectList.pop(R_index)
                NameList.pop(R_index)
                ScoreList.pop(R_index)
                OverlapNumList.pop(R_index)
                R_index = R_index -1
                continue
        
        NewRectList.append(NewRect)
        NewRectNameList.append(NewRectName)
        NewScoreList.append(NewScore)
        NewOverlapNumList.append(NewOverlapNum)
        
    return [NewRectList,NewRectNameList,NewScoreList,NewOverlapNumList]

def countArg(Rect1,Rect2,ImgWidth,ImgHeight):
    area1=(Rect1[2]-Rect1[0]+1)*(Rect1[3]-Rect1[1]+1)
    area2=(Rect2[2]-Rect2[0]+1)*(Rect2[3]-Rect2[1]+1)
    
    center1 = [int((Rect1[0]+Rect1[2])/2),int((Rect1[1]+Rect1[3])/2)]
    
    canvas_width = 801
    canvas_r = int(canvas_width/2)
    
    canvas1 = np.zeros((canvas_width,canvas_width),dtype="uint8")    
    cv.rectangle(canvas1, (Rect1[0]-center1[0]+canvas_r,Rect1[1]-center1[1]+canvas_r),(Rect1[2]-center1[0]+canvas_r,Rect1[3]-center1[1]+canvas_r), 255, -1) 
    #c1=cv.resize(canvas1,(int(ImgWidth/10),int(ImgHeight/10)))
    #cv.imshow("1",c1)
    #cv.waitKey(0)
    
    canvas2 = np.zeros((canvas_width,canvas_width),dtype="uint8")    
    cv.rectangle(canvas2, (Rect2[0]-center1[0]+canvas_r,Rect2[1]-center1[1]+canvas_r),(Rect2[2]-center1[0]+canvas_r,Rect2[3]-center1[1]+canvas_r), 255, -1)
    
    iCanvas = canvas1&canvas2
    intersection = cv.countNonZero(iCanvas)
    
    union = area1+area2-intersection
    
    IOU = intersection/union
    IOR1 = intersection/area1
    IOR2 = intersection/area2  
    return [IOU,IOR1,IOR2]
    


#将合并好的Rect重新写入到xml文件中
def RectWrite(NewRectList,NewRectNameList,NewScoreList,BasicInformation,outputXmlPath)  :
    #创建xml文件头
    doc = Document()
    annotation = doc.createElement("annotation")
    doc.appendChild(annotation)
    folder = doc.createElement("folder")
    annotation.appendChild(folder)
    filename = doc.createElement("filename")
    annotation.appendChild(filename)
    path = doc.createElement("path")
    annotation.appendChild(path)
    source = doc.createElement("source")
    annotation.appendChild(source)
    database = doc.createElement("database")
    source.appendChild(database)
    size = doc.createElement("size")
    annotation.appendChild(size)
    width = doc.createElement("width")
    size.appendChild(width)
    height = doc.createElement("height")
    size.appendChild(height)
    depth = doc.createElement("depth")
    size.appendChild(depth)
    segmented = doc.createElement("segmented")
    annotation.appendChild(segmented)

    folder.appendChild(doc.createTextNode(BasicInformation[0]))
    filename.appendChild(doc.createTextNode(BasicInformation[1]))
    path.appendChild(doc.createTextNode(BasicInformation[2]))
    database.appendChild(doc.createTextNode("Unknown"))
    width.appendChild(doc.createTextNode(BasicInformation[3]))
    height.appendChild(doc.createTextNode(BasicInformation[4]))
    depth.appendChild(doc.createTextNode(BasicInformation[5]))
    segmented.appendChild(doc.createTextNode("0"))
    
    for NR_index,NewRect in enumerate(NewRectList):
        object = doc.createElement("object")
        annotation.appendChild(object)
        name = doc.createElement("name")
        object.appendChild(name)
        pose = doc.createElement("pose")
        object.appendChild(pose)
        truncated = doc.createElement("truncated")
        object.appendChild(truncated)
        difficult = doc.createElement("difficult")
        object.appendChild(difficult)
        bndbox = doc.createElement("bndbox")
        object.appendChild(bndbox)
        xmin = doc.createElement("xmin")
        bndbox.appendChild(xmin)
        ymin = doc.createElement("ymin")
        bndbox.appendChild(ymin)
        xmax = doc.createElement("xmax")
        bndbox.appendChild(xmax)
        ymax = doc.createElement("ymax")
        bndbox.appendChild(ymax) 
        score = doc.createElement("score")     
        object.appendChild(score) 
        
        name.appendChild(doc.createTextNode(NewRectNameList[NR_index]))
        pose.appendChild(doc.createTextNode("Unspecified"))
        truncated.appendChild(doc.createTextNode("0"))
        difficult.appendChild(doc.createTextNode("0"))
        xmin.appendChild(doc.createTextNode(str(NewRect[0])))
        ymin.appendChild(doc.createTextNode(str(NewRect[1])))
        xmax.appendChild(doc.createTextNode(str(NewRect[2])))
        ymax.appendChild(doc.createTextNode(str(NewRect[3])))
        score.appendChild(doc.createTextNode(NewScoreList[NR_index]))  
            
    #xml文件保存
    XMLfile = open(outputXmlPath, "w")
    XMLfile.write(doc.toprettyxml(indent="  "))
    XMLfile.close()  

if __name__ == '__main__':    
    SingleXmlRectFusion("E:/myWork/clear/20181115412/20181115/1019/1/xml_ns/DSC00160.XML")




            