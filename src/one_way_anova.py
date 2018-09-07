# encoding=utf-8
import scipy.stats as stat
import os
import csv
import data_impute


def import_data(source_file_path):
    source_data = data_impute.read_data(path=source_file_path, encoding='gbk')
    unlabeled_data = dict()
    labeled_data = dict()
    thirty_day_readmit = dict()
    one_year_readmit = dict()
    all_cause_death = dict()

    # set head
    for patient_id in source_data:
        single_patient = source_data[patient_id]
        for feature in single_patient:
            if feature == '30天心源性再住院' or feature == '1年内心源性再住院' or feature == '全因死亡' \
                    or feature == '心源性死亡' or feature == '标签' or feature == 'patient_id':
                continue
            unlabeled_data[feature] = list()
            labeled_data[feature] = list()
            thirty_day_readmit[feature] = list()
            one_year_readmit[feature] = list()
            all_cause_death[feature] = list()
        break

    # set value
    for patient_id in source_data:
        single_patient = source_data[patient_id]
        for feature in single_patient:
            if feature == '30天心源性再住院' or feature == '1年内心源性再住院' or feature == '全因死亡' \
                    or feature == '心源性死亡'or feature == '标签' or feature == 'patient_id':
                continue
            if single_patient['30天心源性再住院'] == '1':
                thirty_day_readmit[feature].append(float(single_patient[feature]))
            if single_patient['1年内心源性再住院'] == '1':
                one_year_readmit[feature].append(float(single_patient[feature]))
            if single_patient['全因死亡'] == '1':
                all_cause_death[feature].append(float(single_patient[feature]))
            if single_patient['标签'] == '1':
                labeled_data[feature].append(float(single_patient[feature]))
            else:
                unlabeled_data[feature].append(float(single_patient[feature]))

    return unlabeled_data, labeled_data, thirty_day_readmit, one_year_readmit, all_cause_death


def main():
    source_data_path = os.path.abspath('..\\resource\\合并数据集.csv')
    unlabeled_data, labeled_data, thirty_day_readmit, one_year_readmit, all_cause_death = import_data(source_data_path)

    data_to_write = list()
    data_to_write.append(['key', 'f_value', 'p_value'])
    for key in unlabeled_data:
        unlabeled_data_key = unlabeled_data[key]
        all_cause_death_key = all_cause_death[key]
        labeled_data_key = labeled_data[key]
        thirty_day_readmit_key = thirty_day_readmit[key]
        one_year_readmit_key = one_year_readmit[key]
        f_value, p_value = stat.f_oneway(all_cause_death_key,
                                         thirty_day_readmit_key, one_year_readmit_key)
        data_to_write.append([key, f_value, p_value])

    target_file_path = os.path.abspath('..\\resource\\组别差异显著性分析.csv')
    with open(target_file_path, 'w', encoding='utf-8-sig', newline="") as file:
        csv_writer = csv.writer(file)
        csv_writer.writerows(data_to_write)


if __name__ == '__main__':
    main()
