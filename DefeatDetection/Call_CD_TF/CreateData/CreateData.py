# -*- coding: utf-8 -*-
"""
Created on Wed May  8 16:10:06 2019

@author: admin
"""

import os
import sys
import shutil
import GenerateNewXml as GNX
import CutsGeneration as CG

'''
本程序集合了三个子程序
1.GenerateNewXml  标签拓展
2.CutsGeneration  切片
3.TFRecordGeneration  TFRecord样本生成

example:
python CreateData.py D:/ADoWS/Samples/Detection/work/train/org D:/ADoWS/Samples/Detection/work/train/xml 0.6 20 1 train D:/ADoWS/Samples/Detection/work/train/data 0

输入 inputImagePath，inputXmlPath
     
     1.extensionRatio
     2.baseCropNum，CutNormalFlag
     3.outputName
     outputPath
    
'''

if __name__=="__main__": 
    if len(sys.argv) != 9:
        print('Usage: python inputImagePath inputXmlPath extensionRatio baseCropNum CutNormalFlag outputName outputPath IgnorePrcsImgTxt')
        exit(1)
    elif len(sys.argv) == 9:    
        workPath = os.path.dirname(sys.argv[0])
        inputImagePath = sys.argv[1]
        inputXmlPath = sys.argv[2]
        extensionRatio = float(sys.argv[3])
        baseCropNum = int(sys.argv[4])        
        CutNormalFlag = 1 if int(sys.argv[5])!=0 else 0
        outputName = sys.argv[6] 
        outputPath = sys.argv[7]
        IgnorePrcsImgTxt = int(sys.argv[8])
        
    if not os.path.exists(inputImagePath):
        print("Wrong ImagePath")
        exit(1)
    if not os.path.exists(inputXmlPath):
        print("Wrong XmlPath")
        exit(1)
    if not os.path.exists(outputPath):
        os.makedirs(outputPath)     
    
    #文件夹流程   xml —— xmlE_Processing —— cut —— xmlE —— tfrecord
    outputXmlPath = os.path.join(outputPath,"xmlE_Processing")
    outputCutPath = os.path.join(outputPath,"cut")
    outputTFRecordPath = os.path.join(outputPath,"tfrecord")    
    if not os.path.exists(outputPath):
        os.makedirs(outputPath)  
    if not os.path.exists(outputXmlPath):
        os.makedirs(outputXmlPath)  
    if not os.path.exists(outputCutPath):
        os.makedirs(outputCutPath)  
    if not os.path.exists(outputTFRecordPath):
        os.makedirs(outputTFRecordPath)  
        
    outputXmlEPath = os.path.join(outputPath,"xmlE")
    if not os.path.exists(outputXmlEPath):
        os.makedirs(outputXmlEPath)  
    
    #依次调用子程序
    
    #1.GenerateNewXml  
    if IgnorePrcsImgTxt == 1:
        GNX.ExtensionNewXmls(inputXmlPath,outputXmlPath,extensionRatio)   #如果不考虑processedImgTxt 就把最后的outputPath删掉
    else:
        GNX.ExtensionNewXmls(inputXmlPath,outputXmlPath,extensionRatio,outputPath)   #如果不考虑processedImgTxt 就把最后的outputPath删掉
    
    #2.CutsGeneration
    ImgPath = inputImagePath+"/"
    AnnoPath = outputXmlPath+"/"
    CropNum = CG.ClassStatistics(AnnoPath,workPath,baseCropNum) 
    
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
            image_pre = CG.FindImagePreAcorrdingXMLPre(xmlf_pre)
        
        image = image_pre + ".JPG" 
        imageFullpath = ImgPath + image
    
        xmlFullpath = AnnoPath + xmlf
        CG.CutFromHRImgByXml(xmlFullpath,imageFullpath,outputCutPath,640,CropNum,CutNormalFlag)
        
        #CJY at 2019.10.12   读取processImgRecord.txt中的记录，不对处理过的图片进行处理
        #将xmlE_new移到xmlE中
        srcpath = os.path.join(outputXmlPath, xmlf)
        dirpath = os.path.join(outputXmlEPath, xmlf)
        if os.path.exists(dirpath)==True:
            os.remove(dirpath)
            shutil.move(srcpath,outputXmlEPath)
        else:
            shutil.move(srcpath,outputXmlEPath)    
        #写入processedImgRecord.txt
        f = open(os.path.join(outputPath, "processedImgRecord.txt"),"a")        
        f.write(xmlf+"\n")
        f.close()
        
    shutil.rmtree(outputXmlPath)
    print("Cut Finished!")
    
    #3.TFRecordGeneration
    if os.path.exists(os.path.join(workPath, "TFRecordGeneration.exe")) == True:
        cmdline = os.path.join(workPath,"TFRecordGeneration.exe")+" --xmls_input="+os.path.join(outputCutPath,"Sets","All")+" --images_input="+os.path.join(outputCutPath,"Sets","All")+" --output_path="+outputTFRecordPath+" --output_name="+outputName
    elif os.path.exists(os.path.join(workPath, "TFRecordGeneration.py")) == True:
        cmdline = "python "+os.path.join(workPath,"TFRecordGeneration.py")+" --xmls_input="+os.path.join(outputCutPath,"Sets","All")+" --images_input="+os.path.join(outputCutPath,"Sets","All")+" --output_path="+outputTFRecordPath+" --output_name="+outputName
    else:
        raise Exception("There is no sub program named TFRecordGeneration")
    os.system(cmdline)
    
    print("Creation Finished!")
    