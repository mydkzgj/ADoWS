# -*- coding: utf-8 -*-
"""
Created on Sat Mar  2 15:23:46 2019

@author: nnir
"""


import numpy as np
import os
#import six.moves.urllib as urllib
import sys
#import tarfile
import tensorflow as tf
#import zipfile

#from collections import defaultdict
#from io import StringIO
#from matplotlib import pyplot as plt
from PIL import Image

#from PIL import ImageDraw
#from PIL import ImageFont

#from xml.dom.minidom import Document

import datetime  #获取时间，计算程序执行时间

import shutil   #删除非空文件夹

#import XmlRectFusion
#import thumbGeneration as tG

import cv2
import Grow

# This is needed since the notebook is stored in the object_detection folder.
sys.path.append("..")

from object_detection.utils import ops as utils_ops

from distutils.version import StrictVersion
if StrictVersion(tf.__version__) < StrictVersion('1.9.0'):
  raise ImportError('Please upgrade your TensorFlow installation to v1.9.* or later!')

# This is needed to display the images.


from object_detection.utils import label_map_util

from object_detection.utils import visualization_utils as vis_util



 
def run_inference_for_single_image(image,sess,graph):
  # Get handles to input and output tensors
  with graph.as_default():
    ops = tf.get_default_graph().get_operations()
    all_tensor_names = {output.name for op in ops for output in op.outputs}
    tensor_dict = {}
    for key in ['num_detections', 'detection_boxes', 'detection_scores','detection_classes', 'detection_masks'      ]:
        tensor_name = key + ':0'
        if tensor_name in all_tensor_names:
          tensor_dict[key] = tf.get_default_graph().get_tensor_by_name(tensor_name)
    
    if 'detection_masks' in tensor_dict:
        # The following processing is only for single image
        detection_boxes = tf.squeeze(tensor_dict['detection_boxes'], [0])
        detection_masks = tf.squeeze(tensor_dict['detection_masks'], [0])
        # Reframe is required to translate mask from box coordinates to image coordinates and fit the image size.
        real_num_detection = tf.cast(tensor_dict['num_detections'][0], tf.int32)
        detection_boxes = tf.slice(detection_boxes, [0, 0], [real_num_detection, -1])
        detection_masks = tf.slice(detection_masks, [0, 0, 0], [real_num_detection, -1, -1])
        detection_masks_reframed = utils_ops.reframe_box_masks_to_image_masks(
            detection_masks, detection_boxes, image.shape[0], image.shape[1])
            #detection_masks, detection_boxes, image.size[1], image.size[0])
        detection_masks_reframed = tf.cast(
            tf.greater(detection_masks_reframed, 0.5), tf.uint8)
        # Follow the convention by adding back the batch dimension
        tensor_dict['detection_masks'] = tf.expand_dims(
            detection_masks_reframed, 0)
    image_tensor = tf.get_default_graph().get_tensor_by_name('image_tensor:0')

    # Run inference
    #start1=datetime.datetime.now()
    #start1Time=start1.strftime('%Y-%m-%d %H:%M:%S.%f')
    #print(start1Time)
      
    output_dict = sess.run(tensor_dict,
                             feed_dict={image_tensor: np.expand_dims(image, 0)})
                  
    #end1=datetime.datetime.now()
    #end1Time=end1.strftime('%Y-%m-%d %H:%M:%S.%f')
    #print(end1Time)
        
    #print('Running time: %s Seconds'%(end1-start1))
      
    #print(output_dict['detection_boxes']) 
    #print("after\n")
    
    # all outputs are float32 numpy arrays, so convert types as appropriate
    #aop=output_dict['detection_boxes'][2]
    output_dict['num_detections'] = int(output_dict['num_detections'][0])
    output_dict['detection_classes'] = output_dict[
          'detection_classes'][0].astype(np.uint8)
    output_dict['detection_boxes'] = output_dict['detection_boxes'][0]
    output_dict['detection_scores'] = output_dict['detection_scores'][0]
    if 'detection_masks' in output_dict:
        output_dict['detection_masks'] = output_dict['detection_masks'][0]
    return output_dict



def load_image_into_numpy_array(image):
    (im_width, im_height) = image.size
    return np.array(image.getdata()).reshape(
         (im_height, im_width, 3)).astype(np.uint8)



def run_inference_for_images(workPath,model_name,path_to_labels,inputPath,outputMASKpath = None,resizeRatio = 0.125,scoreThreshold = 0.5):
    print("正在检测，请勿关闭此窗口！否则，将退出检测！")    
    #起始时间记录
    start=datetime.datetime.now()
    startTime=start.strftime('%Y-%m-%d %H:%M:%S.%f')
    print("楼面预分割任务起始时间："+startTime)
    
    #准备需要的路径
    # What model to use.
    MODEL_NAME = model_name    
    # Path to frozen detection graph. This is the actual model that is used for the object detection.
    PATH_TO_CKPT = os.path.join(MODEL_NAME, 'frozen_inference_graph.pb')
    # List of the strings that is used to add correct label for each box.
    PATH_TO_LABELS = os.path.join(path_to_labels, 'label_map.pbtxt')
    
    # the Number of classes
    NUM_CLASSES = 10
    
    #载入图graph
    detection_graph = tf.Graph()
    with detection_graph.as_default():
        od_graph_def = tf.GraphDef()
        with tf.gfile.GFile(PATH_TO_CKPT, 'rb') as fid:
            serialized_graph = fid.read()
            od_graph_def.ParseFromString(serialized_graph)
            tf.import_graph_def(od_graph_def, name='')
            
    label_map = label_map_util.load_labelmap(PATH_TO_LABELS)
    #categories = label_map_util.convert_label_map_to_categories(label_map, max_num_classes=NUM_CLASSES, use_display_name=True)    
    #category_index = label_map_util.create_category_index(categories)    
  
    #创建临时文件夹
    TempPath = os.path.join(workPath,"Temp")    
    if os.path.exists(TempPath)==True:
        shutil.rmtree(TempPath)   #清空  
        os.mkdir(TempPath)
    else:
        os.mkdir(TempPath)
        
    if outputMASKpath == None:
        MaskPath = os.path.join(TempPath,"Mask")
    else:
        MaskPath = outputMASKpath
    if os.path.exists(MaskPath)!=True:
        #shutil.rmtree(MaskPath)   #清空  
        os.mkdir(MaskPath)     
    
    #计算待检测文件夹中有多少待检测文件
    num_files=0
    for file in os.listdir(inputPath):
        fname,ftype = os.path.splitext(file)
        if ftype==".JPG" or ftype==".jpg":
            num_files = num_files + 1      
    print("待检测文件夹中图像数量："+str(num_files))

    #detection_graph.as_default()
    with tf.Session(graph=detection_graph) as sess:
        file_index=0
        for file in os.listdir(inputPath):
            fname,ftype = os.path.splitext(file)
   
            if ftype!=".JPG" and ftype!=".jpg":
                continue        
            else:
                file_index=file_index+1
            
            if os.path.exists(os.path.join(MaskPath,file))==True:
                print("已检测过第%d图片：%s"%(file_index,file))
                continue
            
            print("检测第%d图片：%s"%(file_index,file))
            sPDstart=datetime.datetime.now()   #singlePicDetection
            sPDstartTime=sPDstart.strftime('%Y-%m-%d %H:%M:%S.%f')
            print("开始时间："+sPDstartTime)
            
            filepath = os.path.join(inputPath, file)               
            
            '''
            sCDstart=datetime.datetime.now()
            sCDstartTime=sCDstart.strftime('%Y-%m-%d %H:%M:%S.%f')
            print(sCDstartTime)          
            '''        
            #CJY  at  2019.7.11  为了防止图片损坏的情况，使用try except
            try:
                image = Image.open(filepath) 
            except(OSError, NameError):
                print('OSError, Path:',filepath)
                continue

            img_w = image.size[0]
            img_h = image.size[1]
            w = int(img_w*resizeRatio)
            h = int(img_h*resizeRatio)
            image = image.resize((w,h))
            
            # the array based representation of the image will be used later in order to prepare the
            # result image with boxes and labels on it.               
            image_np = load_image_into_numpy_array(image)   #最耗费时间 0.10s左右
                                
            # Expand dimensions since the model expects images to have shape: [1, None, None, 3]
            #image_np_expanded = np.expand_dims(image_np, axis=0)                
                 
            # Actual detection.        
            output_dict = run_inference_for_single_image(image_np, sess,detection_graph)
                
            '''
            # Visualization of the results of a detection.
            vis_util.visualize_boxes_and_labels_on_image_array(
                        image_np,
                        output_dict['detection_boxes'],
                        output_dict['detection_classes'],
                        output_dict['detection_scores'],
                        category_index,
                        instance_masks=output_dict.get('detection_masks'),
                        use_normalized_coordinates=True,
                        line_thickness=8)
            plt.figure(figsize=IMAGE_SIZE)
            plt.imshow(image_np)
            #print(output_dict['detection_boxes'])       '''
            
            #mask图像绘制与保存
            objectNum = 0
            mask_np=np.ones([h,w,3], dtype = np.uint8, order = 'C')*255  #创建空白掩膜画布
            for index,boxScore in enumerate(output_dict['detection_scores']):
                if boxScore>scoreThreshold:          
                    masks=output_dict.get('detection_masks')#output_dict["detection_masks"][index]
                    vis_util.draw_mask_on_image_array(mask_np,masks[index],"black",1.0)
                    objectNum = objectNum + 1
            
            mask_np = cv2.cvtColor(mask_np,cv2.COLOR_BGR2GRAY)
            
            #识别天空
            resizeRatio2 = 0.05
            image_gray = cv2.cvtColor(cv2.resize(image_np,(int(img_w*resizeRatio2),int(img_h*resizeRatio2))),cv2.COLOR_BGR2GRAY)  #resize中 写  宽、高

            seeds = [Grow.Point(0,0),Grow.Point(image_gray.shape[0]-1,0),Grow.Point(0,image_gray.shape[1]-1),Grow.Point(image_gray.shape[0]-1,image_gray.shape[1]-1)]

            SkyMask = Grow.regionGrow(image_gray,seeds,3)
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT,(5,5))
            SkyMask = cv2.morphologyEx(SkyMask,cv2.MORPH_CLOSE,kernel)    
            contours,hierarchy = cv2.findContours(SkyMask,cv2.RETR_TREE,cv2.CHAIN_APPROX_NONE)
            
            m=np.zeros(SkyMask.shape, dtype = np.uint8, order = 'C')  #创建黑色掩膜画布
            areaTH = int(SkyMask.shape[0]*SkyMask.shape[1]*0.1)
            for i in range(0,len(contours)):
                if cv2.contourArea(contours[i])>=areaTH:
                    cv2.drawContours(m,contours,i,255,-1)    
                    
            SkyMask = cv2.resize(m,(w,h))
            mask_np = (~SkyMask)&mask_np            
            
            #if (objectNum > 0):          
            im = Image.fromarray(mask_np)
            im = im.resize((img_w,img_h))
            im.save(os.path.join(MaskPath,file))
            #'''                
            
            '''
            sCDend=datetime.datetime.now()
            sCDendTime=sCDend.strftime('%Y-%m-%d %H:%M:%S.%f')
            print(sCDendTime)
            print('单张切片完成时间: %s Seconds'%(cend-cstart)) 
            '''
           
            '''
            #写入文件
            if os.path.exists(workPath + "Temp/temp.txt")==True:
                os.remove(workPath + "Temp/temp.txt")
            '''
            
            #4.生成指定成果
           
            
            #单张图像检测结束时间
            sPDend=datetime.datetime.now()
            sPDendTime=sPDend.strftime('%Y-%m-%d %H:%M:%S.%f')
            print("结束时间："+sPDendTime)
            print('单张图像分割时间: %s Seconds'%(sPDend-sPDstart))            
            
            #将信息记录在dTemp.txt中
            detailsLogfile=open(os.path.join(outputMASKpath,'dTemp.txt'),'a')  #TempPath
            detailsLogfile.write(fname+"\n")
            detailsLogfile.write("start:"+sPDstartTime+"\n")
            detailsLogfile.write("end:"+sPDendTime+"\n")
            detailsLogfile.write("segmentation useTime:%s"%(sPDend-sPDstart)+"\n")            
            detailsLogfile.close()
            
            #break
        
    #删除临时文件夹
    if os.path.exists(TempPath)==True:
        shutil.rmtree(TempPath)
    
    #写入标志位，是否完成对所有文件的检测
    #finishfile = open(os.path.join(workPath,'FinishFlag.txt'),'w') 
    #finishfile.write("1")
    #finishfile.close() 
    
    end=datetime.datetime.now()
    endTime=end.strftime('%Y-%m-%d %H:%M:%S.%f')
    print("楼面预分割任务结束时间："+endTime)
    print('楼面预分割任务运行时间: %s Seconds'%(end-start))

def main():
    #检查是否有其他会话正在运行
    #if 'session' in locals() and session is not None:
    #    print('Close interactive session')
    #    session.close()

    #1.设定初始输入参数（共6个）
    workPath = "" #工作路径
    rootPath = "" #待检测图像文件夹(org)所在根路径
    model_name = ""  #检测模型路径
    path_to_labels = ""  #标签路径
    resizeRatio = 0.125
    scoreThreshold = 0.5

    #2.从sys获取对应命令行参数
    if len(sys.argv) != 4 and len(sys.argv) != 5 and len(sys.argv) != 6:
        print('Usage: python WindowDetection.py rootPath model_name path_to_labels resizeRatio scoreThreshold')
        exit(1)    
    elif len(sys.argv) == 4:
        workPath = os.path.dirname(sys.argv[0])
        rootPath = sys.argv[1]
        model_name = sys.argv[2]
        path_to_labels = sys.argv[3]    
    elif len(sys.argv) == 5:
        workPath = os.path.dirname(sys.argv[0])
        rootPath = sys.argv[1]
        model_name = sys.argv[2]
        path_to_labels = sys.argv[3]
        resizeRatio = float(sys.argv[4]) if float(sys.argv[4])>0 else 0.25
    elif len(sys.argv) == 6:
        workPath = os.path.dirname(sys.argv[0])
        rootPath = sys.argv[1]
        model_name = sys.argv[2]
        path_to_labels = sys.argv[3]
        resizeRatio = float(sys.argv[4]) if float(sys.argv[4])>0 else 0.125
        scoreThreshold = float(sys.argv[5]) if (float(sys.argv[5])>=0 and float(sys.argv[5])<=1) else 0.5

    #在Spyder中运行py文件时，取消下列注释
    #rootPath = "D:/myWork/clear/20181115412/20181115/1019/7"
    #model_name = "D:/ADoWS/DetectionWindow/ModelInUse"
    #path_to_labels = "D:/ADoWS/DetectionWindow/Data" 

    #3.部分子路径生成
    inputPath = rootPath + "/org"
    outputMASKpath = rootPath + "/mask"

    if os.path.exists(rootPath)!=True:
        exit(1)
    if os.path.exists(outputMASKpath)!=True:
        os.mkdir(outputMASKpath)
    
    run_inference_for_images(workPath,model_name,path_to_labels,inputPath,outputMASKpath,resizeRatio,scoreThreshold)


if __name__ == "__main__":    
    main()