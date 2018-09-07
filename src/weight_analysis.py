# encoding=utf-8
import os
import csv
import error_analysis
import numpy as np


def read_data():
    root = os.path.abspath('..\\resource\\data\\')
    head_data_path = os.path.join(root, 'general_preprocessed.csv')
    one_year_path = os.path.join(root, 'svm_data\\1_year_readmit')
    thirty_day_path = os.path.join(root, 'svm_data\\30_day_readmit')
    cardio_path = os.path.join(root, 'svm_data\\cardio_death')
    all_cause_path = os.path.join(root, 'svm_data\\all_cause_death')

    # read_weight
    one_year_weight = read_weight(one_year_path, u=1, w=1)
    thirty_day_weight = read_weight(thirty_day_path, u=10, w=0.01)
    cardio_weight = read_weight(cardio_path, u=100, w=0.1)
    all_cause_weight = read_weight(all_cause_path, u=10, w=0.1)
    weight_semi = {'30d': thirty_day_weight, '1y': one_year_weight, 'cardio': cardio_weight, 'all': all_cause_weight}

    one_year_weight = read_weight(one_year_path, svm=True)
    thirty_day_weight = read_weight(thirty_day_path, svm=True)
    cardio_weight = read_weight(cardio_path, svm=True)
    all_cause_weight = read_weight(all_cause_path, svm=True)
    weight_svm = {'30d': thirty_day_weight, '1y': one_year_weight, 'cardio': cardio_weight, 'all': all_cause_weight}

    head = error_analysis.read_head(os.path.join(root, head_data_path))
    return weight_svm, weight_semi, head


def read_weight(path, u=None, w=None, svm=False):
    if not svm and (u is None or w is None):
        raise ValueError('')
    if svm and (u is not None or w is not  None):
        raise ValueError('')

    if u is not None and w is not None and svm:
        weight = []
        for i in range(5):
            batch = []
            with open(os.path.join(path, 'u{}w{}'.format(u, w)+'\\'+str(i)+'trd.weights'), 'r') as file:
                lines = file.readlines()
                for item in lines:
                    item_int = float(item.replace('\n', ''))
                    batch.append(item_int)
            weight.append(batch)
        weight = np.mean(np.array(weight), axis=0)
    else:
        weight = []
        for i in range(5):
            with open(os.path.join(path, 'svm\\' + str(i) + 'trd.weights'), 'r') as file:
                batch = []
                lines = file.readlines()
                for item in lines:
                    item_int = float(item.replace('\n', ''))
                    batch.append(item_int)
            weight.append(batch)
        weight = np.mean(np.array(weight), axis=0)
    return weight


def main():
    weight_svm, weight_semi, head = read_data()
    weight_svm_with_tag = dict()
    weight_semi_with_tag = dict()
    for key in weight_svm:
        weight_svm_with_tag[key] = dict()
        for i in range(len(head)):
            weight_svm_with_tag[key][head[i]] = weight_svm[key][i]
    for key in weight_semi:
        weight_semi_with_tag[key] = dict()
        for i in range(len(head)):
            weight_semi_with_tag[key][head[i]] = weight_semi[key][i]
    root = os.path.abspath('..\\resource\\data\\')

    for key in weight_semi_with_tag:
        data_to_write = []

        # head
        head = list()
        for measure in weight_semi_with_tag[key]:
            head.append(measure)
        data_to_write.append(head)

        # item
        line = list()
        for measure in weight_semi_with_tag[key]:
            line.append(weight_semi_with_tag[key][measure])
        data_to_write.append(line)

        path = os.path.join(root, key+'_semi_weight_analysis.csv')
        with open(path, 'w', encoding='utf-8-sig', newline="") as file:
            csv_writer = csv.writer(file)
            csv_writer.writerows(data_to_write)

    for key in weight_svm_with_tag:
        data_to_write = []

        # head
        head = list()
        for measure in weight_svm_with_tag[key]:
            head.append(measure)
        data_to_write.append(head)

        # item
        line = list()
        for measure in weight_svm_with_tag[key]:
            line.append(weight_svm_with_tag[key][measure])
        data_to_write.append(line)

        path = os.path.join(root, key+'_svm_weight_analysis.csv')
        with open(path, 'w', encoding='utf-8-sig', newline="") as file:
            csv_writer = csv.writer(file)
            csv_writer.writerows(data_to_write)


if __name__ == '__main__':
    main()