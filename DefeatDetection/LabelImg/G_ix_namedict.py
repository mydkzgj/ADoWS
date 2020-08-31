# -*- coding: utf-8 -*-
"""
Created on Wed May 22 14:02:39 2019

@author: cjy
"""

import os

def Generate_img_xml_namedict(inputPath):
    imgPath = os.path.join(inputPath,"org")
    xmlPath = os.path.join(inputPath,"xml")
    
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
            
    fb.close()
    
if __name__ == "__main__":
    inputPath = r"D:\myWork\clear\20181115412\20181115\1019\1"
    Generate_img_xml_namedict(inputPath)
            