# -*- coding: utf-8 -*-
"""
Created on Sat May 25 20:24:09 2019

@author: admin
"""

"""
本脚本用于开始训练以及保存模型

需要调用的exe文件有两个
1.model_main.exe 训练模型
2.export_inference_graph.exe 冻结模型

为了简单起见，只冻结最后一个节点的模型

python D:/tensorflow/projects/BreakDetection/models/modelWork1 ssd_resnet50_v1_fpn_shared_box_predictor_640x640_coco14_sync.config 91000 1

"""
import os
import sys
import shutil

workPath = os.path.dirname(sys.argv[0])

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
            


if __name__ == "__main__":        
    if len(sys.argv) != 5:
        print('Usage: python root_path pipeline_confi_path train_step continueFlag')   #continueFlag表示断点续传，继续训练
        exit(1)
    elif len(sys.argv) == 5:    
        workPath = os.path.dirname(sys.argv[0])
        root_path = sys.argv[1]
        pipeline_confi_path = os.path.join(root_path,sys.argv[2])
        train_step = int(sys.argv[3])   
        continueFlag = int(sys.argv[4])
    
    
    #root_path = "D:/tensorflow/projects/BreakDetection/models/model15"
    #pipeline_confi_path = os.path.join(root_path,"ssd_resnet50_v1_fpn_shared_box_predictor_640x640_coco14_sync.config")
    model_dir = os.path.join(root_path,"train")
    frozenmodel_output_path = os.path.join(root_path,"export")
    
    #train_step = 5000    
    #生成训练程序需要的命令行参数
    config_train = {}
    config_train["--pipeline_config_path="] = pipeline_confi_path
    config_train["--model_dir="] = model_dir
    config_train["--num_train_steps="] = str(train_step)
    config_train["--sample_1_of_n_eval_examples="] = "1"
    config_train["--alsologtostderr"] = ""

    if os.path.exists(os.path.join(workPath, "model_main.exe")) == True:
        cmdline_train = os.path.join(workPath,"model_main.exe")
    elif os.path.exists(os.path.join(workPath, "model_main.py")) == True:
        cmdline_train = "python " + os.path.join(workPath, "model_main.py")
    else:
        raise Exception("There is no sub program named model_main")

    for key in config_train.keys():
        cmdline_train = cmdline_train + " " + key + config_train[key]
        
    print(cmdline_train)
        
    if continueFlag != 1:
        #清空上一次训练的结果
        if os.path.exists(model_dir) == True:
            del_dir_tree(model_dir)
        finetunePath = os.path.join(root_path,"finetune")
        
        #os.mkdir(finetunePath)
    
        
    #寻找export中最近的一次作为重新finetune的起始点，放置到finetune文件夹中
    if os.path.exists(frozenmodel_output_path) == True:
        exportList = os.listdir(frozenmodel_output_path)
        exportIndexMax = 0
        for exportNum in exportList:
            if exportNum.isdigit() == True:
                if int(exportNum) > exportIndexMax:
                    exportIndexMax = int(exportNum)
                
        if exportIndexMax > 0 and continueFlag != 1:
            if os.path.exists(finetunePath) == True:
                del_dir_tree(finetunePath)
            shutil.copytree(os.path.join(frozenmodel_output_path,str(exportIndexMax)),finetunePath)   
    else:
        os.mkdir(frozenmodel_output_path)  #注意export_inference_graph.exe只能创建一层目录，所以没有export的话就不能创建export/1
        exportIndexMax = 0
    
    #运行训练程序  
    os.system(cmdline_train) 
    
    frozenmodel_output_directory = os.path.join(frozenmodel_output_path,str(exportIndexMax+1))
    filelist = os.listdir(config_train["--model_dir="])
    save_ckpt_name = "model.ckpt-" + str(train_step)
    
    config_export = {}
    config_export["--input_type="] = "image_tensor"
    config_export["--pipeline_config_path="] = pipeline_confi_path
    config_export["--trained_checkpoint_prefix="] = os.path.join(model_dir,save_ckpt_name)
    config_export["--output_directory="] = frozenmodel_output_directory

    if os.path.exists(os.path.join(workPath, "export_inference_graph.exe")) == True:
        cmdline_export = os.path.join(workPath,"export_inference_graph.exe")
    elif os.path.exists(os.path.join(workPath, "export_inference_graph.py")) == True:
        cmdline_export = "python " + os.path.join(workPath,"export_inference_graph.py")
    else:
        raise Exception("There is no sub program named export_inference_graph")

    for key in config_export.keys():
        cmdline_export = cmdline_export + " " + key + config_export[key]
    #运行冻结程序
    print(save_ckpt_name+".data-00000-of-00001" in filelist)
    print(save_ckpt_name+".index" in filelist)
    print(save_ckpt_name+".meta" in filelist)
    if (save_ckpt_name+".data-00000-of-00001" in filelist) and (save_ckpt_name+".index" in filelist) and (save_ckpt_name+".meta" in filelist):
        os.system(cmdline_export) 
