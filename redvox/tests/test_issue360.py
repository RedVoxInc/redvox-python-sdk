from redvox.common.api_reader import ApiReader
from redvox.common.data_window import DataWindow
import shutil
from time import time
import os
from os import listdir
from os.path import isfile, join
import numpy as np


def main():
    input_dir = "/Users/yusukehatanaka/Desktop/DATA/20200222_GoodComms/"
    dw = DataWindow(
        input_dir=input_dir,
        # station_ids=['1637610028']
    )
    # input_dir = "/Users/yusukehatanaka/Desktop/DATA/20200222_GoodComms/api900/2020/02/22/"
    # start = time()
    # only_files = [f for f in listdir(input_dir) if isfile(join(input_dir, f))]
    # # print("expected:", os.stat(input_dir + only_files[0]).st_size)
    # temp = np.sum([os.stat(input_dir + item).st_size for item in only_files])
    # print(temp)
    # end = time()
    # print(end - start)


if __name__ == '__main__':
    main()
