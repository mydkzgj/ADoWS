# -*- coding: utf-8 -*-
"""
Created on Thu Dec 27 19:41:46 2018

@author: cjy
"""


import numpy as np

import cv2

 

class Point(object):  #行数，列数

    def __init__(self,x,y):

        self.x = x

        self.y = y

 

    def getX(self):

        return self.x

    def getY(self):

        return self.y

 

def getGrayDiff(img,currentPoint,tmpPoint):

    return abs(int(img[currentPoint.x,currentPoint.y]) - int(img[tmpPoint.x,tmpPoint.y]))

 

def selectConnects(p):

    if p != 0:

        connects = [Point(-1, -1), Point(0, -1), Point(1, -1), Point(1, 0), Point(1, 1), \

                    Point(0, 1), Point(-1, 1), Point(-1, 0)]

    else:

        connects = [ Point(0, -1),  Point(1, 0),Point(0, 1), Point(-1, 0)]

    return connects

 

def regionGrow(img,seeds,thresh,p = 1):

    height, weight = img.shape

    seedMark = np.zeros(img.shape,dtype = np.uint8)

    seedList = []

    for seed in seeds:

        seedList.append(seed)

    label = 255

    connects = selectConnects(p)

    while(len(seedList)>0):

        currentPoint = seedList.pop(0)

 

        seedMark[currentPoint.x,currentPoint.y] = label

        for i in range(8):

            tmpX = currentPoint.x + connects[i].x

            tmpY = currentPoint.y + connects[i].y

            if tmpX < 0 or tmpY < 0 or tmpX >= height or tmpY >= weight:

                continue

            grayDiff = getGrayDiff(img,currentPoint,Point(tmpX,tmpY))

            if grayDiff < thresh and seedMark[tmpX,tmpY] == 0:

                seedMark[tmpX,tmpY] = label

                seedList.append(Point(tmpX,tmpY))

    return seedMark

 

def main():
    img = cv2.imread('DSC00058.JPG',0)
    size = img.shape
    img = cv2.resize(img,(int(size[1]/10),int(size[0]/10)))
    cv2.imshow("1",img)
    cv2.waitKey(0)
    seeds = [Point(0,0),Point(int(size[0]/10)-1,0),Point(0,int(size[1]/10)-1),Point(int(size[0]/10)-1,int(size[1]/10)-1)]
    binaryImg = regionGrow(img,seeds,3)
    cv2.imshow('2',binaryImg)
    cv2.waitKey(0)
    cv2.destroyAllWindows(0)

if __name__=="__main__":
    main()