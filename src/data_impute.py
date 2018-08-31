# encoding=utf-8
import os
import csv
import re


def find_type(data):
    # 将数据分为两类，category(所有数据要不为0，要不为1)和numerical（数据是数值型）
    type_dict = dict()
    for patient_id in data:
        for item in data[patient_id]:
            type_dict[item] = 'Categorical'
        break
    for patient_id in data:
        for feature in data[patient_id]:
            value = re.findall('[-+]?[.]?[\d]+(?:,\d\d\d)*[\.]?\d*(?:[eE][-+]?\d+)?', data[patient_id][feature])
            value = float(value[0])
            if value == -1.0:
                continue
            if value != 1.0 and value != 0.0:
                type_dict[feature] = 'Numerical'
    return type_dict


def impute(data):
    # category数据填充0，numerical填充平均数
    type_dict = find_type(data)

    # find mean
    count_dict = dict()
    sum_dict = dict()
    for item in type_dict:
        count_dict[item] = 0
        sum_dict[item] = 0
    for patient_id in data:
        for item in data[patient_id]:
            value = re.findall('[-+]?[.]?[\d]+(?:,\d\d\d)*[\.]?\d*(?:[eE][-+]?\d+)?', data[patient_id][item])
            value = float(value[0])
            if value != -1.0:
                count_dict[item] += 1
                sum_dict[item] += value

    mean_dict = dict()
    for item in count_dict:
        if count_dict[item] == 0:
            mean_dict[item] = 0
        else:
            mean_dict[item] = sum_dict[item]/count_dict[item]

    # category数据填充0，numerical填充平均数
    for patient_id in data:
        for item in data[patient_id]:
            value = re.findall('[-+]?[.]?[\d]+(?:,\d\d\d)*[\.]?\d*(?:[eE][-+]?\d+)?', data[patient_id][item])
            value = float(value[0])
            if value != -1.0:
                continue

            if type_dict[item] == 'Numerical':
                data[patient_id][item] = mean_dict[item]
            elif type_dict[item] == 'Categorical':
                data[patient_id][item] = 0
            else:
                raise ValueError('Value Error')
    return data, type_dict


def missing_rate_stat(data, path):
    missing_rate_dict = dict()
    # set dict
    for patient_id in data:
        for item in data[patient_id]:
            missing_rate_dict[item] = 0
        break

    for patient_id in data:
        for item in data[patient_id]:
            if str(data[patient_id][item]) == '-1':
                missing_rate_dict[item] += 1

    for item in missing_rate_dict:
        missing_rate_dict[item] = missing_rate_dict[item]/len(data)

    with open(path, 'w', encoding='utf-8-sig', newline="") as file:
        matrix_to_write = list()
        matrix_to_write.append(['属性', '丢失率'])
        for item in missing_rate_dict:
            matrix_to_write.append([item, missing_rate_dict[item]])

        csv_writer = csv.writer(file)
        csv_writer.writerows(matrix_to_write)
    return missing_rate_dict


def normalization(data, type_dict):
    # 对数据做zero mean unit variance 处理
    mean_dict = dict()
    stdev_dict = dict()

    for item in type_dict:
        mean_dict[item] = 0
        stdev_dict[item] = 0

    for patient_id in data:
        for item in data[patient_id]:
            value_ = float(data[patient_id][item])
            mean_dict[item] += value_

    for item in mean_dict:
        mean_dict[item] = mean_dict[item]/len(data)

    for patient_id in data:
        for item in data[patient_id]:
            stdev_dict[item] += (float(data[patient_id][item])-mean_dict[item])**2
    for item in stdev_dict:
        stdev_dict[item] = (stdev_dict[item] / len(data))**0.5
        if stdev_dict[item] == 0 or stdev_dict[item] == 0.0:
            stdev_dict[item] = 1

    for patient_id in data:
        for item in data[patient_id]:
            if type_dict[item] == 'Numerical':
                data[patient_id][item] = (float(data[patient_id][item])-mean_dict[item])/stdev_dict[item]
    return data


def read_data(path, encoding):
    data_dict = dict()
    with open(path, 'r', encoding=encoding, newline="") as file:
        csv_reader = csv.reader(file)
        head_dict = dict()
        for i, line in enumerate(csv_reader):
            if i == 0:
                for j, item in enumerate(line):
                    head_dict[j] = item
            else:
                for j, item in enumerate(line):
                    if j == 0:
                        data_dict[item] = dict()
                    else:
                        data_dict[line[0]][head_dict[j]] = item
    return data_dict


def main():
    # source_file_path = os.path.abspath('..\\resource\\HFDatabase\\general_stat_no_impute.csv')
    # impute_file_path = os.path.abspath('..\\resource\\HFDatabase\\general_stat_imputed.csv')
    # missing_rate_path = os.path.abspath('..\\resource\\HFDatabase\\hf_database_missing_rate.csv')

    source_file_path = os.path.abspath('..\\resource\\general_stat_no_impute.csv')
    impute_file_path = os.path.abspath('..\\resource\\general_preprocessed.csv')
    missing_rate_path = os.path.abspath('..\\resource\\missing_rate.csv')

    source_data = read_data(path=source_file_path, encoding='utf-8-sig')
    missing_rate_dict = missing_rate_stat(source_data, missing_rate_path)
    imputed_data, type_dict = impute(source_data)
    imputed_data = normalization(imputed_data, type_dict)

    with open(impute_file_path, 'w', encoding='utf-8-sig', newline="") as file:
        matrix_to_write = []
        head_list = ['patient_id']
        type_list = ["data type"]
        missing_list = ["missing rate"]
        for patient_id in imputed_data:
            for item in imputed_data[patient_id]:
                head_list.append(item)
                type_list.append(type_dict[item])
                missing_list.append(missing_rate_dict[item])
            break
        matrix_to_write.append(head_list)
        matrix_to_write.append(type_list)
        matrix_to_write.append(missing_list)

        for patient_id in imputed_data:
            line = [patient_id]
            for item in imputed_data[patient_id]:
                line.append(imputed_data[patient_id][item])
            matrix_to_write.append(line)

        csv_writer = csv.writer(file)
        csv_writer.writerows(matrix_to_write)


if __name__ == "__main__":
    main()
