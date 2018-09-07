# encoding=utf-8
import os
import file_generate
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import roc_auc_score, accuracy_score, precision_score, recall_score, f1_score
from sklearn import linear_model
from sklearn import neighbors
from sklearn.neural_network import MLPClassifier
import performance
import csv
import math
"""
使用随机森林，最近邻，逻辑回归和神经网络做出比较
"""


def read_data(source_data_path):
    # 读取数据并拆分成五折交叉验证的形式
    data = file_generate.read_data(source_data_path)
    thirty_day_readmit, one_year_readmit, cardio_death, all_cause_death = file_generate.event_split(data)
    data_5_fold = dict()
    data_5_fold['30d'] = file_generate.five_fold_split(thirty_day_readmit, True)
    data_5_fold['1y'] = file_generate.five_fold_split(one_year_readmit, True)
    data_5_fold['cardio'] = file_generate.five_fold_split(cardio_death, True)
    data_5_fold['all_cause'] = file_generate.five_fold_split(all_cause_death, True)
    # 将-1标签全部设为0
    for key in data_5_fold:
        for i in range(len(data_5_fold[key])):
            for j in range(len(data_5_fold[key][i])):
                if data_5_fold[key][i][j][-1] == -1:
                    data_5_fold[key][i][j][-1] = 0

    # 生成五折交叉验证的数据集
    data_split = dict()
    for key in data_5_fold:
        data_split[key] = dict()
        for i in range(5):
            data_split[key][i] = {'train': [], 'test': None}
            for j in range(len(data_5_fold[key])):
                if i == j:
                    data_split[key][i]['test'] = data_5_fold[key][j]
                else:
                    data_split[key][i]['train'].append(data_5_fold[key][j])
            data_split[key][i]['train'] = np.concatenate(data_split[key][i]['train'], axis=0)
    return data_split


def random_forest(data_split):
    declie_result = dict()
    performance_result = dict()
    for key in data_split:
        declie_result[key] = []
        performance_result[key] = dict()
        for i in range(5):
            test_x, test_y = data_split[key][i]['test'][:, 0: -1], data_split[key][i]['test'][:, -1]
            train_x, train_y = data_split[key][i]['train'][:, 0: -1], data_split[key][i]['train'][:, -1]
            clf = RandomForestClassifier()
            clf.fit(train_x, train_y)

            prediction = clf.predict(test_x)
            probability = clf.predict_proba(test_x)[:, 1]
            auc = roc_auc_score(test_y, probability)
            acc = accuracy_score(test_y, prediction)
            precision = precision_score(test_y, prediction)
            recall = recall_score(test_y, prediction)
            f1 = f1_score(test_y, prediction)
            performance_result[key][i] = {'auc': auc, 'acc': acc, 'precision': precision, 'recall': recall, 'f1': f1}
            declie_result[key].append(performance.declie_analysis(probability, test_y))
    mean_result, mean_declie = evaluate_performance(performance_result, declie_result)
    return mean_result, mean_declie


def logistic_regression(data_split):
    declie_result = dict()
    performance_result = dict()
    for key in data_split:
        declie_result[key] = []
        performance_result[key] = dict()
        for i in range(5):
            test_x, test_y = data_split[key][i]['test'][:, 0: -1], data_split[key][i]['test'][:, -1]
            train_x, train_y = data_split[key][i]['train'][:, 0: -1], data_split[key][i]['train'][:, -1]
            clf = linear_model.LogisticRegression(penalty='l1', tol=1e-6)
            clf.fit(train_x, train_y)

            prediction = clf.predict(test_x)
            probability = clf.predict_proba(test_x)[:, 1]
            auc = roc_auc_score(test_y, probability)
            acc = accuracy_score(test_y, prediction)
            precision = precision_score(test_y, prediction)
            recall = recall_score(test_y, prediction)
            f1 = f1_score(test_y, prediction)
            performance_result[key][i] = {'auc': auc, 'acc': acc, 'precision': precision, 'recall': recall, 'f1': f1}
            declie_result[key].append(performance.declie_analysis(probability, test_y))
    mean_result, mean_declie = evaluate_performance(performance_result, declie_result)
    return mean_result, mean_declie


def neural_network(data_split):
    declie_result = dict()
    performance_result = dict()
    for key in data_split:
        declie_result[key] = []
        performance_result[key] = dict()
        for i in range(5):
            test_x, test_y = data_split[key][i]['test'][:, 0: -1], data_split[key][i]['test'][:, -1]
            train_x, train_y = data_split[key][i]['train'][:, 0: -1], data_split[key][i]['train'][:, -1]
            clf = MLPClassifier(solver='lbfgs', alpha=1e-5, hidden_layer_sizes=(32, 16))
            clf.fit(train_x, train_y)

            prediction = clf.predict(test_x)
            probability = clf.predict_proba(test_x)[:, 1]
            auc = roc_auc_score(test_y, probability)
            acc = accuracy_score(test_y, prediction)
            precision = precision_score(test_y, prediction)
            recall = recall_score(test_y, prediction)
            f1 = f1_score(test_y, prediction)
            performance_result[key][i] = {'auc': auc, 'acc': acc, 'precision': precision, 'recall': recall, 'f1': f1}
            declie_result[key].append(performance.declie_analysis(probability, test_y))
    mean_result, mean_declie = evaluate_performance(performance_result, declie_result)
    return mean_result, mean_declie


def k_neighbors(data_split):
    declie_result = dict()
    performance_result = dict()
    for key in data_split:
        declie_result[key] = []
        performance_result[key] = dict()
        for i in range(5):
            test_x, test_y = data_split[key][i]['test'][:, 0: -1], data_split[key][i]['test'][:, -1]
            train_x, train_y = data_split[key][i]['train'][:, 0: -1], data_split[key][i]['train'][:, -1]
            clf = neighbors.KNeighborsClassifier()
            clf.fit(train_x, train_y)

            predict = clf.predict(test_x)
            probability = clf.predict_proba(test_x)[:, 1]
            p_dict = performance.performance_eval(predict, test_y)
            performance_result[key][i] = {'auc': p_dict['auc'], 'acc': p_dict['acc'], 'precision': p_dict['precision'],
                                          'recall': p_dict['recall'], 'f1': p_dict['f1']}
            declie_result[key].append(performance.declie_analysis(probability, test_y))
    mean_result, mean_declie = evaluate_performance(performance_result, declie_result)
    return mean_result, mean_declie


def evaluate_performance(performance_result, declie_result):
    # 五折交叉验证取平均和95%置信区间
    mean_result = dict()
    mean_declie = dict()
    ci = dict()

    # 计算均值
    for key in performance_result:
        mean_result[key] = {'auc': 0, 'acc': 0, 'precision': 0, 'recall': 0, 'f1': 0}
        mean_declie[key] = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        for i in range(5):
            mean_result[key]['auc'] += performance_result[key][i]['auc'] / 5
            mean_result[key]['acc'] += performance_result[key][i]['acc'] / 5
            mean_result[key]['precision'] += performance_result[key][i]['precision'] / 5
            mean_result[key]['recall'] += performance_result[key][i]['recall'] / 5
            mean_result[key]['f1'] += performance_result[key][i]['f1'] / 5
            for j in range(10):
                mean_declie[key][j] += declie_result[key][i][j] / 5

    # 计算95%置信区间
    for key in performance_result:
        ci[key] = dict()
        ci[key]['auc'] = 0
        ci[key]['acc'] = 0
        ci[key]['precision'] = 0
        ci[key]['recall'] = 0
        ci[key]['f1'] = 0
        for i in range(5):
            ci[key]['auc'] += (mean_result[key]['auc']-performance_result[key][i]['auc'])**2
            ci[key]['acc'] += (mean_result[key]['acc']-performance_result[key][i]['acc'])**2
            ci[key]['precision'] += (mean_result[key]['precision']-performance_result[key][i]['precision'])**2
            ci[key]['recall'] += (mean_result[key]['recall']-performance_result[key][i]['recall'])**2
            ci[key]['f1'] += (mean_result[key]['f1']-performance_result[key][i]['f1'])**2
        ci[key]['auc'] = 1.96*math.sqrt(ci[key]['auc'])/math.sqrt(5)
        ci[key]['acc'] = 1.96 * math.sqrt(ci[key]['acc']) / math.sqrt(5)
        ci[key]['precision'] = 1.96 * math.sqrt(ci[key]['precision']) / math.sqrt(5)
        ci[key]['recall'] = 1.96 * math.sqrt(ci[key]['recall']) / math.sqrt(5)
        ci[key]['f1'] = 1.96 * math.sqrt(ci[key]['f1']) / math.sqrt(5)

    return mean_result, mean_declie, ci


def main():
    root = os.path.abspath('..\\resource\\Data\\')
    source_data_path = os.path.join(root, 'general_preprocessed.csv')
    performance_path = os.path.join(root, 'baseline_result.csv')
    declie_path = os.path.join(root, 'declie_result.csv')

    data_split = read_data(source_data_path)
    rf_result, rf_declie = random_forest(data_split)
    lr_result, lr_declie = logistic_regression(data_split)
    nn_result, nn_declie = neural_network(data_split)
    kn_result, kn_declie = k_neighbors(data_split)
    result_dict = {'rf': rf_result, 'lr': lr_result, 'nn': nn_result, 'kn': kn_result}
    declie_dict = {'rf': rf_declie, 'lr': lr_declie, 'nn': nn_declie, 'kn': kn_declie}

    # write baseline result
    data_to_write = list()
    # write head
    data_to_write.append(['algorithm', 'type', 'auc', 'acc', 'precision', 'recall', 'f1'])
    for algorithm in result_dict:
        for key in result_dict[algorithm]:
            auc = result_dict[algorithm][key]['auc']
            acc = result_dict[algorithm][key]['acc']
            precision = result_dict[algorithm][key]['precision']
            recall = result_dict[algorithm][key]['recall']
            f1 = result_dict[algorithm][key]['f1']
            data_to_write.append([algorithm, key, auc, acc, precision, recall, f1])

    with open(performance_path, 'w', encoding='utf-8-sig', newline="") as file:
        csv_writer = csv.writer(file)
        csv_writer.writerows(data_to_write)
    # write baseline declie
    print('finish')

    # write baseline declie
    data_to_write = list()
    # write head
    data_to_write.append(['algorithm', 'type', '0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10'])
    for algorithm in result_dict:
        for key in result_dict[algorithm]:
            declie = declie_dict[algorithm][key]
            data_to_write.append([algorithm, key, declie[0], declie[1], declie[2], declie[3], declie[4], declie[5],
                                  declie[6], declie[7], declie[8], declie[9]])

    with open(declie_path, 'w', encoding='utf-8-sig', newline="") as file:
        csv_writer = csv.writer(file)
        csv_writer.writerows(data_to_write)
    # write baseline declie
    print('finish')


if __name__ == '__main__':
    main()
