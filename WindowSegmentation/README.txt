1.图像和json文件resize
python resize_img_json.py

2.依据图像和json文件生成tfrecord
python create_tf_record.py --images_dir=your absolute path to read images. --annotations_json_dir=your path to annotaion json files. --label_map_path=your path to label_map.pbtxt --output_path=your path to write .record.

python create_tf_record.py --images_dir=D:\ADoWS\Samples\WindowSegmentation\source\split_sets\train --annotations_json_dir=D:\ADoWS\Samples\WindowSegmentation\source\split_sets\train --label_map_path=D:\ADoWS\Samples\WindowSegmentation\source\label_map.pbtxt --output_path=D:\ADoWS\Samples\WindowSegmentation\source\split_sets\record\train.record

python create_tf_record.py --images_dir=D:\ADoWS\Samples\WindowSegmentation\source\split_sets\val --annotations_json_dir=D:\ADoWS\Samples\WindowSegmentation\source\split_sets\val --label_map_path=D:\ADoWS\Samples\WindowSegmentation\source\label_map.pbtxt --output_path=D:\ADoWS\Samples\WindowSegmentation\source\split_sets\record\val.record