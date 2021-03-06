import os
import random

import cv2
import numpy as np

from Algorithm.OCR.utils import newNet
from Algorithm.utils.Finder import meterFinderBySIFT
from Algorithm.utils.boxRectifier import boxRectifier
from configuration import *


def digitPressure(image, info):
    template = meterFinderBySIFT(image, info)
    template = cv2.GaussianBlur(template, (3, 3), 0)

    # 读取标定信息
    widthSplit = info["widthSplit"]
    heightSplit = info["heightSplit"]

    # 由标定点得到液晶区域
    dst = boxRectifier(template, info)

    # 灰度图
    gray = cv2.cvtColor(dst, cv2.COLOR_BGR2GRAY)

    # 针对不同的数字表类型进行不同的增强
    if info["digitType"] != "TTC":
        Blur = cv2.GaussianBlur(gray, (5, 5), 0)
        Hist = cv2.equalizeHist(Blur)
        thresh = cv2.adaptiveThreshold(Hist, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY_INV, 15, 11)
    else:
        thresh = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 55, 11)

    # 存储图片
    if not os.path.exists("storeDigitData"):
        os.mkdir("storeDigitData")
    if not os.path.exists("storeDigitData/digits"):
        os.mkdir("storeDigitData/digits")
    imgNum = int((len(os.listdir("storeDigitData/"))-1)/3)
    cv2.imwrite("storeDigitData/" + str(imgNum) + "_dst.bmp", dst)
    cv2.imwrite("storeDigitData/" + str(imgNum) + "_gray.bmp", gray)
    cv2.imwrite("storeDigitData/" + str(imgNum) + "_thresh.bmp", thresh)

    # 网络初始化
    MyNet = newNet()
    myRes = []

    for i in range(len(heightSplit)):
        split = widthSplit[i]
        myNum = ""
        for j in range(len(split) - 1):
            if "decimal" in info.keys() and j == info["decimal"][i]:
                myNum += "."
                continue
            # 得到分割的图片区域
            img = thresh[heightSplit[i][0]:heightSplit[i][1], split[j]:split[j + 1]]

            # 增强
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 2))
            img = cv2.morphologyEx(img, cv2.MORPH_OPEN, kernel)

            num = MyNet.recognizeNet(img)
            myNum = myNum + num

            # 存储图片
            cv2.imwrite("storeDigitData/digits/{}_{}{}_p{}.bmp".format(
                imgNum,
                i,
                j,
                num
            ), img)

        myRes.append(myNum)

    if info["digitType"] == "KWH":
        myRes[0] = myRes[0][:4]+myRes.pop(1)

    # 去除头部的非数字字符，同时将非头部的字符转为数字
    for i in range(len(myRes)):
        temp = ""
        for j, c in enumerate(myRes[i]):
            if c != "?":
                temp += c
            elif j != 0:
                temp += str(random.randint(0, 9))
        myRes[i] = float(temp)

    if ifShow:
        cv2.imshow("rec", dst)
        cv2.imshow("image", image)
        print(myRes)
        cv2.waitKey(0)
        cv2.destroyAllWindows()

    return myRes
