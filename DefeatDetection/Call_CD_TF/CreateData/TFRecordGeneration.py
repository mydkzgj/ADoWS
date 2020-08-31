# -*- coding: utf-8 -*-
"""
Created on Sat Dec 15 19:52:50 2018

@author: cjy
"""



"""

Usage:

  # Using Xml Create TFRecord data for detection:

  python generate_tfrecord.py --xmls_input=data/xml  --images_input=imagesData --output_path=output  --output_name

  #for example:
  
  python D:/ADoWS/Code/TFRecordGeneration/ForDetection/TFRecordGeneration.py --xmls_input=E:/ProjectData/Samples/Detection/done/test_add_normal --images_input=E:/ProjectData/Samples/Detection/done/test_add_normal --output_path=E:/ProjectData/Samples/Detection/done/test_add_normal  --output_name=test  

  #Note:

  本程序将原始的两步：1.根据xml生成csv （xml_to_csv.py）2.根据csv和images生成TFRecord文件  
  以调用xml_to_csv中程序的方式，合并为一步。
  本程序会随机打乱文件的顺序，且只用于配有xml文件的检测任务。
  
  调用脚本时，tfRecord_label_map.pbtxt和xml_to_csv.py必须放在同一目录下。
  修改tfRecord_label_map.pbtxt的内容可以改变种类和标签值。

"""



import os

import sys

import io

import pandas as pd

import tensorflow as tf

import random

from PIL import Image

from object_detection.utils import dataset_util

from collections import namedtuple, OrderedDict

from object_detection.utils import label_map_util

import xml_to_csv as xtc

flags = tf.app.flags

flags.DEFINE_string('xmls_input', '', 'Path to the XMLs input')

flags.DEFINE_string('images_input', '', 'Path to the Images(.jpg) input')

flags.DEFINE_string('output_path', '', 'Path to output TFRecord')

flags.DEFINE_string('output_name', '', 'the name of TFRecord')

FLAGS = flags.FLAGS

os.chdir(FLAGS.images_input)



# TO-DO replace this with label map

def class_text_to_int(row_label):
    return cate_dict[row_label]
    '''
    if row_label == 'break':

        return 1
    elif row_label == 'crack':
        
        return 1
    
    elif row_label == 'rebar':
        
        return 1
    elif row_label == 'sundries':
        
        return 1
    elif row_label == 'suspect':
        
        return 1

    #elif row_label == 'vehicle':

    #    return 2

    else:

        None
    '''




def split(df, group):

    data = namedtuple('data', ['filename', 'object'])

    gb = df.groupby(group)

    return [data(filename, gb.get_group(x)) for filename, x in zip(gb.groups.keys(), gb.groups)]





def create_tf_example(group, path):

    with tf.gfile.GFile(os.path.join(path, '{}'.format(group.filename)), 'rb') as fid:

        encoded_jpg = fid.read()

    encoded_jpg_io = io.BytesIO(encoded_jpg)

    image = Image.open(encoded_jpg_io)

    width, height = image.size



    filename = group.filename.encode('utf8')

    image_format = b'jpg'

    xmins = []

    xmaxs = []

    ymins = []

    ymaxs = []

    classes_text = []

    classes = []



    for index, row in group.object.iterrows():
        if cate_dict.get(row['class']) == "normal":    #CJY at 2019.4.9  如果目标为normal，就不记录他的检测框
            continue
        
        if cate_dict.get(row['class']) == None:    #CJY at 2019.4.9  如果目标不在dict里，就不记录他的检测框
            continue

        xmins.append(row['xmin'] / width)

        xmaxs.append(row['xmax'] / width)

        ymins.append(row['ymin'] / height)

        ymaxs.append(row['ymax'] / height)

        classes_text.append(row['class'].encode('utf8'))  
        #classes_text.append('abnormity'.encode('utf8'))

        classes.append(class_text_to_int(row['class']))
    

    tf_example = tf.train.Example(features=tf.train.Features(feature={

        'image/height': dataset_util.int64_feature(height),

        'image/width': dataset_util.int64_feature(width),

        'image/filename': dataset_util.bytes_feature(filename),

        'image/source_id': dataset_util.bytes_feature(filename),

        'image/encoded': dataset_util.bytes_feature(encoded_jpg),

        'image/format': dataset_util.bytes_feature(image_format),

        'image/object/bbox/xmin': dataset_util.float_list_feature(xmins),

        'image/object/bbox/xmax': dataset_util.float_list_feature(xmaxs),

        'image/object/bbox/ymin': dataset_util.float_list_feature(ymins),

        'image/object/bbox/ymax': dataset_util.float_list_feature(ymaxs),

        'image/object/class/text': dataset_util.bytes_list_feature(classes_text),

        'image/object/class/label': dataset_util.int64_list_feature(classes),

    }))

    return tf_example




workPath = os.path.dirname(sys.argv[0])
# 获取类别及其对应标号
NUM_CLASSES = 100
PATH_TO_LABELS = os.path.join(workPath,"tfRecord_label_map.pbtxt")
print(PATH_TO_LABELS)
label_map = label_map_util.load_labelmap(PATH_TO_LABELS)
categories = label_map_util.convert_label_map_to_categories(label_map, max_num_classes=NUM_CLASSES, use_display_name=True)
cate_dict = dict()
for cateIndex in range(len(categories)):
    cate_dict[categories[cateIndex]["name"]]=categories[cateIndex]["id"]
 

def main(_):   

    
    if not os.path.exists(FLAGS.output_path):
        os.makedirs(FLAGS.output_path) 
    # 先运行 xml to csv
    csv_input = os.path.join(FLAGS.output_path, FLAGS.output_name + ".csv")
    print(csv_input)
    xtc.xml_to_csv_byName(FLAGS.xmls_input,csv_input,cate_dict)   
    
    outputFilename = os.path.join(FLAGS.output_path, FLAGS.output_name + ".record")
    
    writer = tf.python_io.TFRecordWriter(outputFilename)

    #path = os.path.join(os.getcwd(), 'images')
    path = os.path.join(FLAGS.images_input)

    examples = pd.read_csv(csv_input)

    grouped = split(examples, 'filename')
    
    # 打乱顺序
    random.shuffle(grouped)

    for group in grouped:

        tf_example = create_tf_example(group, path)

        writer.write(tf_example.SerializeToString())

    writer.close()    

    print('Successfully created the TFRecords: {}'.format(outputFilename))

if __name__ == '__main__':
    tf.app.run()