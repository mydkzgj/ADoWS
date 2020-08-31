总程序
CreateData.py
其主要集合了三个子程序
1.GenerateNewXml  标签拓展
2.CutsGeneration  切片
3.TFRecordGeneration  TFRecord样本生成

其中ClassStatistics.txt设定各类别的扩增数量，用于CutsGeneration.py中
其中tfRecord_label_map.pbtxt记录哪些类别保存到tfrecord中，用于TFRecordGeneration.py

Usage: python inputImagePath inputXmlPath extensionRatio baseCropNum CutNormalFlag outputName outputPath IgnorePrcsImgTxt

example:
python CreateData.py D:/ADoWS/Samples/Detection/work/train/org D:/ADoWS/Samples/Detection/work/train/xml 0.6 20 1 train D:/ADoWS/Samples/Detection/work/train/data 1

