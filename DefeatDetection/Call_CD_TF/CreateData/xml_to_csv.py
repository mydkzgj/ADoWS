# -*- coding: utf-8 -*-

"""

Created on Tue Jan 16 00:52:02 2018



@author: Xiang Guo

"""
"""

Usage:

  # From tensorflow/models/

  # Create train csv:

  python xml_to_csv.py --xml_input=xmlData  --output_path=train_labels.csv

  # Create test csv:

  python generate_tfrecord.py --xml_input=xmlData  --output_path=test_labels.csv

"""
#python xml_to_csv.py --xml_input=D:/abcd/cuts/All  --output_path=D:\abcd\cuts\All/1/train_labels.csv
#python xml_to_csv.py D:/abcd/cuts/All  D:\abcd\cuts\All/1/train_labels.csv
import sys

import os

import glob

import pandas as pd

import xml.etree.ElementTree as ET



import random

'''
from tensorflow import app 

flags = app.flags

flags.DEFINE_string('xml_input', '', 'Path to the XML input')

#flags.DEFINE_string('images_input', '', 'Path to the Images(.jpg) input')

flags.DEFINE_string('output_path', '', 'Path to output CSV')

FLAGS = flags.FLAGS

#os.chdir(FLAGS.xml_input)
'''

def xml_to_csv_byName(path,outputPath,class_dict):

    xml_list = []

    xfile_List=glob.glob(path + '/*.xml')
    random.shuffle(xfile_List)
    #for xml_file in glob.glob(path + '/*.xml'):
    for xml_file in xfile_List:
        
        tree = ET.parse(xml_file)

        root = tree.getroot()

        for member in root.findall('object'):

            value = (root.find('filename').text,

                     int(root.find('size')[0].text),

                     int(root.find('size')[1].text),

                     member[0].text,

                     int(member[4][0].text),

                     int(member[4][1].text),

                     int(member[4][2].text),

                     int(member[4][3].text)

                     )
            #新增
            if class_dict.get(member[0].text) != None:
                xml_list.append(value)

    column_name = ['filename', 'width', 'height', 'class', 'xmin', 'ymin', 'xmax', 'ymax']

    xml_df = pd.DataFrame(xml_list, columns=column_name)
    
    xml_df.to_csv(outputPath, index=None)
    
    print('Successfully converted xml to csv.')

    return xml_df



def xml_to_csv(path,outputPath):

    xml_list = []

    xfile_List=glob.glob(path + '/*.xml')
    random.shuffle(xfile_List)
    #for xml_file in glob.glob(path + '/*.xml'):
    for xml_file in xfile_List:
        
        tree = ET.parse(xml_file)

        root = tree.getroot()

        for member in root.findall('object'):

            value = (root.find('filename').text,

                     int(root.find('size')[0].text),

                     int(root.find('size')[1].text),

                     member[0].text,

                     int(member[4][0].text),

                     int(member[4][1].text),

                     int(member[4][2].text),

                     int(member[4][3].text)

                     )

            xml_list.append(value)

    column_name = ['filename', 'width', 'height', 'class', 'xmin', 'ymin', 'xmax', 'ymax']

    xml_df = pd.DataFrame(xml_list, columns=column_name)
    
    xml_df.to_csv(outputPath, index=None)
    
    print('Successfully converted xml to csv.')

    return xml_df




def main():
    #设定命令行参数个数
    xmlsPath = ""
    outputPath = ""
    #print(sys.argv)
    if len(sys.argv) != 3:
        print('Usage: python inputPath outputPath')
        exit(1)
    else:
        xmlsPath = sys.argv[1]
        outputPath = sys.argv[2]
    xml_df = xml_to_csv(xmlsPath,outputPath)  
    
if __name__ == "__main__":
    main()