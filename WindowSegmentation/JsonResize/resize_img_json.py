# -*- coding: utf-8 -*-
"""
Created on Fri Mar  1 11:27:38 2019

@author: admin
"""
"""Resize img and json.

Please note that this tool only applies to labelme's annotations(json file).

Example usage:
    python3 create_tf_record.py \
        --images_dir=your absolute path to read images.
        --annotations_json_dir=your path to annotaion json files.
        --label_map_path=your path to label_map.pbtxt
        --output_path=your path to write .record.
"""
import os
import json
from PIL import Image

ImagePath = r"D:\ADoWS\Samples\WindowSegmentation\source\database\original"
JsonPath = r"D:\ADoWS\Samples\WindowSegmentation\source\database\original"
OutputPath = r"D:\ADoWS\Samples\WindowSegmentation\source\database\resized"
ratioW=0.25
ratioH=0.25


import base64
import io
import numpy as np

def img_b64_to_arr(img_b64):
    f = io.BytesIO()
    f.write(base64.b64decode(img_b64))
    img_arr = np.array(Image.open(f))
    return img_arr

def resizeJson(InputJsonName,OutputJsonName,ratioW,ratioH,):
    fb = open(InputJsonName,'r')
    dicts = json.load(fb)
    fb.close()
    
    shapes = dicts["shapes"]
    imageH = dicts["imageHeight"]
    imageW = dicts["imageWidth"]
    dicts["imageHeight"] = str(int(int(imageH)*ratioH))
    dicts["imageWidth"] = str(int(int(imageW)*ratioW))

    '''
    img = Image.open("D:/tensorflow/test/DSC04193.JPG") 
    rW = int(img.size[0]*ratioW)
    rH = int(img.size[1]*ratioH)
    img1 = img.resize((rW,rH))
    dicts["imageData"] = base64.b64encode(img1).decode('utf-8')
    '''
    #CJY at 2020.8.24
    #修改json中的img文件
    dicts["imageData"] = None#base64.b64encode(img).decode('utf-8')

    for shape in shapes:
        points = shape["points"]
        for point in points:
            point[0] = int(point[0]*ratioW)
            point[1] = int(point[1]*ratioH)
    
    fb = open(OutputJsonName,'w')
    fb.write(json.dumps(dicts,indent=2))
    fb.close()

def rij(ImagePath,JsonPath,OutputPath,ratioW,ratioH):    
    if os.path.exists(OutputPath)!=True:
        os.mkdir(OutputPath)
    
    images = os.listdir(ImagePath)
    for image in images:
        image_pre, ext = os.path.splitext(image)  
        if ext !=".JPG" and ext !=".jpg":
            continue
        print("processing image: {}".format(image))
        InputImageName = os.path.join(ImagePath,image)
        OutputImageName = os.path.join(OutputPath,image)
        img = Image.open(InputImageName) 
        rW = int(img.size[0]*ratioW)
        rH = int(img.size[1]*ratioH)
        img1 = img.resize((rW,rH))
        img1.save(OutputImageName)  #只进行质量压缩
        
    jsons = os.listdir(JsonPath)
    for jsonf in jsons:
        json_pre, ext = os.path.splitext(jsonf)  
        if ext !=".json":
            continue
        print("processing json: {}".format(jsonf))
        InputJsonName = os.path.join(JsonPath,jsonf)
        OutputJsonName = os.path.join(OutputPath,jsonf)
        resizeJson(InputJsonName,OutputJsonName,ratioW,ratioH)


if __name__ == "__main__":
    rij(ImagePath,JsonPath,OutputPath,ratioW,ratioH)