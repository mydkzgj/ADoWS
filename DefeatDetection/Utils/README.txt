程序简介
1. RemoveXmlSuffix
功能：删去xml文件最后一个"_"之后的内容（由于detection.py检测后生成的xml会在图像名称后加入时间戳，将导致labelImg无法匹配读取）
python RemoveXmlSuffix.py input_folder output_folder
python RemoveXmlSuffix.py D:\myWork\clear\20181115412\20181115\1019\train\xml D:\ADoWS\Samples\Detection\work\database\re_training\train\xml

