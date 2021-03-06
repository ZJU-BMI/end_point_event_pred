# encoding=utf-8


def write_svm(data_type):
    cmd_list = list()
    cmd_list.append('cd {}'.format(data_type))
    cmd_list.append('mkdir svm')
    for i in range(5):
        cmd_list.append('svmlin -A 0 {}trd {}trl'.format(i, i))
        cmd_list.append('svmlin -f {}trd.weights {}ted {}tel'.format(i, i, i))
        cmd_list.append('copy /Y D:\\PythonProject\\end_point_event_pred\\resource\\Data\\svm_data\\{}\\'
                        '{}ted.outputs D:\\PythonProject\\end_point_event_pred\\resource\\Data\\svm_data\\'
                        '{}\\{}\\{}ted.outputs'.format(data_type, i, data_type, 'svm', i))
        cmd_list.append('copy /Y D:\\PythonProject\\end_point_event_pred\\resource\\Data\\svm_data\\{}\\'
                        '{}trd.weights D:\PythonProject\\end_point_event_pred\\resource\\Data\\svm_data\\'
                        '{}\\svm\\{}trd.weights'.format(data_type, i, data_type, i))
    cmd_list.append('cd ..')
    return cmd_list


def write_semi_svm(data_type, u, w, r):
    cmd_list = list()
    cmd_list.append('cd {}'.format(data_type))
    cmd_list.append('mkdir u{}w{}'.format(u, w))
    for i in range(5):
        cmd_list.append('svmlin -A 2 -W {} -U {} -R {}  {}trd {}trl'.format(w, u, r, i, i))
        cmd_list.append('svmlin -f {}trd.weights {}ted {}tel'.format(i, i, i))
        cmd_list.append('copy /Y D:\\PythonProject\\end_point_event_pred\\resource\\Data\\svm_data\\{}\\'
                        '{}ted.outputs D:\PythonProject\\end_point_event_pred\\resource\\Data\\svm_data\\'
                        '{}\\u{}w{}\\{}ted.outputs'.format(data_type, i, data_type, u, w, i))
        cmd_list.append('copy /Y D:\\PythonProject\\end_point_event_pred\\resource\\Data\\svm_data\\{}\\'
                        '{}trd.weights D:\PythonProject\\end_point_event_pred\\resource\\Data\\svm_data\\'
                        '{}\\u{}w{}\\{}trd.weights'.format(data_type, i, data_type, u, w, i))
    cmd_list.append('cd ..')
    return cmd_list


def write_general():
    cmd_list = list()
    # 写数据生成代码
    for i in range(10):
        cmd_list.append('D:')
        cmd_list.append('cd D:\\PythonProject\\end_point_event_pred\\src\\')
        cmd_list.append('python file_generate.py')

        # 执行批处理文件
        cmd_list.append('cd D:\\PythonProject\\end_point_event_pred\\resource\\Data\\')
        cmd_list.append('call 1_year_readmit.cmd')
        cmd_list.append('cd D:\\PythonProject\\end_point_event_pred\\resource\\Data\\')
        cmd_list.append('call 30_day_readmit.cmd')
        cmd_list.append('cd D:\\PythonProject\\end_point_event_pred\\resource\\Data\\')
        cmd_list.append('call all_cause_death.cmd')
        cmd_list.append('cd D:\\PythonProject\\end_point_event_pred\\resource\\Data\\')
        cmd_list.append('call cardio_death.cmd')
        cmd_list.append('cd /')

        # 写统计生成代码
        cmd_list.append('cd D:\\PythonProject\\end_point_event_pred\\src\\')
        cmd_list.append('python performance.py')
        cmd_list.append('cd /')
    return cmd_list


def main():
    cmd_dict = dict()
    data_type_dict = ['1_year_readmit', '30_day_readmit', 'all_cause_death', 'cardio_death']
    ratio = {'1_year_readmit': 0.56, '30_day_readmit': 0.16, 'all_cause_death': 0.11, 'cardio_death': 0.06}

    # 写数据批处理代码
    for data_type in data_type_dict:
        cmd_type_list = list()
        cmd_type_list.append('D:')
        cmd_type_list.append('cd D:\\PythonProject\\end_point_event_pred\\resource\\Data\\svm_data\\')
        # 写svm的批处理代码
        list_ = write_svm(data_type)
        for item in list_:
            cmd_type_list.append(item)
        # 写semi_svm的批处理代码
        for u in [1, 0.001, 0.01, 0.1, 10, 100]:
            for w in [1, 0.001, 0.01, 0.1, 1, 10, 100]:
                list_2 = write_semi_svm(data_type, u, w, ratio[data_type])
                for item in list_2:
                    cmd_type_list.append(item)
        cmd_dict[data_type] = cmd_type_list
    for item in cmd_dict:
        with open('D:\\PythonProject\\end_point_event_pred\\resource\\Data\\{}.cmd'.format(item), 'w') as file:
            for line in cmd_dict[item]:
                file.write(line+'\n')

    cmd = write_general()
    with open('D:\\PythonProject\\end_point_event_pred\\resource\\Data\\general.cmd', 'w') as file:
        for line in cmd:
            file.write(line + '\n')


if __name__ == "__main__":
    main()
