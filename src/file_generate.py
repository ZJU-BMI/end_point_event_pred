# encoding=utf-8
import os
import csv
import numpy as np
import random
import re
from itertools import islice


# 生成开源SVM所需的格式
def read_data(file_path):
    data_matrix = []
    with open(file_path, 'r', encoding='gbk', newline="") as file:
        csv_reader = csv.reader(file)
        # 跳过第一行Head和第一列
        for line in islice(csv_reader, 1, None):
            row = []
            for item in islice(line, 1, None):
                value = re.findall('[-+]?[.]?[\d]+(?:,\d\d\d)*[\.]?\d*(?:[eE][-+]?\d+)?', item)
                value = float(value[0])
                row.append(value)
            data_matrix.append(row)
    return np.array(data_matrix)


def read_label(file_path):
    thirty_day_readmit = list()
    one_year_readmit = list()
    cardio_death = list()
    all_cause_death = list()

    with open(file_path, 'r', encoding='gbk', newline="") as file:
        csv_reader = csv.reader(file)
        # 跳过第一行Head和第一列
        for line in islice(csv_reader, 1, None):
            thirty_day_readmit.append(line[0])
            one_year_readmit.append(line[0])
            cardio_death.append(line[0])
            all_cause_death.append(line[0])

    thirty_day_readmit = np.array(thirty_day_readmit)
    one_year_readmit = np.array(one_year_readmit)
    cardio_death = np.array(cardio_death)
    all_cause_death = np.array(all_cause_death)
    return thirty_day_readmit, one_year_readmit, cardio_death, all_cause_death


def event_split(data):
    feature = data[:, 0:-4]
    thirty_day_readmit = data[:, -4]
    thirty_day_readmit = thirty_day_readmit[:, np.newaxis]
    one_year_readmit = data[:, -3]
    one_year_readmit = one_year_readmit[:, np.newaxis]
    cardio_death = data[:, -2]
    cardio_death = cardio_death[:, np.newaxis]
    all_cause_death = data[:, -1]
    all_cause_death = all_cause_death[:, np.newaxis]

    thirty_day_readmit = np.concatenate([feature, thirty_day_readmit], axis=1)
    one_year_readmit = np.concatenate([feature, one_year_readmit], axis=1)
    cardio_death = np.concatenate([feature, cardio_death], axis=1)
    all_cause_death = np.concatenate([feature, all_cause_death], axis=1)
    return thirty_day_readmit, one_year_readmit, cardio_death, all_cause_death


def five_fold_split(data):
    # 数据规范，data是一个 M*N的矩阵，其中，M*(N-1)的部分是特征，最后一列是标签
    # 标签要求正标签为1，负标签为-1，无标签为0
    pos_data = list()
    neg_data = list()
    no_label_data = list()

    for item in data:
        if item[-1] == 1:
            pos_data.append(item)
        elif item[-1] == -1:
            neg_data.append(item)
        elif item[-1] == 0:
            no_label_data.append(item)
        else:
            raise ValueError("")

    # 随机化
    random.shuffle(pos_data)
    random.shuffle(neg_data)
    random.shuffle(no_label_data)

    five_fold = list()
    for i in range(5):
        pos_num = len(pos_data) // 5
        neg_num = len(neg_data) // 5
        no_num = len(no_label_data) // 5
        if i != 4:
            fold_pos = np.array(pos_data[i*pos_num:(i+1)*pos_num])
            fold_neg = np.array(neg_data[i*neg_num:(i+1)*neg_num])
            fold_no = np.array(no_label_data[i*no_num:(i+1)*no_num])
            five_fold.append(np.concatenate([fold_pos, fold_neg, fold_no], axis=0))
        else:
            # 由于数据珍贵，不能丢弃任何一个数据
            fold_pos = np.array(pos_data[4*pos_num:])
            fold_neg = np.array(neg_data[4*neg_num:])
            fold_no = np.array(no_label_data[4*no_num:])

            five_fold.append(np.concatenate([fold_pos, fold_neg, fold_no], axis=0))
    return five_fold


def data_generate(five_fold_data):
    reconstructed = list()
    for i in range(5):
        train = list()
        for j in range(5):
            if i == j:
                continue
            train.append(five_fold_data[j])
        train = np.concatenate([train[0], train[1], train[2], train[3]], axis=0)
        train_data = train[:, :-1]
        train_label = train[:, -1]

        test = []
        for item in five_fold_data[i]:
            if item[-1] != 0:
                test.append(item)
        test = np.array(test)
        test_label = test[:, -1]
        test_data = test[:, : -1]

        reconstructed.append([train_data, train_label, test_data, test_label])
    return reconstructed


def write_data(data, label, data_path, label_path):
    data_to_write = []
    for case in data:
        line_string = str()
        for index, item in enumerate(case):
            line_string += str(index+1)+':'+str(item)+" "
        line_string = line_string[:-1]+'\n'
        data_to_write.append(line_string)

    label_to_write = []
    for case in label:
        label_to_write.append(str(int(case))+"\n")

    with open(data_path, 'w', encoding='utf-8') as file:
        for item in data_to_write:
            file.write(item)
    with open(label_path, 'w', encoding='utf-8') as file:
        for item in label_to_write:
            file.write(item)


def semi_supervised_data_generate():
    source_data_path = os.path.abspath('..\\resource\\Data\\source_data_imputed_with_HF_database.csv')
    data = read_data(source_data_path)
    print()
    thirty_day_readmit, one_year_readmit, cardio_death, all_cause_death = event_split(data)
    thirty_day_readmit_5_fold = five_fold_split(thirty_day_readmit)
    one_year_readmit_5_fold = five_fold_split(one_year_readmit)
    cardio_death_5_fold = five_fold_split(cardio_death)
    all_cause_death_5_fold = five_fold_split(all_cause_death)

    thirty_day_readmit_data = data_generate(thirty_day_readmit_5_fold)
    one_year_readmit_data = data_generate(one_year_readmit_5_fold)
    cardio_death_data = data_generate(cardio_death_5_fold)
    all_cause_death_data = data_generate(all_cause_death_5_fold)

    thirty_day_readmit_path = os.path.abspath('..\\resource\\Data\\svm_data\\30_day_readmit')
    one_year_readmit_path = os.path.abspath('..\\resource\\Data\\svm_data\\1_year_readmit')
    cardio_death_path = os.path.abspath('..\\resource\\Data\\svm_data\\cardio_death')
    all_cause_death_path = os.path.abspath('..\\resource\\Data\\svm_data\\all_cause_death')
    data_dict = {'30_day': [thirty_day_readmit_data, thirty_day_readmit_path],
                 '1_year': [one_year_readmit_data, one_year_readmit_path],
                 'all_cause': [all_cause_death_data, all_cause_death_path],
                 'cardio': [cardio_death_data,cardio_death_path]}

    for key in data_dict:
        data, path = data_dict[key]
        for i in range(5):
            train_data, train_label, test_data, test_label = data[i]
            train_data_path = os.path.join(path, str(i)+'trd')
            train_label_path = os.path.join(path, str(i) + 'trl')
            test_data_path = os.path.join(path, str(i) + 'ted')
            test_label_path = os.path.join(path, str(i) + 'tel')
            write_data(train_data, train_label, train_data_path, train_label_path)
            write_data(test_data, test_label, test_data_path, test_label_path)

    print('finish')


def main():
    semi_supervised_data_generate()


if __name__ == "__main__":
    main()
