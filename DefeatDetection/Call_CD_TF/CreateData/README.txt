�ܳ���
CreateData.py
����Ҫ�����������ӳ���
1.GenerateNewXml  ��ǩ��չ
2.CutsGeneration  ��Ƭ
3.TFRecordGeneration  TFRecord��������

����ClassStatistics.txt�趨��������������������CutsGeneration.py��
����tfRecord_label_map.pbtxt��¼��Щ��𱣴浽tfrecord�У�����TFRecordGeneration.py

Usage: python inputImagePath inputXmlPath extensionRatio baseCropNum CutNormalFlag outputName outputPath IgnorePrcsImgTxt

example:
python CreateData.py D:/ADoWS/Samples/Detection/work/train/org D:/ADoWS/Samples/Detection/work/train/xml 0.6 20 1 train D:/ADoWS/Samples/Detection/work/train/data 1

