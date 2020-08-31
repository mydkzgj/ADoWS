# -*- coding: utf-8 -*-
"""
Created on Tue Jan 15 09:27:25 2019

@author: nnir
"""
import sys
import os
import shutil


XmlInputPath = ""
XmlOutputPath = ""

if len(sys.argv) != 3:
    print('Usage: python input_name output_name')
    exit(1)
elif len(sys.argv) == 3:
    XmlInputPath = sys.argv[1]
    XmlOutputPath = sys.argv[2] 
    
#XmlInputPath = "D:\\myWork\\clear\\20181115412\\20181115\\1019\\10\\xml"
#XmlOutputPath = "D:\\myWork\\clear\\20181115412\\20181115\\1019\\10\\xmlWs"

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
    

def main():
   
    if os.path.exists(XmlInputPath)!=True:
        exit(1)
    if os.path.exists(XmlOutputPath)!=True:
        os.mkdir(XmlOutputPath)
    
    xmllist = os.listdir(XmlInputPath)
    for xmlf in xmllist:
        xmlf_pre, ext = os.path.splitext(xmlf)
        if ext!=".XML" and ext!=".xml":
            continue
        image_pre = FindImagePreAcorrdingXMLPre(xmlf_pre)
        xmlf_ns_pre = image_pre
        xmlf_ns = xmlf_ns_pre + ".XML"
        
        shutil.copy(XmlInputPath+"/"+xmlf,XmlOutputPath+"/"+xmlf_ns)
        
        #XRF.SingleXmlRectFusion(XmlOutputPath+"/"+xmlf_ns)
        
if __name__ == "__main__":
    main()
        
    