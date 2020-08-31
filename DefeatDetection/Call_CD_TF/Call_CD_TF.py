# -*- coding: utf-8 -*-
"""
Created on Sun Oct 13 10:24:39 2019

@author: admin
"""


import os
import sys
import shutil


'''
本程序集合了两个子程序
1.CreateData  创建数据
2.TrainAndFreezeModel  训练和评估


example:
python D:/ADoWS/Code/DefeatDetection/Call_CD_TF/Call_CD_TF.py D:/ADoWS/Samples/Detection/work/database/re_training/train/org D:/ADoWS/Samples/Detection/work/database/re_training/train/xml 0.6 20 1 train D:/ADoWS/Samples/Detection/work/database/re_training/train/data 0 D:/tensorflow/projects/BreakDetection/models/modelWork1 ssd_resnet50_v1_fpn_shared_box_predictor_640x640_coco14_sync.config 200 1 D:/ADoWS/Code/DefeatDetection/Call_CD_TF/MIU

输入 inputImagePath，inputXmlPath
     
     1.extensionRatio
     2.baseCropNum，CutNormalFlag
     3.outputName
     outputPath
    
'''
def del_dir_tree(path):
    ''' 递归删除目录及其子目录,　子文件'''
    if os.path.isfile(path):
        try:
            os.remove(path)
        except Exception as e:
            #pass
            print(e)
    elif os.path.isdir(path):
        for item in os.listdir(path):
            itempath = os.path.join(path, item)
            del_dir_tree(itempath)
        try:
            os.rmdir(path) # 删除空目录
        except Exception as e:
            #pass
            print(e)
            


if __name__=="__main__": 
    print(sys.argv)
    if len(sys.argv) != 14:
        print('Usage: Call_CD_TF.exe inputImagePath inputXmlPath extensionRatio baseCropNum CutNormalFlag outputName outputPath IgnorePrcsImgTxt / root_path pipeline_confi_path train_step continueFlag / ModelInUsePath')
        exit(1)
    elif len(sys.argv) == 14:
        workPath = os.path.dirname(sys.argv[0])
        """
        #for CreateData
        inputImagePath = sys.argv[1]
        inputXmlPath = sys.argv[2]
        extensionRatio = float(sys.argv[3])
        baseCropNum = int(sys.argv[4])        
        CutNormalFlag = 1 if int(sys.argv[5])!=0 else 0
        outputName = sys.argv[6] 
        outputPath = sys.argv[7]
        IgnorePrcsImgTxt = int(sys.argv[8])
        #for TrainAndFreezeModel
        root_path = sys.argv[9]
        pipeline_confi_path = os.path.join(root_path,sys.argv[10])
        train_step = int(sys.argv[11])   
        continueFlag = int(sys.argv[12])    
        ModelInUsePath = sys.argv[13]
        """
        if os.path.exists(os.path.join(workPath, "CreateData/CreateData.exe")) == True:
            CD_cmdline = os.path.join(workPath,"CreateData/CreateData.exe")+" "+sys.argv[1]+" "+sys.argv[2]+" "+sys.argv[3]+" "+sys.argv[4]+" "+sys.argv[5]+" "+sys.argv[6]+" "+sys.argv[7]+" "+sys.argv[8]
        elif os.path.exists(os.path.join(workPath, "CreateData/CreateData.py")) == True:
            CD_cmdline = "python " + os.path.join(workPath, "CreateData/CreateData.py") + " " + sys.argv[1] + " " + sys.argv[2] + " " + sys.argv[3] + " " + sys.argv[4] + " " + sys.argv[5] + " " + sys.argv[6] + " " + sys.argv[7] + " " + sys.argv[8]
        else:
            raise Exception("There is no sub program named CreateData")

        if os.path.exists(os.path.join(workPath, "TrainAndFreezeModel/TrainAndFreezeModel.exe")) == True:
            TF_cmdline = os.path.join(workPath,"TrainAndFreezeModel/TrainAndFreezeModel.exe")+ " "+sys.argv[9]+" "+sys.argv[10]+" "+sys.argv[11]+" "+sys.argv[12]
        elif os.path.exists(os.path.join(workPath, "TrainAndFreezeModel/TrainAndFreezeModel.py")) == True:
            TF_cmdline = "python " + os.path.join(workPath, "TrainAndFreezeModel/TrainAndFreezeModel.py") + " " + sys.argv[9] + " " + sys.argv[10] + " " + sys.argv[11] + " " + sys.argv[12]
        else:
            raise Exception("There is no sub program named TrainAndFreezeModel")

    print("创建数据，请稍等")
    print(CD_cmdline)
    os.system(CD_cmdline)
    print("数据创建已完成")
    print("正在训练，请稍等")
    print(TF_cmdline)
    os.system(TF_cmdline)
    print("训练已完成")

    # 后处理
    # 更新finetune model & model in use
    # 寻找export中最近的一次作为重新finetune的起始点，放置到finetune文件夹中
    root_path = sys.argv[9]
    frozenmodel_output_path = os.path.join(root_path,"export")
    ModelInUsePath = sys.argv[13]
    if os.path.exists(frozenmodel_output_path) == True:
        exportList = os.listdir(frozenmodel_output_path)
        exportIndexMax = 0
        for exportNum in exportList:
            if exportNum.isdigit() == True:
                if int(exportNum) > exportIndexMax:
                    exportIndexMax = int(exportNum)
        if exportIndexMax != 0:
            if os.path.exists(ModelInUsePath) == True:
                del_dir_tree(ModelInUsePath)
            shutil.copytree(os.path.join(frozenmodel_output_path,str(exportIndexMax)),ModelInUsePath)
        else:
            raise Exception("Error! Train Failed!")
    else:
        raise Exception("Error! Train Failed!")
    
    
    