# encoding=utf-8
import os
import csv


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
        with open(os.path.join(file_path, str(i) + 'ted.outputs'), 'r') as file:
            lines = file.readlines()
            for item in lines:
                item_float = float(item)
                if item_float > 0:
                    item_int = 1
                else:
                    item_int = -1
                prediction.append(item_int)
    return prediction


def read_label(path):
    label = []
    for i in range(5):
        with open(os.path.join(path, str(i)+'tel'), 'r') as file:
            lines = file.readlines()
            for item in lines:
                item_int = int(item)
                label.append(item_int)
    return label


def get_confusion_mat(prediction, label):
    tp = 0
    tn = 0
    fp = 0
    fn = 0
    for i in range(len(prediction)):
        if prediction[i] == 1 and label[i] == 1:
            tp += 1
        elif prediction[i] == 1 and label[i] == -1:
            fp += 1
        elif prediction[i] == -1 and label[i] == -1:
            tn += 1
        elif prediction[i] == -1 and label[i] == 1:
            fn += 1
        else:
            raise ValueError('')
    return tp, tn, fp, fn


def performance_eval(tp, tn, fp, fn, item):
    acc = (tp+tn)/(tp+tn+fp+fn)
    if tp+fn != 0:
        recall = tp/(tp+fn)
    else:
        recall = -1
    if tp+fp != 0:
        precision = tp/(tp+fp)
    else:
        precision = -1
    f1 = 2*tp/(2*tp+fp+fn)
    specificity = tn/(tn+fp)

    print_str = '%10s acc: %2.4f, recall: %2.4f, precision: %2.4f, f1: %.4f, specificity: %2.4f'\
                % (item, acc, recall, precision, f1, specificity)
    print(print_str)
    return {'acc': acc, 'recall': recall, 'precision': precision, 'f1': f1, 'specificity': specificity}


def find_best(performance_svm, performance_semi_svm):
    best_dict = {}
    for item in performance_svm:
        best_dict[item] = dict()
        best_dict[item]['svm'] = performance_svm[item]

        best_acc = -1
        best_recall = -1
        best_precision = -1
        best_f1 = -1
        best_specificity = -1

        for case in performance_semi_svm[item]:
            acc = performance_semi_svm[item][case]['acc']
            recall = performance_semi_svm[item][case]['recall']
            precision = performance_semi_svm[item][case]['precision']
            f1 = performance_semi_svm[item][case]['f1']
            specificity = performance_semi_svm[item][case]['specificity']
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
            if specificity > best_specificity:
                best_specificity = specificity
                best_dict[item]['specificity'] = performance_semi_svm[item][case]
    return best_dict


def write_best(path, best_dict):
    with open(path, 'w', encoding='utf-8-sig', newline="") as file:
        csv_writer = csv.writer(file)
        data_to_write = []

        # write head
        head = list()
        head.append("")
        head.append("best measurement")
        for case in best_dict:
            for stat_type in best_dict[case]:
                head.append(stat_type)
            break
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


def main():
    root = os.path.abspath('..\\resource\\data\\svm_data\\')
    one_year_path = os.path.join(root, '1_year_readmit')
    thirty_day_path = os.path.join(root, '30_day_readmit')
    cardio_path = os.path.join(root, 'cardio_death')
    all_cause_path = os.path.join(root, 'all_cause_death')
    path_dict = {'1y': one_year_path, '30d': thirty_day_path,  'cardio': cardio_path, 'all': all_cause_path}

    # read_label
    one_year_label = read_label(one_year_path)
    thirty_day_label = read_label(thirty_day_path)
    cardio_label = read_label(cardio_path)
    all_cause_label = read_label(all_cause_path)
    label_dict = {'30d': thirty_day_label, '1y': one_year_label, 'cardio': cardio_label, 'all': all_cause_label}

    performance_svm = dict()
    performance_semi_svm = dict()
    for item in path_dict:
        print('svm')
        prediction = read_result(path_dict[item], svm='svm')
        label = label_dict[item]
        tp, tn, fp, fn = get_confusion_mat(prediction, label)
        performance_svm[item] = performance_eval(tp, tn, fp, fn, item)

        performance_semi_svm[item] = dict()
        for u in [0.0001, 0.001, 0.01, 0.1, 1, 10, 100]:
            for w in [0.0001, 0.001, 0.01, 0.1, 1, 10, 100]:
                print('semi-svm, u = {0}, w = {1}'.format(u, w))
                prediction = read_result(path_dict[item], u=u, w=w)
                label = label_dict[item]
                tp, tn, fp, fn = get_confusion_mat(prediction, label)
                key_name = '{}u{}w{}'.format(item, u, w)
                performance_semi_svm[item][key_name] = performance_eval(tp, tn, fp, fn, item)

    best_dict = find_best(performance_svm, performance_semi_svm)
    write_best(os.path.join(root, 'best_result_dict.csv'), best_dict)


if __name__ == "__main__":
    main()
