# encoding=utf-8
import os
import csv
import performance
import numpy as np


def read_data():
    root = os.path.abspath('..\\resource\\data\\')
    head_data_path = os.path.join(root, 'general_preprocessed.csv')
    one_year_path = os.path.join(root, 'svm_data\\1_year_readmit')
    thirty_day_path = os.path.join(root, 'svm_data\\30_day_readmit')
    cardio_path = os.path.join(root, 'svm_data\\cardio_death')
    all_cause_path = os.path.join(root, 'svm_data\\all_cause_death')
    path_dict = {'1y': one_year_path, '30d': thirty_day_path, 'cardio': cardio_path, 'all': all_cause_path}

    # read_label
    one_year_label = performance.read_label(one_year_path)
    thirty_day_label = performance.read_label(thirty_day_path)
    cardio_label = performance.read_label(cardio_path)
    all_cause_label = performance.read_label(all_cause_path)
    label_dict = {'30d': thirty_day_label, '1y': one_year_label, 'cardio': cardio_label, 'all': all_cause_label}

    # 参数值由观察结果中AUC最佳的实验数据得到
    one_year_prediction = performance.read_result(path_dict['1y'], u=1, w=1)
    thirty_day_prediction = performance.read_result(path_dict['30d'], u=10, w=0.01)
    cardio_prediction = performance.read_result(path_dict['cardio'], u=100, w=0.1)
    all_prediction = performance.read_result(path_dict['all'], u=10, w=0.1)
    predict_dict = {'30d': thirty_day_prediction, '1y': one_year_prediction, 'cardio': cardio_prediction,
                    'all': all_prediction}

    # 读取数据
    data_dict = dict()
    for key in path_dict:
        data_dict[key] = read_feature(path=path_dict[key])

    # 读取标题
    head = read_head(head_data_path)

    return label_dict, predict_dict, data_dict, head


def read_head(head_data_path):
    head = []
    with open(head_data_path, 'r', encoding='gbk') as file:
        csv_reader = csv.reader(file)
        for line in csv_reader:
            for item in line:
                head.append(item)
            break
    head = head[1:-5]
    return head


def read_feature(path):
    data_value = list()
    for i in range(5):
        batch = list()
        with open(os.path.join(path, '{}ted'.format(i)), 'r') as file:
            data = file.readlines()
            for line in data:
                line_value = []
                features = line.split(' ')
                for feature in features:
                    feature_value = float(feature.split(":")[1])
                    line_value.append(feature_value)
                batch.append(line_value)
        data_value.append(batch)
    return data_value


def get_mean(label_dict, predict_dict, data_dict, head):
    measure = dict()
    # 获取数据
    for key in label_dict:
        measure[key] = {'tp': list(), 'tn': list(), 'fp': list(), 'fn': list()}
        label = []
        pred = []
        data = []
        for i in range(5):
            for j in range(len(label_dict[key][i])):
                label.append(label_dict[key][i][j])
                if predict_dict[key][i][j] > 0:
                    pred.append(1)
                else:
                    pred.append(0)
                data.append(data_dict[key][i][j])
        for i in range(len(label)):
            if label[i] == 1 and pred[i] == 1:
                measure[key]['tp'].append(data[i])
            if label[i] == 1 and pred[i] == 0:
                measure[key]['fn'].append(data[i])
            if label[i] == -1 and pred[i] == 1:
                measure[key]['fp'].append(data[i])
            if label[i] == -1 and pred[i] == 0:
                measure[key]['tn'].append(data[i])

    # 获取均值
    for key in measure:
        for pred in measure[key]:
            sample = np.array(measure[key][pred])
            sample = np.mean(sample, axis=0)
            measure[key][pred] = sample

    measure_with_tag = dict()
    for key in measure:
        measure_with_tag[key] = dict()
        for pred in measure[key]:
            measure_with_tag[key][pred] = dict()
            for i in range(len(measure[key][pred])):
                measure_with_tag[key][pred][head[i]] = measure[key][pred][i]
    return measure_with_tag


def main():
    label_dict, predict_dict, data_dict, head = read_data()
    measure_with_tag = get_mean(label_dict, predict_dict, data_dict, head)

    root = os.path.abspath('..\\resource\\data\\')
    for key in measure_with_tag:
        data_to_write = []

        # head
        head = list()
        head.append('指标')
        for measure in measure_with_tag[key]:
            for item in measure_with_tag[key][measure]:
                head.append(item)
            break
        data_to_write.append(head)

        # item
        for measure in measure_with_tag[key]:
            line = list()
            line.append(measure)
            for item in measure_with_tag[key][measure]:
                line.append(measure_with_tag[key][measure][item])
            data_to_write.append(line)

        # transpose
        data_t = []
        for i in range(len(data_to_write[0])):
            line = list()
            line.append(data_to_write[0][i])
            line.append(data_to_write[1][i])
            line.append(data_to_write[2][i])
            line.append(data_to_write[3][i])
            line.append(data_to_write[4][i])
            data_t.append(line)

        path = os.path.join(root, key+'_error_analysis.csv')
        with open(path, 'w', encoding='utf-8-sig', newline="") as file:
            csv_writer = csv.writer(file)
            csv_writer.writerows(data_t)


if __name__ == '__main__':
    main()
