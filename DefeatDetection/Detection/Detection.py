# -*- coding: utf-8 -*-
"""
Created on Sat Oct 13 18:56:32 2018

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
from matplotlib import pyplot as plt
from PIL import Image

from PIL import ImageDraw
from PIL import ImageFont

from xml.dom.minidom import Document

import datetime  #获取时间，计算程序执行时间

import shutil   #删除非空文件夹

import XmlRectFusion
import thumbGeneration as tG

import cv2
import WindowDetection as WD

# This is needed since the notebook is stored in the object_detection folder.
sys.path.append("..")

from object_detection.utils import ops as utils_ops

from distutils.version import StrictVersion
if StrictVersion(tf.__version__) < StrictVersion('1.9.0'):
  raise ImportError('Please upgrade your TensorFlow installation to v1.9.* or later!')

# This is needed to display the images.


from object_detection.utils import label_map_util

from object_detection.utils import visualization_utils as vis_util


def cut(inputFilename,vx,vy,stepRatio,useMaskFlag):        #打开图片图片1.jpg
    #for i in range(id):
    #outputPath = "D:\\tensorflow\\models\\research\\object_detection\\cutimages\\"
        
    #CJY at 2019.3.3 增加
    inputMaskName = inputFilename.replace("org","mask")
    if useMaskFlag == 1:
        if os.path.exists(inputMaskName)==True :
            mask = Image.open(inputMaskName)   
        else:
            useMaskFlag = 0
    num_grid = 2
    ng_step_x = vx//(num_grid*2)
    ng_step_y = vy//(num_grid*2)
    
    outputPath = os.path.join(workPath,"Temp","cutimages")
    if os.path.exists(outputPath)!=True:
        os.mkdir(outputPath)
         
    im =Image.open(inputFilename)

    #偏移量
    dx = int(vx*stepRatio)
    dy = int(vy*stepRatio)
    xindex = 0
    yindex = 0
    index = 0

    #左上角切割
    x1 = 0
    y1 = 0
    x2 = vx
    y2 = vy
    print ("图像大小：",im.size) #im.size[0] 宽和高
    w = im.size[0]#宽
    h = im.size[1]#高
    
    TEST_IMAGE_PATHS = []
    #纵向
    while y2 <= h:
        #横向切     
        xindex = 0                
        while x2 <= w:
            outputFilename = os.path.join(outputPath, "image_" + str(yindex) + "_" + str(xindex) + ".jpg")
            #name3 = name2 +  str(index)+ ".jpg"
            #print n,x1,y1,x2,y2
            #CJY at 2019.3.3
            center_x = (x1+x2)//2
            center_y = (y1+y2)//2
            
            #CJY at 2019.3.13 增加
            if useMaskFlag == 1:
                shootMaskFlag = 0
                for r in range(num_grid):
                    if shootMaskFlag == 1:
                        break
                    for c in range(num_grid):
                        if mask.getpixel((center_x+ng_step_x*r,center_y+ng_step_y*c))==255:  #只要有墙体（255）就切
                            shootMaskFlag = 1
                            break     
                        
                if shootMaskFlag == 1:
                    im2 = im.crop((x1, y1, x2, y2))
                    im2.save(outputFilename)
                    TEST_IMAGE_PATHS.append(outputFilename)
                
            else:
                im2 = im.crop((x1, y1, x2, y2))
                im2.save(outputFilename)
                TEST_IMAGE_PATHS.append(outputFilename)
                
            x1 = x1 + dx
            x2 = x1 + vx
            xindex = xindex + 1
            index = index + 1
        x1 = 0
        x2 = vx
        y1 = y1 + dy
        y2 = y1 + vy
        yindex = yindex + 1              
            
    #print ("图片切割成功，切割得到的子图片数为%d"%(xindex*yindex))
    #return [xindex,yindex]     
    print ("图片切割成功，切割得到的子图片数为%d"%(len(TEST_IMAGE_PATHS)))
    return TEST_IMAGE_PATHS      
           
 
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



def run_inference_for_images(workPath,model_name,path_to_labels,inputPath,outputXMLpath,DetectionWindow = 300,stepRatio = 0.5,scoreThreshold = 0.5,useMaskFlag = 1):
    print("正在检测，请勿关闭此窗口！否则，将退出检测！")    
    #起始时间记录
    start=datetime.datetime.now()
    startTime=start.strftime('%Y-%m-%d %H:%M:%S.%f')
    print("检测任务起始时间："+startTime)
    
    #准备需要的路径
    # What model to use.
    MODEL_NAME = model_name    
    # Path to frozen detection graph. This is the actual model that is used for the object detection.
    PATH_TO_CKPT = os.path.join(MODEL_NAME, 'frozen_inference_graph.pb')
    # List of the strings that is used to add correct label for each box.
    PATH_TO_LABELS = os.path.join(path_to_labels, 'label_map.pbtxt')
    # 待检测切片位置
    PATH_TO_TEST_IMAGES_DIR = os.path.join(workPath,"Temp","cutimages")   
    
    # Size, in inches, of the output images.
    #IMAGE_SIZE = (12, 8)
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
    categories = label_map_util.convert_label_map_to_categories(label_map, max_num_classes=NUM_CLASSES, use_display_name=True)    
    #category_index = label_map_util.create_category_index(categories)    
  
    #创建临时文件夹
    TempPath = os.path.join(workPath,"Temp")    
    if os.path.exists(TempPath)==True:
        shutil.rmtree(TempPath)   #清空  
        os.mkdir(TempPath)
    else:
        os.mkdir(TempPath)
    
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
            
            print("检测第%d图片：%s"%(file_index,file))
            sPDstart=datetime.datetime.now()   #singlePicDetection
            sPDstartTime=sPDstart.strftime('%Y-%m-%d %H:%M:%S.%f')
            print("开始时间："+sPDstartTime)
            
            filepath = os.path.join(inputPath, file)      
            
            #CJY at 2019.7.11  为了防止图片损坏，首先尝试读取
            try:
                tryimage = Image.open(filepath) 
            except(OSError, NameError):
                print('OSError, Path:',filepath)
                continue   
            
            #CJY at 2019.3.13 读取非墙体区域掩膜
            inputMaskpath = filepath.replace("org","mask")
            uMF_onePic = useMaskFlag
            if uMF_onePic == 1:
                if os.path.exists(inputMaskpath)==True :
                    mask = cv2.imread(inputMaskpath,cv2.IMREAD_GRAYSCALE)   
                    #将墙体区域（白色）扩展——膨胀
                    kernel = np.ones((50, 50), np.uint8)
                    mask = cv2.dilate(mask, kernel)  # 膨胀dilate
                else:
                    uMF_onePic = 0
            
            
            #1.将原始大图分割成小图
            subWidth = DetectionWindow
            WinStep = int(subWidth*stepRatio)   
            
            #indexRange=cut(filepath,subWidth,subWidth,stepRatio)
            #numCuts=indexRange[0]*indexRange[1] 
            TEST_IMAGE_PATHS = cut(filepath,subWidth,subWidth,stepRatio,useMaskFlag)
            numCuts=len(TEST_IMAGE_PATHS) 
            
            #待检测切片全路径
            #TEST_IMAGE_PATHS = [ os.path.join(PATH_TO_TEST_IMAGES_DIR, 'image_{}_{}.jpg'.format(test_i,test_j)) for test_i in range(0,indexRange[1]) for test_j in range(0,indexRange[0])]
           
            #2.创建xml文件头
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
            
            img =Image.open(filepath)             
            folder.appendChild(doc.createTextNode(os.path.split(inputPath)[-1]))
            filename.appendChild(doc.createTextNode(file))
            path.appendChild(doc.createTextNode(filepath))
            database.appendChild(doc.createTextNode("Unknown"))
            width.appendChild(doc.createTextNode(str(img.size[0])))
            height.appendChild(doc.createTextNode(str(img.size[1])))
            depth.appendChild(doc.createTextNode("3"))
            segmented.appendChild(doc.createTextNode("0"))
            
            cutstart=datetime.datetime.now()
            cutstartTime=cutstart.strftime('%Y-%m-%d %H:%M:%S.%f')
            print(cutstartTime)
            
            #3.对子块进行检测并生成对应成果
            objectNum=0
            objectNumByCates = []  #分别为每一类计数，除了normal
            for i in range(len(categories)-1):
                objectNumByCates.append(0)
                
            for cutIndex,imgCut_path in enumerate(TEST_IMAGE_PATHS):
                '''
                sCDstart=datetime.datetime.now()
                sCDstartTime=sCDstart.strftime('%Y-%m-%d %H:%M:%S.%f')
                print(sCDstartTime)          
                '''                
                imgCut_pre, ext = os.path.splitext(imgCut_path)
                xCutIndex = int(imgCut_pre.split("_")[-1])
                yCutIndex = int(imgCut_pre.split("_")[-2])
                image = Image.open(imgCut_path)                
                
                # the array based representation of the image will be used later in order to prepare the
                # result image with boxes and labels on it.               
                #image_np = load_image_into_numpy_array(image)   #最耗费时间 0.10s左右
                                
                # Expand dimensions since the model expects images to have shape: [1, None, None, 3]
                #image_np_expanded = np.expand_dims(image_np, axis=0)                
                 
                # Actual detection.        
                output_dict = run_inference_for_single_image(image, sess,detection_graph)
                
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
                #print(output_dict['detection_boxes'])
                '''
                                 
                #写入xml也很费时间，0.015s左右
                for index,boxScore in enumerate(output_dict['detection_scores']):
                    if boxScore>scoreThreshold:                      
                        objectNameIndex = output_dict['detection_classes'][index]
                        objectName = categories[objectNameIndex-1]['name']
                        if objectName == "normal":
                            continue   
                        passedBox=output_dict['detection_boxes'][index]
                        
                        x_bais=xCutIndex*WinStep 
                        y_bais=yCutIndex*WinStep        
        
                        #label_img 的坐标系与 tensorflow 坐标系(水平y，竖直x)不一致  xmin ymin xmax ymax
                        xmin_value=int(passedBox[1]*subWidth+x_bais)
                        ymin_value=int(passedBox[0]*subWidth+y_bais)
                        xmax_value=int(passedBox[3]*subWidth+x_bais)
                        ymax_value=int(passedBox[2]*subWidth+y_bais)
                        
                        #如果考虑掩膜的话，进行检测框筛选
                        if uMF_onePic == 1:
                            if mask[ymin_value,xmin_value]!=255 or mask[ymin_value,xmax_value]!=255 and mask[ymax_value,xmin_value]!=255 and mask[ymax_value,xmax_value]!=255:#4个角点都处于墙体区域
                                continue                      
                        
     
                        objectNum =objectNum+1
                        objectNumByCates[objectNameIndex-1] = objectNumByCates[objectNameIndex-1]+1
                      
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

                        
                        name.appendChild(doc.createTextNode(objectName))
                        pose.appendChild(doc.createTextNode("Unspecified"))
                        truncated.appendChild(doc.createTextNode("0"))
                        difficult.appendChild(doc.createTextNode("0"))
                        xmin.appendChild(doc.createTextNode(str(xmin_value)))
                        ymin.appendChild(doc.createTextNode(str(ymin_value)))
                        xmax.appendChild(doc.createTextNode(str(xmax_value)))
                        ymax.appendChild(doc.createTextNode(str(ymax_value)))              
                        score.appendChild(doc.createTextNode(str(boxScore)))  
                
                logfile=open(os.path.join(TempPath,"temp.txt"),'w')  
                logfile.write("("+str(num_files)+"/"+str(file_index)+")"+file+":"+str(numCuts)+"/"+str(cutIndex+1))
                logfile.close()                
                
                #显示进程
                print("("+str(num_files)+"/"+str(file_index)+")"+file+": "+str(numCuts)+"/"+str(cutIndex+1))  
                
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
            #(1).xml文件保存
            OnePicEnd=datetime.datetime.now()
            OPEtime=OnePicEnd.strftime('%Y%m%d%H%M%S')
            xmlfilename=fname+"_"+OPEtime+".XML"  
            xmlfullname=os.path.join(outputXMLpath,xmlfilename)
            XMLfile = open(xmlfullname, "w")
            XMLfile.write(doc.toprettyxml(indent="  "))
            XMLfile.close()  
            
            #增加xmlWs中的保存
            '''
            xmlfullname2 = os.path.join(outputXMLwithoutSpath,fname+".XML")
            XMLfile = open(xmlfullname2, "w")
            XMLfile.write(doc.toprettyxml(indent="  "))
            XMLfile.close()  
            '''
            
            #(可选)Xml Rect 融合(视情况而定)
            XmlRectFusion.SingleXmlRectFusion(xmlfullname, inputMaskpath, useMaskFlag)
            
            #(2).生成缩略图及带标注缩略图
            outputErrThumb = tG.GenerationThumbAndErrThumb(filepath,xmlfullname,rootPath,quality=10)     
            
            '''
            #CJY at 2019.5.24  复制xml到xml_m中 ,搬移 err 到err_m
            shutil.copy2(xmlfullname,outputXMLMpath)
            shutil.move(outputErrThumb,outputERRMpath)
            '''
            
            '''
            #将图片与xml名字做匹配，记录到org文件下的"img_xml_namedict.txt"中
            ix_file = open(os.path.join(os.path.dirname(inputPath),"img_xml_namedict.txt"),"a")
            ix_file.write(file)
            ix_file.write(" ")
            ix_file.write(xmlfilename.replace(".XML",".xml"))
            ix_file.write("\n")
            '''
            
            #单张图像检测结束时间
            sPDend=datetime.datetime.now()
            sPDendTime=sPDend.strftime('%Y-%m-%d %H:%M:%S.%f')
            print(sPDendTime)
            print('单张图像检测时间: %s Seconds'%(sPDend-sPDstart))            
            
            #将信息记录在dTemp.txt中
            print()
            detailsLogfile=open(os.path.join(outputMASKpath,'dTemp.txt'),'a')   #TempPath
            detailsLogfile.write(fname+"\n")
            detailsLogfile.write("start:"+sPDstartTime+"\n")
            detailsLogfile.write("end:"+sPDendTime+"\n")
            detailsLogfile.write("detection useTime:%s"%(sPDend-sPDstart)+"\n")
            detailsLogfile.write("abnormNum:%s"%(str(objectNum))+"\n")
            detailsLogfile.close()
        
    #CJY at 2019.6.20  新增ORGERR备份
    shutil.copytree(outputERRpath,outputORGERRpath)
    
    
    #删除临时文件夹
    if os.path.exists(TempPath)==True:
        shutil.rmtree(TempPath)
    
    #写入标志位，是否完成对所有文件的检测
    finishfile = open(os.path.join(workPath,'FinishFlag.txt'),'w') 
    finishfile.write("1")
    finishfile.close() 
    
    end=datetime.datetime.now()
    endTime=end.strftime('%Y-%m-%d %H:%M:%S.%f')
    print("检测任务结束时间："+endTime)
    print('检测程序运行时间: %s Seconds'%(end-start))


#检查是否有其他会话正在运行
#if 'session' in locals() and session is not None:
#    print('Close interactive session')
#    session.close()

#1.设定初始输入参数（共6个）
workPath = "" #工作路径
rootPath = "" #待检测图像文件夹(org)所在根路径
model_name = ""  #检测模型路径
path_to_labels = ""  #标签路径
DetectionWindow = 640
stepRatio = 0.5
scoreThreshold = 0.5

W_model_name = ""
W_path_to_labels = ""
W_resizeRatio = 0.125
W_scoreThreshold = 0.5

#2.从sys获取对应命令行参数
#python Detection.py E:/myWork/clear/20181115412/20181115/1019/1 D:/ADoWS/DetectionAbnormity/ModelInUse D:/ADoWS/DetectionAbnormity/Data 300 0.5 0.5 D:/ADoWS/DetectionWindow/ModelInUse D:/ADoWS/DetectionWindow/Data 0.25 0.5
if len(sys.argv) != 4 and len(sys.argv) != 5 and len(sys.argv) != 6 and len(sys.argv) != 7 and len(sys.argv) != 9 and len(sys.argv) != 10 and len(sys.argv) != 11:
    print('Usage: python Detection.py rootPath model_name path_to_labels DetectionWindow stepRatio scoreThrehold')    
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
    DetectionWindow = int(sys.argv[4]) if int(sys.argv[4])>0 else 300
elif len(sys.argv) == 6:
    workPath = os.path.dirname(sys.argv[0])
    rootPath = sys.argv[1]
    model_name = sys.argv[2]
    path_to_labels = sys.argv[3]
    DetectionWindow = int(sys.argv[4]) if int(sys.argv[4])>0 else 300
    stepRatio = float(sys.argv[5]) if float(sys.argv[5])>0 else 0.5
elif len(sys.argv) == 7:
    workPath = os.path.dirname(sys.argv[0])
    rootPath = sys.argv[1]
    model_name = sys.argv[2]
    path_to_labels = sys.argv[3]
    DetectionWindow = int(sys.argv[4]) if int(sys.argv[4])>0 else 300
    stepRatio = float(sys.argv[5]) if float(sys.argv[5])>0 else 0.5
    scoreThreshold = float(sys.argv[6]) if (float(sys.argv[6])>=0 and float(sys.argv[6])<=1) else 0.5
#加入窗户检测
elif len(sys.argv) == 9:
    workPath = os.path.dirname(sys.argv[0])
    rootPath = sys.argv[1]
    model_name = sys.argv[2]
    path_to_labels = sys.argv[3]
    DetectionWindow = int(sys.argv[4]) if int(sys.argv[4])>0 else 300
    stepRatio = float(sys.argv[5]) if float(sys.argv[5])>0 else 0.5
    scoreThreshold = float(sys.argv[6]) if (float(sys.argv[6])>=0 and float(sys.argv[6])<=1) else 0.5
    #窗户检测参数
    W_model_name = sys.argv[7]
    W_path_to_labels = sys.argv[8]    
    
elif len(sys.argv) == 10:
    workPath = os.path.dirname(sys.argv[0])
    rootPath = sys.argv[1]
    model_name = sys.argv[2]
    path_to_labels = sys.argv[3]
    DetectionWindow = int(sys.argv[4]) if int(sys.argv[4])>0 else 300
    stepRatio = float(sys.argv[5]) if float(sys.argv[5])>0 else 0.5
    scoreThreshold = float(sys.argv[6]) if (float(sys.argv[6])>=0 and float(sys.argv[6])<=1) else 0.5
    #窗户检测参数
    W_model_name = sys.argv[7]
    W_path_to_labels = sys.argv[8]
    W_resizeRatio = float(sys.argv[9]) if float(sys.argv[9])>0 else 0.25
    
elif len(sys.argv) == 11:
    workPath = os.path.dirname(sys.argv[0])
    rootPath = sys.argv[1]
    model_name = sys.argv[2]
    path_to_labels = sys.argv[3]
    DetectionWindow = int(sys.argv[4]) if int(sys.argv[4])>0 else 300
    stepRatio = float(sys.argv[5]) if float(sys.argv[5])>0 else 0.5    
    scoreThreshold = float(sys.argv[6]) if (float(sys.argv[6])>=0 and float(sys.argv[6])<=1) else 0.5
    #窗户检测参数
    W_model_name = sys.argv[7]
    W_path_to_labels = sys.argv[8]
    W_resizeRatio = float(sys.argv[9]) if float(sys.argv[9])>0 else 0.25
    W_scoreThreshold = float(sys.argv[10]) if (float(sys.argv[10])>=0 and float(sys.argv[10])<=1) else 0.5
    

#在Spyder中运行py文件时，取消下列注释
'''
rootPath = "D:/myWork/clear/20181115412/20181115/1019/train"
model_name = "D:/ADoWS/DetectionAbnormity/ModelInUse"
path_to_labels = "D:/ADoWS/DetectionAbnormity/Data"    

W_model_name = "D:/ADoWS/DetectionWindow/ModelInUse"
W_path_to_labels = "D:/ADoWS/DetectionWindow/Data" 
#'''

#3.部分子路径生成
inputPath = rootPath + "/org"
outputXMLpath = rootPath + "/xml"
outputTHpath = rootPath + "/th"
outputERRpath = rootPath + "/err"
outputORGERRpath = rootPath + "/orgerr"
outputXMLwithoutSpath = rootPath + "/xmlWs"
outputMASKpath = rootPath + "/mask"

outputXMLMpath = rootPath + "/xml_m"
outputERRMpath = rootPath + "/err_m"


if os.path.exists(rootPath)!=True:
    exit(1)
if os.path.exists(outputXMLpath)!=True:
    os.mkdir(outputXMLpath)
else:
    shutil.rmtree(outputXMLpath)
    os.mkdir(outputXMLpath)
if os.path.exists(outputTHpath)!=True:
    os.mkdir(outputTHpath)
else:
    shutil.rmtree(outputTHpath)
    os.mkdir(outputTHpath)
if os.path.exists(outputERRpath)!=True:
    os.mkdir(outputERRpath)
else:
    shutil.rmtree(outputERRpath)
    os.mkdir(outputERRpath)
if os.path.exists(outputMASKpath)!=True:
    os.mkdir(outputMASKpath)
#if os.path.exists(outputXMLwithoutSpath)!=True:
#    os.mkdir(outputXMLwithoutSpath)
    
if os.path.exists(outputORGERRpath)==True:
    shutil.rmtree(outputORGERRpath)
    
'''
if os.path.exists(outputXMLMpath)!=True:
    os.mkdir(outputXMLMpath)
else:
    shutil.rmtree(outputXMLMpath)
    os.mkdir(outputXMLMpath)
if os.path.exists(outputERRMpath)!=True:
    os.mkdir(outputERRMpath)
else:
    shutil.rmtree(outputERRMpath)
    os.mkdir(outputERRMpath)
'''

if __name__ == "__main__": 
    if os.path.exists(os.path.join(outputMASKpath,'dTemp.txt'))==True:
        os.remove(os.path.join(outputMASKpath,'dTemp.txt'))        
    WD.run_inference_for_images(workPath,W_model_name,W_path_to_labels,inputPath,outputMASKpath,W_resizeRatio,W_scoreThreshold)
    if os.path.exists(os.path.join(rootPath,"img_xml_namedict.txt"))==True:
        os.remove(os.path.join(rootPath,"img_xml_namedict.txt"))
    print("scoreThreshold:",scoreThreshold)
    run_inference_for_images(workPath,model_name,path_to_labels,inputPath,outputXMLpath,DetectionWindow,stepRatio,scoreThreshold,1)
    #删除无用的文件夹
    #if os.path.exists(outputMASKpath)==True:
    #    shutil.rmtree(outputMASKpath)