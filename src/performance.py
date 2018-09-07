# encoding=utf-8
import os
import csv
import datetime
import math


def read_result(path, u=None, w=None, svm=None):
    if svm is None and (u is None or w is None):
        raise ValueError('')
    if u is not None and w is not None:
        folder = 'u'+str(u)+'w'+str(w)
    elif svm is not None:
        folder = 'svm'
    else:
        raise ValueError('')
    file_path = os.path.join(path, folder)
    prediction = []
    for i in range(5):
        batch = []
        with open(os.path.join(file_path, str(i) + 'ted.outputs'), 'r') as file:
            lines = file.readlines()
            for item in lines:
                item_float = float(item)
                batch.append(item_float)
        prediction.append(batch)
    return prediction


def read_label(path):
    label = []
    for i in range(5):
        batch = []
        with open(os.path.join(path, str(i)+'tel'), 'r') as file:
            lines = file.readlines()
            for item in lines:
                item_int = int(item)
                batch.append(item_int)
        label.append(batch)
    return label


def get_confusion_mat(prediction, label):
    tp = 0
    tn = 0
    fp = 0
    fn = 0
    for i in range(len(prediction)):
        if prediction[i] == 1 and label[i] == 1:
            tp += 1
        elif prediction[i] == 1 and label[i] == 0:
            fp += 1
        elif prediction[i] == 0 and label[i] == 0:
            tn += 1
        elif prediction[i] == 0 and label[i] == 1:
            fn += 1
        else:
            raise ValueError('')
    return tp, tn, fp, fn


def performance_eval(prediction, label):
    auc, auc_ci = get_auc(prediction, label)

    def single_batch_performance(prediction_, label_):
        calibration_pred = list()
        calibration_label = list()
        for item_ in prediction_:
            if item_ > 0:
                calibration_pred.append(1)
            else:
                calibration_pred.append(0)
        for item_ in label_:
            if item_ > 0:
                calibration_label.append(1)
            else:
                calibration_label.append(0)
        prediction_ = calibration_pred
        label_ = calibration_label

        tp, tn, fp, fn = get_confusion_mat(prediction_, label_)
        acc_ = (tp + tn) / (tp + tn + fp + fn)
        if tp + fn != 0:
            recall_ = tp / (tp + fn)
        else:
            recall_ = -1
        if tp + fp != 0:
            precision_ = tp / (tp + fp)
        else:
            precision_ = -1
        f1_ = 2 * tp / (2 * tp + fp + fn)
        return {'acc': acc_, 'precision': precision_, 'recall': recall_, 'f1': f1_}

    performance_list = []
    for k in range(len(prediction)):
        performance_list.append(single_batch_performance(prediction[k], label[k]))
    # mean
    acc = 0
    precision = 0
    recall = 0
    f1 = 0
    for item in performance_list:
        acc += item['acc'] / len(performance_list)
        precision += item['precision'] / len(performance_list)
        recall += item['recall'] / len(performance_list)
        f1 += item['f1'] / len(performance_list)

    acc_ci = 0
    precision_ci = 0
    recall_ci = 0
    f1_ci = 0
    for item in performance_list:
        acc_ci += (item['acc'] - acc) ** 2 / (len(performance_list) - 1)
        precision_ci += (item['acc'] - acc) ** 2 / (len(performance_list) - 1)
        recall_ci += (item['acc'] - acc) ** 2 / (len(performance_list) - 1)
        f1_ci += (item['acc'] - acc) ** 2 / (len(performance_list) - 1)
    acc_ci = 1.96 * math.sqrt(acc_ci) / math.sqrt(len(performance_list))
    precision_ci = 1.96 * math.sqrt(precision_ci) / math.sqrt(len(performance_list))
    recall_ci = 1.96 * math.sqrt(recall_ci) / math.sqrt(len(performance_list))
    f1_ci = 1.96 * math.sqrt(f1_ci) / math.sqrt(len(performance_list))

    result_dict = dict()
    result_dict['auc'] = auc
    result_dict['acc'] = acc
    result_dict['precision'] = precision
    result_dict['recall'] = recall
    result_dict['f1'] = f1
    result_dict['auc_ci'] = auc_ci
    result_dict['acc_ci'] = acc_ci
    result_dict['precision_ci'] = precision_ci
    result_dict['recall_ci'] = recall_ci
    result_dict['f1_ci'] = f1_ci
    return result_dict


def find_best_performance(performance_svm, performance_semi_svm):
    best_dict = {}
    for item in performance_svm:
        best_dict[item] = dict()
        best_dict[item]['svm'] = performance_svm[item]

        best_auc = -1
        best_acc = -1
        best_recall = -1
        best_precision = -1
        best_f1 = -1

        for case in performance_semi_svm[item]:
            auc = performance_semi_svm[item][case]['auc']
            acc = performance_semi_svm[item][case]['acc']
            recall = performance_semi_svm[item][case]['recall']
            precision = performance_semi_svm[item][case]['precision']
            f1 = performance_semi_svm[item][case]['f1']
            if auc > best_auc:
                best_auc = auc
                best_dict[item]['auc'] = performance_semi_svm[item][case]
            if acc > best_acc:
                best_acc = acc
                best_dict[item]['acc'] = performance_semi_svm[item][case]
            if recall > best_recall:
                best_recall = recall
                best_dict[item]['recall'] = performance_semi_svm[item][case]
            if precision > best_precision:
                best_precision = precision
                best_dict[item]['precision'] = performance_semi_svm[item][case]
            if f1 > best_f1:
                best_f1 = f1
                best_dict[item]['f1'] = performance_semi_svm[item][case]
    return best_dict


def get_auc(prediction, label):
    def single_batch_auc(pred_, label_):
        pos_index_list = list()
        neg_index_list = list()
        for i in range(len(label_)):
            if label_[i] == 1:
                pos_index_list.append(i)
            else:
                neg_index_list.append(i)
        great_sum = 0
        for i in pos_index_list:
            for j in neg_index_list:
                if pred_[i] > pred_[j]:
                    great_sum += 1
        auc_ = great_sum / (len(pos_index_list) * len(neg_index_list))
        return auc_
    auc_list = []
    for k in range(len(prediction)):
        auc_list.append(single_batch_auc(prediction[k], label[k]))
    # mean auc
    auc = 0
    for item in auc_list:
        auc += item / len(auc_list)
    # confidence interval
    ci = 0
    for item in auc_list:
        ci += (auc-item)**2 / (len(auc_list) - 1)
    ci = 1.96 * math.sqrt(ci) / math.sqrt(len(auc_list))
    return auc, ci


def write_best_performance(path, best_dict):
    with open(path, 'w', encoding='utf-8-sig', newline="") as file:
        csv_writer = csv.writer(file)
        data_to_write = []

        # write head
        head = ["best measurement", 'type', 'auc', 'acc', 'precision', 'recall', 'f1', 'auc_ci', 'acc_ci',
                'precision_ci', 'recall_ci', 'f1_ci']
        data_to_write.append(head)
        for case in best_dict:
            for stat_type in best_dict[case]:
                line = list()
                line.append(case)
                line.append(stat_type)
                for stat in best_dict[case][stat_type]:
                    line.append(best_dict[case][stat_type][stat])
                data_to_write.append(line)
        csv_writer.writerows(data_to_write)


def declie_analysis(prediction, label):
    combine = list()
    declie_list = list()
    for i in range(len(prediction)):
        for j in range(len(prediction[i])):
            combine.append([prediction[i][j], label[i][j]])
    combine = sorted(combine, key=lambda x: x[0])
    declie_number = len(combine)//10
    for i in range(10):
        declie_list.append(0)
        start_index = declie_number*i
        if i == 9:
            end_index = len(combine)
        else:
            end_index = declie_number*(i+1)
        for j in range(start_index, end_index):
            if combine[j][1] == 1:
                declie_list[i] += 1

    for i in range(len(declie_list)):
        if i != 9:
            declie_list[i] = declie_list[i]/declie_number
        else:
            declie_list[i] = declie_list[i] / (declie_number+len(combine) % 10)
    return declie_list


def find_best_declie(svm_declie_dict, semi_declie_dict, best_dict):
    # 以AUC最高结果的为十分位输出
    best_declie = dict()
    for item in best_dict:
        key = best_dict[item]['auc']['para']
        best_declie[item] = [semi_declie_dict[item][key], svm_declie_dict[item]]
    return best_declie


def write_best_declie(best_declie, path):
    data_to_write = list()
    # head
    data_to_write.append(['type', 'model', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10'])
    for key in best_declie:
        svm_list = list()
        semi_list = list()
        svm_list.append(key)
        semi_list.append(key)
        svm_list.append('svm')
        semi_list.append('semi_svm')
        for item in best_declie[key][0]:
            semi_list.append(item)
        for item in best_declie[key][1]:
            svm_list.append(item)
        data_to_write.append(svm_list)
        data_to_write.append(semi_list)
        data_to_write.append([''])
    with open(path, 'w', encoding='utf-8-sig', newline="") as file:
        csv_writer = csv.writer(file)
        csv_writer.writerows(data_to_write)


def main():
    root = os.path.abspath('..\\resource\\data\\')
    one_year_path = os.path.join(root, 'svm_data\\1_year_readmit')
    thirty_day_path = os.path.join(root, 'svm_data\\30_day_readmit')
    cardio_path = os.path.join(root, 'svm_data\\cardio_death')
    all_cause_path = os.path.join(root, 'svm_data\\all_cause_death')
    path_dict = {'1y': one_year_path, '30d': thirty_day_path,  'cardio': cardio_path, 'all': all_cause_path}

    # read_label
    one_year_label = read_label(one_year_path)
    thirty_day_label = read_label(thirty_day_path)
    cardio_label = read_label(cardio_path)
    all_cause_label = read_label(all_cause_path)
    label_dict = {'30d': thirty_day_label, '1y': one_year_label, 'cardio': cardio_label, 'all': all_cause_label}

    performance_svm = dict()
    performance_semi_svm = dict()
    svm_declie_dict = dict()
    semi_declie_dict = dict()
    for item in path_dict:
        prediction = read_result(path_dict[item], svm='svm')
        label = label_dict[item]
        result_list = performance_eval(prediction, label)
        result_list['para'] = 'svm'
        performance_svm[item] = result_list
        svm_declie_dict[item] = declie_analysis(prediction, label)

        performance_semi_svm[item] = dict()
        semi_declie_dict[item] = dict()
        for u in [0.001, 0.01, 0.1, 1, 10, 100]:
            for w in [0.001, 0.01, 0.1, 1, 10, 100]:
                prediction = read_result(path_dict[item], u=u, w=w)
                label = label_dict[item]
                key_name = '{}u{}w{}'.format(item, u, w)
                result_list = performance_eval(prediction, label)
                result_list['para'] = key_name
                performance_semi_svm[item][key_name] = result_list
                semi_declie_dict[item][key_name] = declie_analysis(prediction, label)

    now = datetime.datetime.now().strftime('%Y_%m_%d_%H_%M_%S')
    best_dict = find_best_performance(performance_svm, performance_semi_svm)
    write_best_performance(os.path.join(root, 'svm_result_{}.csv'.format(now)), best_dict)
    best_decile = find_best_declie(svm_declie_dict, semi_declie_dict, best_dict)
    write_best_declie(best_decile, os.path.join(root, 'svm_declie_{}.csv'.format(now)))


if __name__ == "__main__":
    main()
