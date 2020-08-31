# -*- coding: utf-8 -*-
"""
Created on Mon Apr 22 21:40:37 2019

@author: admin
"""
from xml.dom.minidom import Document
from xml.dom.minidom import parse
import os

def ExtensionNewXmlForSingleImg(truthXmlFullPath,outputXmlFullPath,extensionRatio):    
    truthDOMTree = parse(truthXmlFullPath)      
    TruthAnnotation = truthDOMTree.documentElement  
    
    #先把中文都改了
    folder_dom = TruthAnnotation.getElementsByTagName('folder')
    #print(folder_dom[0].firstChild.data)
    folder_dom[0].firstChild.data = 'unkown'
    fn_dom = TruthAnnotation.getElementsByTagName('filename')
    #print(fn_dom[0].firstChild.data)
    fn_dom[0].firstChild.data = 'unkown'
    path_dom = TruthAnnotation.getElementsByTagName('path')
    #print(path_dom[0].firstChild.data)
    path_dom[0].firstChild.data = 'unkown'
    
    truthname_list = TruthAnnotation.getElementsByTagName('name')
    NameList = []
    for Name in truthname_list:
        NameList.append(Name.childNodes[0].data)
    
    width = int(TruthAnnotation.getElementsByTagName('width')[0].childNodes[0].data)
    height = int(TruthAnnotation.getElementsByTagName('height')[0].childNodes[0].data)
    
    TruthRectList = []    
    truthbndbox = TruthAnnotation.getElementsByTagName('bndbox')    
    #遍历所有检测框,将其对应的x1,y1,x2,y2存入RectList中
    for boxIndex in range(0, len(truthbndbox)): 
        x1_list = truthbndbox[boxIndex].getElementsByTagName('xmin')  # 寻找有着给定标签名的所有的元素
        x1 = int(x1_list[0].childNodes[0].data)
        y1_list = truthbndbox[boxIndex].getElementsByTagName('ymin')
        y1 = int(y1_list[0].childNodes[0].data)
        x2_list = truthbndbox[boxIndex].getElementsByTagName('xmax')
        x2 = int(x2_list[0].childNodes[0].data)
        y2_list = truthbndbox[boxIndex].getElementsByTagName('ymax')
        y2 = int(y2_list[0].childNodes[0].data)        
        TruthRectList.append([x1,y1,x2,y2])
        
        w = x2 - x1
        h = y2 - y1
        w_e = int(w*extensionRatio/2)+1
        h_e = int(h*extensionRatio/2)+1


        if NameList[boxIndex] == "crack":
            if w <= h:
                x1_list[0].childNodes[0].data = str(max(2,x1 - w_e))            
                x2_list[0].childNodes[0].data = str(min(width - 2,x2 + w_e))    
            else:
                y1_list[0].childNodes[0].data = str(max(2,y1 - h_e))            
                y2_list[0].childNodes[0].data = str(min(height - 2, y2 + h_e))
            continue

        if max(w, h) > 100:  #大目标就不扩增了， 小目标扩展尺寸
            continue

        x1_list[0].childNodes[0].data = str(max(2,x1 - w_e))
        y1_list[0].childNodes[0].data = str(max(2,y1 - h_e)) 
        x2_list[0].childNodes[0].data = str(min(width - 2,x2 + w_e))
        y2_list[0].childNodes[0].data = str(min(height - 2,y2 + h_e))       


    #保存
    with open(os.path.join(outputXmlFullPath),'w') as fh:
        truthDOMTree.writexml(fh)
        print("写入"+outputXmlFullPath+"OK!")
        
        
def ExtensionNewXmls(truthXmlsPath,outputPath,extensionRatio, readRecordTxtPath = None):
    if not os.path.exists(outputPath):
        os.makedirs(outputPath) 
    truthxmllist = os.listdir(truthXmlsPath)
    
    #CJY at 2019.10.12   读取processImgRecord.txt中的记录，不对处理过的图片进行处理
    if readRecordTxtPath != None:
        recordTxt = os.path.join(readRecordTxtPath, "processedImgRecord.txt")
        if os.path.exists(recordTxt) == True:
            f = open(recordTxt)
            for line in f:
                line = line.strip("\n")
                if line in truthxmllist:
                    truthxmllist.remove(line)    
    
    for truthxml in truthxmllist:
        truthxml_pre, ext = os.path.splitext(truthxml)
        if ext!=".XML" and ext!=".xml":
            continue
        
        truthXmlFullPath = os.path.join(truthXmlsPath,truthxml)
        outputXmlFullPath = os.path.join(outputPath,truthxml)
        
        ExtensionNewXmlForSingleImg(truthXmlFullPath,outputXmlFullPath,extensionRatio)
        
        
if __name__ == "__main__":
    truthXmlsPath1 = "D:/ADoWS/Samples/Detection/sets/train/xml_o"
    outputPath1 = "D:/ADoWS/Samples/Detection/sets/train/xml"
    truthXmlsPath2 = "D:/ADoWS/Samples/Detection/sets/val/xml_o"
    outputPath2 = "D:/ADoWS/Samples/Detection/sets/val/xml"
    truthXmlsPath3 = "D:/ADoWS/Samples/Detection/sets/test/xml_o"
    outputPath3 = "D:/ADoWS/Samples/Detection/sets/test/xml"
    extensionRatio = 0.6
    ExtensionNewXmls(truthXmlsPath1,outputPath1,extensionRatio)
    ExtensionNewXmls(truthXmlsPath2,outputPath2,extensionRatio)
    ExtensionNewXmls(truthXmlsPath3,outputPath3,extensionRatio)
    
    