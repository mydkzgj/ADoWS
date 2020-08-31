本程序集合了两个子程序
1.CreateData  创建数据
2.TrainAndFreezeModel  训练和评估

Usage: Call_CD_TF.exe inputImagePath inputXmlPath extensionRatio baseCropNum CutNormalFlag outputName outputPath IgnorePrcsImgTxt / root_path pipeline_confi_path train_step continueFlag / ModelInUsePath

example:
python Call_CD_TF.py D:/ADoWS/Samples/Detection/work/train/org D:/ADoWS/Samples/Detection/work/train/xml 0.6 20 1 train D:/ADoWS/Samples/Detection/work/train/data 0 D:/tensorflow/projects/BreakDetection/models/modelWork1 ssd_resnet50_v1_fpn_shared_box_predictor_640x640_coco14_sync.config 91010 1 D:/ADoWS/DetectionAbnormity/ModelInUse

D:/ADoWS/Code/specific/Call_CD_TF/Call_CD_TF.exe D:/ADoWS/Samples/Detection/work/train/org D:/ADoWS/Samples/Detection/work/train/xml 0.6 20 1 train D:/ADoWS/Samples/Detection/work/train/data 0 D:/tensorflow/projects/BreakDetection/models/modelWork1 ssd_resnet50_v1_fpn_shared_box_predictor_640x640_coco14_sync.config 91100 1 D:/ADoWS/DetectionAbnormity/ModelInUse

输入 inputImagePath，inputXmlPath
     
     1.extensionRatio
     2.baseCropNum，CutNormalFlag
     3.outputName
     outputPath

