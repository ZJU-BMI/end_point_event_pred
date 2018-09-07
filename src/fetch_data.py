# encoding=utf-8
import datetime
import os
import csv
import re
import math
import connection


def get_latest_visit_id(path, patient_id_list=None):
    """
    定义患者最后一次入院的数据为所需数据，返回数据库所有患者最后一次入院的Visit_ID

    如果patient_id_list不为空，则在查询到的Visit_ID中进行筛选，只返回在patient_id_list中的病人的最后一次入院ID
    :return:
    """
    conn = connection.get_connection()
    visit_dict = dict()
    with conn.cursor() as cursor:
        sql = "select patient_id, max(visit_id) from pat_visit group by patient_id"
        for row in cursor.execute(sql):
            visit_dict[row[0]] = row[1]

    # further selection
    if patient_id_list is None:
        pass
    else:
        selected_dict = dict()
        for item in patient_id_list:
            if visit_dict.__contains__(item):
                selected_dict[item] = str(visit_dict[item])
            else:
                print(item + ' is not in the database')
        visit_dict = selected_dict

    # 写入文档
    with open(path, 'w', encoding='utf-8-sig', newline="") as file:
        matrix_to_write = []
        csv_writer = csv.writer(file)
        head = ['pat_id', 'visit_id']
        matrix_to_write.append(head)
        for patient_id in visit_dict:
            line = list()
            line.append(patient_id)
            line.append(visit_dict[patient_id])
            matrix_to_write.append(line)
        csv_writer.writerows(matrix_to_write)
    return visit_dict


def get_sex(visit_dict, path):
    """
    获取目标病人的性别
    :param visit_dict:
    :param path:
    :return:
    """
    conn = connection.get_connection()
    sex_dict = dict()
    with conn.cursor() as cursor:
        sql = "select patient_id, sex from pat_master_index"
        for row in cursor.execute(sql):
            if row[1] == '男':
                sex_dict[row[0]] = 1
            else:
                sex_dict[row[0]] = 0

    selected_dict = dict()
    for patient_id in visit_dict:
        if sex_dict.__contains__(patient_id):
            selected_dict[patient_id] = sex_dict[patient_id]
        else:
            selected_dict[patient_id] = -1
            print(patient_id + '\'s sex is not in the database')
    sex_dict = selected_dict

    # 写入文档
    with open(path, 'w', encoding='utf-8-sig', newline="") as file:
        matrix_to_write = []
        csv_writer = csv.writer(file)
        head = ['pat_id', '性别']
        matrix_to_write.append(head)
        for patient_id in visit_dict:
            line = list()
            line.append(patient_id)
            line.append(sex_dict[patient_id])
            matrix_to_write.append(line)
        csv_writer.writerows(matrix_to_write)
    return sex_dict


def get_age(visit_dict, path):
    """
    获取病人最后一次入院的年龄
    :param visit_dict:
    :param path:
    :return:
    """
    conn = connection.get_connection()
    birthday_dict = dict()
    visit_date_dict = dict()
    age_dict = dict()
    # 获取病人的出生年月
    with conn.cursor() as cursor:
        sql = 'select patient_id, date_of_birth from pat_master_index'
        for row in cursor.execute(sql):
            birthday = row[1]

            if birthday is None:
                continue
            elif len(birthday) > 12:
                birthday = datetime.datetime.strptime(birthday, '%Y/%m/%d %H:%M:%S')
            else:
                birthday = datetime.datetime.strptime(birthday, '%Y/%m/%d')

            birthday_dict[row[0]] = birthday

    # 获取病人的入院时间
    with conn.cursor() as cursor:
        sql = 'select patient_id, visit_id, admission_date_time from pat_visit'
        for row in cursor.execute(sql):
            admit_date_time = row[2]
            if admit_date_time is None:
                continue
            elif len(admit_date_time) > 12:
                admit_date_time = datetime.datetime.strptime(admit_date_time, '%Y/%m/%d %H:%M:%S')
            else:
                admit_date_time = datetime.datetime.strptime(admit_date_time, '%Y/%m/%d')

            if visit_dict.__contains__(row[0]) and str(visit_dict[row[0]]) == str(row[1]):
                visit_date_dict[row[0]] = admit_date_time

    for key in visit_dict:
        if (not birthday_dict.__contains__(key)) or (not visit_date_dict.__contains__(key)):
            age_dict[key] = -1
            print(key + '\'s age is not in the database')
            continue
        birthday = birthday_dict[key]
        admit = visit_date_dict[key]
        age = (admit - birthday).days/365
        age_dict[key] = age

    # 写入文档
    with open(path, 'w', encoding='utf-8-sig', newline="") as file:
        matrix_to_write = []
        csv_writer = csv.writer(file)
        head = ['pat_id', '年龄']
        matrix_to_write.append(head)
        for patient_id in visit_dict:
            line = list()
            line.append(patient_id)
            line.append(age_dict[patient_id])
            matrix_to_write.append(line)
        csv_writer.writerows(matrix_to_write)
    return age_dict


def get_vital_sign(visit_dict, path):
    """
    获取身高，体重，BMI（依据身高体重计算），收缩压，舒张压，心率这几个指标
    所有指标依据Vital_Sign表中的第一个指标进行计算
    :param visit_dict:
    :param path:
    :return:
    """
    conn = connection.get_connection()
    sbp_dict = dict()
    dbp_dict = dict()
    hr_dict = dict()
    height_dict = dict()
    weight_dict = dict()
    bmi_dict = dict()
    area_dict = dict()
    for patient_id in visit_dict:
        sbp_dict[patient_id] = [-1, datetime.datetime(2020, 1, 1)]
        dbp_dict[patient_id] = [-1, datetime.datetime(2020, 1, 1)]
        hr_dict[patient_id] = [-1, datetime.datetime(2020, 1, 1)]
        height_dict[patient_id] = [-1, datetime.datetime(2020, 1, 1)]
        weight_dict[patient_id] = [-1, datetime.datetime(2020, 1, 1)]
        bmi_dict[patient_id] = [-1, datetime.datetime(2020, 1, 1)]
        area_dict[patient_id] = [-1, datetime.datetime(2020, 1, 1)]

    with conn.cursor() as cursor:
        sql = 'select patient_id, visit_id, recording_date, vital_signs, vital_signs_values from vital_signs_rec'

        for row in cursor.execute(sql):
            patient_id, visit_id, record_date, sign_type, value = row

            if record_date is None:
                continue
            elif len(record_date) > 12:
                record_date = datetime.datetime.strptime(record_date, '%Y/%m/%d %H:%M:%S')
            else:
                record_date = datetime.datetime.strptime(record_date, '%Y/%m/%d')

            if visit_dict.__contains__(patient_id) and str(visit_dict[patient_id]) == str(visit_id):
                if sign_type == '血压Low':
                    _, previous_date = dbp_dict[patient_id]
                    if previous_date > record_date:
                        dbp_dict[patient_id] = value, record_date
                if sign_type == '血压high':
                    _, previous_date = sbp_dict[patient_id]
                    if previous_date > record_date:
                        sbp_dict[patient_id] = value, record_date
                if sign_type == '身高':
                    _, previous_date = height_dict[patient_id]
                    if previous_date > record_date:
                        height_dict[patient_id] = value, record_date
                if sign_type == '体重':
                    _, previous_date = weight_dict[patient_id]
                    if previous_date > record_date:
                        weight_dict[patient_id] = value, record_date
                if sign_type == '脉搏':
                    _, previous_date = hr_dict[patient_id]
                    if previous_date > record_date:
                        hr_dict[patient_id] = value, record_date
    # 计算体表面积和BMI
    for patient_id in visit_dict:
        if height_dict[patient_id][0] != -1 and weight_dict[patient_id][0] != -1:
            height = float(height_dict[patient_id][0])
            weight = float(weight_dict[patient_id][0])
            time = weight_dict[patient_id][1]
            area = 0.0061*height+0.0128*weight-0.1529
            bmi = weight/(height*height)*10000
            area_dict[patient_id] = [area, time]
            bmi_dict[patient_id] = [bmi, time]

    # 删除时间信息
    for patient_id in visit_dict:
        sbp_dict[patient_id] = sbp_dict[patient_id][0]
        dbp_dict[patient_id] = dbp_dict[patient_id][0]
        hr_dict[patient_id] = hr_dict[patient_id][0]
        height_dict[patient_id] = height_dict[patient_id][0]
        weight_dict[patient_id] = weight_dict[patient_id][0]
        bmi_dict[patient_id] = bmi_dict[patient_id][0]
        area_dict[patient_id] = area_dict[patient_id][0]

    # 写入文档
    with open(path, 'w', encoding='utf-8-sig', newline="") as file:
        matrix_to_write = []
        csv_writer = csv.writer(file)
        head = ['pat_id', '血压Low', '血压high', '身高', '体重', '脉搏', 'BMI', '体表面积']
        matrix_to_write.append(head)
        for patient_id in visit_dict:
            line = list()
            line.append(patient_id)
            line.append(sbp_dict[patient_id])
            line.append(dbp_dict[patient_id])
            line.append(hr_dict[patient_id])
            line.append(height_dict[patient_id])
            line.append(weight_dict[patient_id])
            line.append(bmi_dict[patient_id])
            line.append(area_dict[patient_id])
            matrix_to_write.append(line)
        csv_writer.writerows(matrix_to_write)
    return sbp_dict, dbp_dict, hr_dict, height_dict, weight_dict, bmi_dict, area_dict


def get_pharmacy(visit_dict, mapping_file, write_path):
    # 以在医院中Order表中用药为准
    # 载入药物映射
    conn = connection.get_connection()
    pharmacy_name_map = dict()
    with open(mapping_file, 'r', encoding='gbk', newline='') as file:
        csv_reader = csv.reader(file)
        for line in csv_reader:
            for i in range(1, len(line)):
                if len(line[i]) <= 1:
                    continue
                pharmacy_name_map[line[i]] = line[0]

    # 初始化名单
    pharmacy_dict = dict()
    for patient_id in visit_dict:
        pharmacy_dict[patient_id] = {'beta_blocker': 'False', 'ACEI': 'False', 'ARB': 'False',
                                     'Anticoagulant': 'False', 'Antiplatelet': 'False', 'Statin': 'False',
                                     'CCB': 'False', 'Digoxin': 'False', 'Non_Aldosterone_Diuretic': 'False',
                                     'Aldosterone_Diuretic': 'False', 'Nitrate': 'False'}
    with conn.cursor() as cursor:
        sql = "select patient_id, visit_id, order_text from orders where order_class = 'A'"
        for row in cursor.execute(sql):
            patient_id, visit_id, order_text = row
            if visit_dict.__contains__(patient_id) and str(visit_dict[patient_id]) == str(visit_id):
                for item in pharmacy_name_map:
                    if order_text is not None and order_text.__contains__(item):
                        normalized_name = pharmacy_name_map[item]
                        if normalized_name == 'beta-blocker':
                            pharmacy_dict[patient_id]['beta_blocker'] = 'True'
                        elif normalized_name == '非醛固酮利尿剂':
                            pharmacy_dict[patient_id]['Non_Aldosterone_Diuretic'] = 'True'
                        elif normalized_name == '醛固酮利尿剂':
                            pharmacy_dict[patient_id]['Aldosterone_Diuretic'] = 'True'
                        elif normalized_name == 'ARB':
                            pharmacy_dict[patient_id]['ARB'] = 'True'
                        elif normalized_name == 'ACEI':
                            pharmacy_dict[patient_id]['ACEI'] = 'True'
                        elif normalized_name == '抗凝药物':
                            pharmacy_dict[patient_id]['Anticoagulant'] = 'True'
                        elif normalized_name == '他汀':
                            pharmacy_dict[patient_id]['Statin'] = 'True'
                        elif normalized_name == '钙通道阻滞剂':
                            pharmacy_dict[patient_id]['CCB'] = 'True'
                        elif normalized_name == '抗血小板':
                            pharmacy_dict[patient_id]['Antiplatelet'] = 'True'
                        elif normalized_name == '地高辛':
                            pharmacy_dict[patient_id]['Digoxin'] = 'True'
                        elif normalized_name == '硝酸盐':
                            pharmacy_dict[patient_id]['Nitrate'] = 'True'
                        else:
                            raise ValueError('')
    with open(write_path, 'w', encoding='utf-8-sig', newline="") as file:
        matrix_to_write = []
        csv_writer = csv.writer(file)
        head = ['pat_id']
        # write head
        for patient_id in pharmacy_dict:
            for item in pharmacy_dict[patient_id]:
                head.append(item)
            break
        matrix_to_write.append(head)
        for patient_id in pharmacy_dict:
            line = [patient_id]
            for item in pharmacy_dict[patient_id]:
                line.append(pharmacy_dict[patient_id][item])
            matrix_to_write.append(line)
        csv_writer.writerows(matrix_to_write)
    return pharmacy_dict


def get_labtest(visit_dict, path):
    # 建立模板
    conn = connection.get_connection()
    labtest_dict = dict()
    for patient_id in visit_dict:
        labtest_result = dict()
        labtest_result['脑利钠肽前体'] = [-1, -1, datetime.datetime(2020, 1, 1)]
        labtest_result['丙氨酸氨基转移酶'] = [-1, -1, datetime.datetime(2020, 1, 1)]
        labtest_result['天冬氨酸氨基转移酶'] = [-1, -1, datetime.datetime(2020, 1, 1)]
        labtest_result['总蛋白'] = [-1, -1, datetime.datetime(2020, 1, 1)]
        labtest_result['血清白蛋白'] = [-1, -1, datetime.datetime(2020, 1, 1)]
        labtest_result['总胆红素'] = [-1, -1, datetime.datetime(2020, 1, 1)]
        labtest_result['直接胆红素'] = [-1, -1, datetime.datetime(2020, 1, 1)]
        labtest_result['葡萄糖'] = [-1, -1, datetime.datetime(2020, 1, 1)]
        labtest_result['尿素'] = [-1, -1, datetime.datetime(2020, 1, 1)]
        labtest_result['肌酐'] = [-1, -1, datetime.datetime(2020, 1, 1)]

        labtest_result['尿酸'] = [-1, -1, datetime.datetime(2020, 1, 1)]
        labtest_result['钠'] = [-1, -1, datetime.datetime(2020, 1, 1)]
        labtest_result['钙'] = [-1, -1, datetime.datetime(2020, 1, 1)]
        labtest_result['磷'] = [-1, -1, datetime.datetime(2020, 1, 1)]
        labtest_result['镁'] = [-1, -1, datetime.datetime(2020, 1, 1)]
        labtest_result['钾'] = [-1, -1, datetime.datetime(2020, 1, 1)]
        labtest_result['肌钙蛋白T'] = [-1, -1, datetime.datetime(2020, 1, 1)]
        labtest_result['碱性磷酸酶'] = [-1, -1, datetime.datetime(2020, 1, 1)]
        labtest_result['γ-谷氨酰基转移酶'] = [-1, -1, datetime.datetime(2020, 1, 1)]
        # 除了肌酸激酶，其余单位均统一
        labtest_result['肌酸激酶'] = [-1, -1, datetime.datetime(2020, 1, 1)]

        labtest_result['乳酸脱氢酶'] = [-1, -1, datetime.datetime(2020, 1, 1)]
        labtest_result['肌酸激酶同工酶'] = [-1, -1, datetime.datetime(2020, 1, 1)]
        labtest_result['总胆固醇'] = [-1, -1, datetime.datetime(2020, 1, 1)]
        labtest_result['甘油三酯'] = [-1, -1, datetime.datetime(2020, 1, 1)]
        labtest_result['高密度脂蛋白胆固醇'] = [-1, -1, datetime.datetime(2020, 1, 1)]
        labtest_result['低密度脂蛋白胆固醇'] = [-1, -1, datetime.datetime(2020, 1, 1)]
        labtest_result['载脂蛋白A1'] = [-1, -1, datetime.datetime(2020, 1, 1)]
        labtest_result['载脂蛋白B'] = [-1, -1, datetime.datetime(2020, 1, 1)]
        labtest_result['血清胱抑素'] = [-1, -1, datetime.datetime(2020, 1, 1)]
        labtest_result['红细胞计数'] = [-1, -1, datetime.datetime(2020, 1, 1)]

        labtest_result['血红蛋白'] = [-1, -1, datetime.datetime(2020, 1, 1)]
        labtest_result['红细胞比积'] = [-1, -1, datetime.datetime(2020, 1, 1)]
        labtest_result['红细胞体积分布宽度'] = [-1, -1, datetime.datetime(2020, 1, 1)]
        labtest_result['白细胞计数'] = [-1, -1, datetime.datetime(2020, 1, 1)]
        labtest_result['中性粒细胞'] = [-1, -1, datetime.datetime(2020, 1, 1)]
        labtest_result['淋巴细胞'] = [-1, -1, datetime.datetime(2020, 1, 1)]
        labtest_result['单核细胞'] = [-1, -1, datetime.datetime(2020, 1, 1)]
        labtest_result['嗜酸性粒细胞'] = [-1, -1, datetime.datetime(2020, 1, 1)]
        labtest_result['嗜碱性粒细胞'] = [-1, -1, datetime.datetime(2020, 1, 1)]
        labtest_result['血小板计数'] = [-1, -1, datetime.datetime(2020, 1, 1)]

        labtest_result['平均血小板体积'] = [-1, -1, datetime.datetime(2020, 1, 1)]
        labtest_result['C-反应蛋白'] = [-1, -1, datetime.datetime(2020, 1, 1)]
        labtest_result['凝血酶时间'] = [-1, -1, datetime.datetime(2020, 1, 1)]
        labtest_result['血浆活化部分凝血酶原时间'] = [-1, -1, datetime.datetime(2020, 1, 1)]
        labtest_result['血浆凝血酶原时间'] = [-1, -1, datetime.datetime(2020, 1, 1)]
        labtest_result['血浆凝血酶原活动度'] = [-1, -1, datetime.datetime(2020, 1, 1)]
        labtest_result['国际标准化比值'] = [-1, -1, datetime.datetime(2020, 1, 1)]
        labtest_result['血浆纤维蛋白原'] = [-1, -1, datetime.datetime(2020, 1, 1)]
        labtest_result['血浆-D-二聚体'] = [-1, -1, datetime.datetime(2020, 1, 1)]
        labtest_result['血清甲状腺素'] = [-1, -1, datetime.datetime(2020, 1, 1)]

        labtest_result['三碘甲腺原氨酸'] = [-1, -1, datetime.datetime(2020, 1, 1)]
        labtest_result['游离T3'] = [-1, -1, datetime.datetime(2020, 1, 1)]
        labtest_result['游离T4'] = [-1, -1, datetime.datetime(2020, 1, 1)]
        labtest_result['促甲状腺激素'] = [-1, -1, datetime.datetime(2020, 1, 1)]
        labtest_dict[patient_id] = labtest_result

    with conn.cursor() as cursor:
        sql = "select s.PATIENT_ID, s.VISIT_ID, s.TEST_NO, u.ITEM_NO, u.REPORT_ITEM_NAME, u.RESULT_DATE_TIME,  " \
              "u.RESULT, u. UNITS from LAB_TEST_MASTER s, LAB_TEST_RESULT u where s.TEST_NO = u.TEST_NO"
        for row in cursor.execute(sql):
            patient_id, visit_id, _, _, item_name, item_time, result, unit = row
            if item_time is None:
                continue
            elif len(item_time) > 12:
                item_time = datetime.datetime.strptime(item_time, '%Y/%m/%d %H:%M:%S')
            else:
                item_time = datetime.datetime.strptime(item_time, '%Y/%m/%d')

            if visit_dict.__contains__(patient_id) and str(visit_dict[patient_id]) == str(visit_id) and \
                    item_name is not None:
                if item_name == '脑利钠肽前体':
                    if labtest_dict[patient_id]['脑利钠肽前体'][2] > item_time:
                        labtest_dict[patient_id]['脑利钠肽前体'] = [result, unit, item_time]
                elif item_name == '丙氨酸氨基转移酶':
                    if labtest_dict[patient_id]['丙氨酸氨基转移酶'][2] > item_time:
                        labtest_dict[patient_id]['丙氨酸氨基转移酶'] = [result, unit, item_time]
                elif item_name == '天冬氨酸氨基转移酶':
                    if labtest_dict[patient_id]['天冬氨酸氨基转移酶'][2] > item_time:
                        labtest_dict[patient_id]['天冬氨酸氨基转移酶'] = [result, unit, item_time]
                elif item_name == '总蛋白':
                    if labtest_dict[patient_id]['总蛋白'][2] > item_time:
                        labtest_dict[patient_id]['总蛋白'] = [result, unit, item_time]
                elif item_name == '血清白蛋白':
                    if labtest_dict[patient_id]['血清白蛋白'][2] > item_time:
                        labtest_dict[patient_id]['血清白蛋白'] = [result, unit, item_time]
                elif item_name == '总胆红素':
                    if labtest_dict[patient_id]['总胆红素'][2] > item_time:
                        labtest_dict[patient_id]['总胆红素'] = [result, unit, item_time]
                elif item_name == '直接胆红素':
                    if labtest_dict[patient_id]['直接胆红素'][2] > item_time:
                        labtest_dict[patient_id]['直接胆红素'] = [result, unit, item_time]
                elif item_name == '葡萄糖':
                    if labtest_dict[patient_id]['葡萄糖'][2] > item_time:
                        labtest_dict[patient_id]['葡萄糖'] = [result, unit, item_time]
                elif item_name == '尿素':
                    if labtest_dict[patient_id]['尿素'][2] > item_time:
                        labtest_dict[patient_id]['尿素'] = [result, unit, item_time]
                elif item_name == '肌酐':
                    if labtest_dict[patient_id]['肌酐'][2] > item_time:
                        labtest_dict[patient_id]['肌酐'] = [result, unit, item_time]
                elif item_name == '血清尿酸':
                    if labtest_dict[patient_id]['尿酸'][2] > item_time:
                        labtest_dict[patient_id]['尿酸'] = [result, unit, item_time]
                elif item_name == '钠':
                    if labtest_dict[patient_id]['钠'][2] > item_time:
                        labtest_dict[patient_id]['钠'] = [result, unit, item_time]
                # 此处的钙大约指代血清总钙而非游离钙
                elif item_name == '钙':
                    if labtest_dict[patient_id]['钙'][2] > item_time:
                        labtest_dict[patient_id]['钙'] = [result, unit, item_time]
                elif item_name == '无机磷':
                    if labtest_dict[patient_id]['磷'][2] > item_time:
                        labtest_dict[patient_id]['磷'] = [result, unit, item_time]
                elif item_name == '镁':
                    if labtest_dict[patient_id]['镁'][2] > item_time:
                        labtest_dict[patient_id]['镁'] = [result, unit, item_time]
                elif item_name == '钾':
                    if labtest_dict[patient_id]['钾'][2] > item_time:
                        labtest_dict[patient_id]['钾'] = [result, unit, item_time]
                elif item_name == 'γ-谷氨酰基转移酶':
                    if labtest_dict[patient_id]['γ-谷氨酰基转移酶'][2] > item_time:
                        labtest_dict[patient_id]['γ-谷氨酰基转移酶'] = [result, unit, item_time]
                elif item_name == '碱性磷酸酶':
                    if labtest_dict[patient_id]['碱性磷酸酶'][2] > item_time:
                        labtest_dict[patient_id]['碱性磷酸酶'] = [result, unit, item_time]
                elif item_name == '肌酸激酶':
                    if labtest_dict[patient_id]['肌酸激酶'][2] > item_time:
                        labtest_dict[patient_id]['肌酸激酶'] = [result, unit, item_time]
                elif item_name == '肌钙蛋白T':
                    if labtest_dict[patient_id]['肌钙蛋白T'][2] > item_time:
                        labtest_dict[patient_id]['肌钙蛋白T'] = [result, unit, item_time]
                elif item_name == '乳酸脱氢酶':
                    if labtest_dict[patient_id]['乳酸脱氢酶'][2] > item_time:
                        labtest_dict[patient_id]['乳酸脱氢酶'] = [result, unit, item_time]
                # 肌酸激酶同工酶存在两种名称
                # 1. 肌酸激酶同工酶（50000记录） 2.肌酸激酶同工酶定量测定（110000记录）
                # 1 的单位是U/L，2的单位是ng/ml，由于两者难以相互转化计算，因此只取第二种记录
                elif item_name == '肌酸激酶同工酶定量测定':
                    if labtest_dict[patient_id]['肌酸激酶同工酶'][2] > item_time:
                        labtest_dict[patient_id]['肌酸激酶同工酶'] = [result, unit, item_time]
                elif item_name == '总胆固醇':
                    if labtest_dict[patient_id]['总胆固醇'][2] > item_time:
                        labtest_dict[patient_id]['总胆固醇'] = [result, unit, item_time]
                elif item_name == '甘油三酯':
                    if labtest_dict[patient_id]['甘油三酯'][2] > item_time:
                        labtest_dict[patient_id]['甘油三酯'] = [result, unit, item_time]
                elif item_name == '高密度脂蛋白胆固醇':
                    if labtest_dict[patient_id]['高密度脂蛋白胆固醇'][2] > item_time:
                        labtest_dict[patient_id]['高密度脂蛋白胆固醇'] = [result, unit, item_time]
                elif item_name == '低密度脂蛋白胆固醇':
                    if labtest_dict[patient_id]['低密度脂蛋白胆固醇'][2] > item_time:
                        labtest_dict[patient_id]['低密度脂蛋白胆固醇'] = [result, unit, item_time]
                elif item_name == '载脂蛋白A1':
                    if labtest_dict[patient_id]['载脂蛋白A1'][2] > item_time:
                        labtest_dict[patient_id]['载脂蛋白A1'] = [result, unit, item_time]
                elif item_name == '载脂蛋白B':
                    if labtest_dict[patient_id]['载脂蛋白B'][2] > item_time:
                        labtest_dict[patient_id]['载脂蛋白B'] = [result, unit, item_time]
                elif item_name == '红细胞计数':
                    if labtest_dict[patient_id]['红细胞计数'][2] > item_time:
                        labtest_dict[patient_id]['红细胞计数'] = [result, unit, item_time]
                elif item_name == '血清胱抑素(Cystatin C)测定':
                    if labtest_dict[patient_id]['血清胱抑素'][2] > item_time:
                        labtest_dict[patient_id]['血清胱抑素'] = [result, unit, item_time]

                elif item_name == '血小板计数':
                    if labtest_dict[patient_id]['血小板计数'][2] > item_time:
                        labtest_dict[patient_id]['血小板计数'] = [result, unit, item_time]
                elif item_name == '血红蛋白测定':
                    if labtest_dict[patient_id]['血红蛋白'][2] > item_time:
                        labtest_dict[patient_id]['血红蛋白'] = [result, unit, item_time]
                elif item_name == '红细胞比积测定':
                    if labtest_dict[patient_id]['红细胞比积'][2] > item_time:
                        labtest_dict[patient_id]['红细胞比积'] = [result, unit, item_time]
                elif item_name == '红细胞体积分布宽度测定CV':
                    if labtest_dict[patient_id]['红细胞体积分布宽度'][2] > item_time:
                        labtest_dict[patient_id]['红细胞体积分布宽度'] = [result, unit, item_time]
                elif item_name == '白细胞计数':
                    if labtest_dict[patient_id]['白细胞计数'][2] > item_time:
                        labtest_dict[patient_id]['白细胞计数'] = [result, unit, item_time]
                elif item_name == '中性粒细胞':
                    if labtest_dict[patient_id]['中性粒细胞'][2] > item_time:
                        labtest_dict[patient_id]['中性粒细胞'] = [result, unit, item_time]
                elif item_name == '淋巴细胞':
                    if labtest_dict[patient_id]['淋巴细胞'][2] > item_time:
                        labtest_dict[patient_id]['淋巴细胞'] = [result, unit, item_time]
                elif item_name == '单核细胞':
                    if labtest_dict[patient_id]['单核细胞'][2] > item_time:
                        labtest_dict[patient_id]['单核细胞'] = [result, unit, item_time]
                elif item_name == '嗜酸性粒细胞':
                    if labtest_dict[patient_id]['嗜酸性粒细胞'][2] > item_time:
                        labtest_dict[patient_id]['嗜酸性粒细胞'] = [result, unit, item_time]
                elif item_name == '嗜碱性粒细胞':
                    if labtest_dict[patient_id]['嗜碱性粒细胞'][2] > item_time:
                        labtest_dict[patient_id]['嗜碱性粒细胞'] = [result, unit, item_time]

                elif item_name == '平均血小板体积测定':
                    if labtest_dict[patient_id]['平均血小板体积'][2] > item_time:
                        labtest_dict[patient_id]['平均血小板体积'] = [result, unit, item_time]
                elif item_name == 'C-反应蛋白测定':
                    if labtest_dict[patient_id]['C-反应蛋白'][2] > item_time:
                        labtest_dict[patient_id]['C-反应蛋白'] = [result, unit, item_time]
                elif item_name == '凝血酶时间测定':
                    if labtest_dict[patient_id]['凝血酶时间'][2] > item_time:
                        labtest_dict[patient_id]['凝血酶时间'] = [result, unit, item_time]
                elif item_name == '血浆活化部分凝血酶原时间测定':
                    if labtest_dict[patient_id]['血浆活化部分凝血酶原时间'][2] > item_time:
                        labtest_dict[patient_id]['血浆活化部分凝血酶原时间'] = [result, unit, item_time]
                elif item_name == '血浆凝血酶原时间测定':
                    if labtest_dict[patient_id]['血浆凝血酶原时间'][2] > item_time:
                        labtest_dict[patient_id]['血浆凝血酶原时间'] = [result, unit, item_time]
                elif item_name == '血浆凝血酶原活动度测定':
                    if labtest_dict[patient_id]['血浆凝血酶原活动度'][2] > item_time:
                        labtest_dict[patient_id]['血浆凝血酶原活动度'] = [result, unit, item_time]
                elif item_name == '国际标准化比值':
                    if labtest_dict[patient_id]['国际标准化比值'][2] > item_time:
                        labtest_dict[patient_id]['国际标准化比值'] = [result, unit, item_time]
                elif item_name == '血浆纤维蛋白原测定':
                    if labtest_dict[patient_id]['血浆纤维蛋白原'][2] > item_time:
                        labtest_dict[patient_id]['血浆纤维蛋白原'] = [result, unit, item_time]
                elif item_name == '血浆D-二聚体测定':
                    if labtest_dict[patient_id]['血浆-D-二聚体'][2] > item_time:
                        labtest_dict[patient_id]['血浆-D-二聚体'] = [result, unit, item_time]
                elif item_name == '血清甲状腺素测定':
                    if labtest_dict[patient_id]['血清甲状腺素'][2] > item_time:
                        labtest_dict[patient_id]['血清甲状腺素'] = [result, unit, item_time]

                elif item_name == '血清三碘甲腺原氨酸测定':
                    if labtest_dict[patient_id]['三碘甲腺原氨酸'][2] > item_time:
                        labtest_dict[patient_id]['三碘甲腺原氨酸'] = [result, unit, item_time]
                elif item_name == '血清游离T3测定':
                    if labtest_dict[patient_id]['游离T3'][2] > item_time:
                        labtest_dict[patient_id]['游离T3'] = [result, unit, item_time]
                elif item_name == '血清游离T4测定':
                    if labtest_dict[patient_id]['游离T4'][2] > item_time:
                        labtest_dict[patient_id]['游离T4'] = [result, unit, item_time]
                elif item_name == '血清促甲状腺激素测定':
                    if labtest_dict[patient_id]['促甲状腺激素'][2] > item_time:
                        labtest_dict[patient_id]['促甲状腺激素'] = [result, unit, item_time]
    # 数据数值化
    # 采取的策略是直接删除符号，英文，中文字符
    for patient_id in labtest_dict:
        for item in labtest_dict[patient_id]:
            item_value = str(labtest_dict[patient_id][item][0])
            value = re.findall('[-+]?[.]?[\d]+(?:,\d\d\d)*[\.]?\d*(?:[eE][-+]?\d+)?', item_value)
            if len(value) < 1:
                labtest_dict[patient_id][item][0] = -1
            elif value[0] != '-1':
                labtest_dict[patient_id][item][0] = float(value[0])

    # 观察单位是否统一
    unit_dict = dict()
    for patient_id in labtest_dict:
        for item in labtest_dict[patient_id]:
            item_unit = labtest_dict[patient_id][item][1]
            if not unit_dict.__contains__(item):
                unit_dict[item] = set()
            unit_dict[item].add(item_unit)
    for item in unit_dict:
        unit_set = unit_dict[item].__str__()
        print(item + '   ' + unit_set)

    # 去除所有时间信息和单位信息
    for patient_id in labtest_dict:
        for item in labtest_dict[patient_id]:
            item_value, _, _ = labtest_dict[patient_id][item]
            labtest_dict[patient_id][item] = item_value

    with open(path, 'w', encoding='utf-8-sig', newline="") as file:
        matrix_to_write = []
        csv_writer = csv.writer(file)
        head = ['pat_id']
        # write head
        for patient_id in labtest_dict:
            for item in labtest_dict[patient_id]:
                head.append(item)
            break
        matrix_to_write.append(head)
        for patient_id in labtest_dict:
            line = [patient_id]
            for item in labtest_dict[patient_id]:
                line.append(labtest_dict[patient_id][item])
            matrix_to_write.append(line)
        csv_writer.writerows(matrix_to_write)
    return labtest_dict


def get_diagnosis(visit_dict, path):
    # 建立模板
    conn = connection.get_connection()
    diagnosis_dict = dict()
    for patient_id in visit_dict:
        diagnosis_list_dict = dict()
        diagnosis_list_dict['贫血'] = 'False'
        diagnosis_list_dict['高血压'] = 'False'
        diagnosis_list_dict['冠心病'] = 'False'
        diagnosis_list_dict['心肌梗死'] = 'False'
        diagnosis_list_dict['扩张性心肌病'] = 'False'
        diagnosis_list_dict['糖尿病'] = 'False'
        diagnosis_list_dict['高脂血症'] = 'False'
        diagnosis_list_dict['房颤'] = 'False'
        diagnosis_list_dict['脑梗塞'] = 'False'
        diagnosis_list_dict['脑出血'] = 'False'
        diagnosis_list_dict['心力衰竭'] = 'False'
        diagnosis_list_dict['肾功能不全'] = 'False'
        diagnosis_dict[patient_id] = diagnosis_list_dict

    with conn.cursor() as cursor:
        sql = "select patient_id, visit_id, DIAGNOSIS_TYPE, DIAGNOSIS_DESC from DIAGNOSIS"
        for row in cursor.execute(sql):
            patient_id, visit_id, diagnosis_type, diagnosis_desc = row
            # 有关ICD编码的判断可以
            if visit_dict.__contains__(patient_id) and str(visit_dict[patient_id]) == str(visit_id) and \
                    (diagnosis_type == '3' or diagnosis_type == 'A'):
                if diagnosis_desc.__contains__('贫血'):
                    diagnosis_dict[patient_id]['贫血'] = 'True'

                if diagnosis_desc.__contains__('高血压'):
                    diagnosis_dict[patient_id]['高血压'] = 'True'

                if diagnosis_desc.__contains__('冠心病') or diagnosis_desc.__contains__('心绞痛') or \
                        diagnosis_desc.__contains__('心肌梗死') or diagnosis_desc.__contains__('心梗') or \
                        diagnosis_desc.__contains__('粥样硬化'):
                    diagnosis_dict[patient_id]['冠心病'] = 'True'

                if diagnosis_desc.__contains__('心肌梗死') or diagnosis_desc.__contains__('心梗'):
                    diagnosis_dict[patient_id]['心肌梗死'] = 'True'

                if diagnosis_desc.__contains__('扩张性心肌病') or diagnosis_desc.__contains__('扩张型心肌病') or \
                        diagnosis_desc.__contains__('扩心病'):
                    diagnosis_dict[patient_id]['扩张性心肌病'] = 'True'

                if diagnosis_desc.__contains__('糖尿病'):
                    diagnosis_dict[patient_id]['糖尿病'] = 'True'

                if diagnosis_desc.__contains__('高脂血症') or diagnosis_desc.__contains__('高血脂'):
                    diagnosis_dict[patient_id]['高脂血症'] = 'True'

                if diagnosis_desc.__contains__('房颤'):
                    diagnosis_dict[patient_id]['房颤'] = 'True'

                if diagnosis_desc.__contains__('脑梗'):
                    diagnosis_dict[patient_id]['脑梗塞'] = 'True'

                if diagnosis_desc.__contains__('脑出血'):
                    diagnosis_dict[patient_id]['脑出血'] = 'True'

                if diagnosis_desc.__contains__('肾功能'):
                    diagnosis_dict[patient_id]['肾功能不全'] = 'True'

                if diagnosis_desc.__contains__('心力衰竭') or diagnosis_desc.__contains__('心功能'):
                    diagnosis_dict[patient_id]['心力衰竭'] = 'True'

    with open(path, 'w', encoding='utf-8-sig', newline="") as file:
        matrix_to_write = []
        csv_writer = csv.writer(file)
        head = ['pat_id']
        # write head
        for patient_id in diagnosis_dict:
            for item in diagnosis_dict[patient_id]:
                head.append(item)
            break
        matrix_to_write.append(head)
        for patient_id in diagnosis_dict:
            line = list()
            line.append(patient_id)
            for item in diagnosis_dict[patient_id]:
                line.append(diagnosis_dict[patient_id][item])
            matrix_to_write.append(line)
        csv_writer.writerows(matrix_to_write)
    return diagnosis_dict


def get_exam_item(visit_dict, area_dict, path):
    conn = connection.get_connection()
    exam_dict = dict()
    for patient_id in visit_dict:
        pat_exam_dict = dict()
        pat_exam_dict['射血分数'] = -1
        pat_exam_dict['缩短分数'] = -1
        pat_exam_dict['左房内径'] = -1
        pat_exam_dict['主动脉瓣环径'] = -1
        pat_exam_dict['窦内径'] = -1
        pat_exam_dict['窦上径'] = -1
        pat_exam_dict['升主动脉'] = -1
        pat_exam_dict['左室舒张末内径'] = -1
        pat_exam_dict['左室收缩末内径'] = -1
        pat_exam_dict['室间隔厚度'] = -1
        pat_exam_dict['左室后壁厚度'] = -1
        pat_exam_dict['左室收缩末容量'] = -1
        pat_exam_dict['左室舒张末容量'] = -1
        pat_exam_dict['左室舒张末容量指数'] = -1
        pat_exam_dict['左室质量指数'] = -1
        exam_dict[patient_id] = pat_exam_dict

    with conn.cursor() as cursor:
        sql = "select u.patient_id, u.visit_id, s.exam_no, u.req_date_time, exam_para, description, impression, " + \
              "recommendation, is_abnormal from exam_items s, exam_report t, exam_master u where " \
              "s.exam_no = t.exam_no and u.exam_no = s.exam_no and exam_item like '%超声心动图%' and " \
              "exam_para is not null and visit_id is not null and length(exam_para) > 30"

        def read_value(candidate_str):
            value_list = re.findall('[-+]?[.]?[\d]+(?:,\d\d\d)*[\.]?\d*(?:[eE][-+]?\d+)?', candidate_str)
            if len(value_list) == 0:
                return -1
            value = value_list[0]
            return value

        # 识别策略，对目标子字符串的后10个字符（不足则取到底）进行截取，使用正则表达式进行数字识别，
        # 然后截取第一个数字作为值
        for row in cursor.execute(sql):
            patient_id, visit_id, _, req_time, exam_para, _, _, _, _ = row
            if visit_dict.__contains__(patient_id) and str(visit_dict[patient_id]) == str(visit_id):
                if exam_para.__contains__("室间隔"):
                    pos = exam_para.find("室间隔")
                    target_length = len("室间隔")
                    exam_dict[patient_id]['室间隔厚度'] = read_value(exam_para[pos+target_length: pos+target_length+5])
                if exam_para.__contains__("左室后壁"):
                    pos = exam_para.find("左室后壁")
                    target_length = len("左室后壁")
                    exam_dict[patient_id]['左室后壁厚度'] = read_value(exam_para[pos+target_length: pos+target_length+5])

                if exam_para.__contains__("左心室舒张末内径"):
                    pos = exam_para.find("左心室舒张末内径")
                    target_length = len("左心室舒张末内径")
                    exam_dict[patient_id]['左室舒张末内径'] = read_value(exam_para[pos+target_length: pos+target_length+5])
                elif exam_para.__contains__("左室舒张末内径"):
                    pos = exam_para.find("左室舒张末内径")
                    target_length = len("左室舒张末内径")
                    exam_dict[patient_id]['左室舒张末内径'] = read_value(exam_para[pos+target_length: pos+target_length+5])

                if exam_para.__contains__("左心室收缩末内径"):
                    pos = exam_para.find("左心室收缩末内径")
                    target_length = len("左心室收缩末内径")
                    exam_dict[patient_id]['左室收缩末内径'] = read_value(exam_para[pos+target_length: pos+target_length+5])
                elif exam_para.__contains__("左室收缩末内径"):
                    pos = exam_para.find("左室收缩末内径")
                    target_length = len("左室收缩末内径")
                    exam_dict[patient_id]['左室收缩末内径'] = read_value(exam_para[pos+target_length: pos+target_length+5])

                if exam_para.__contains__("左室舒张末容量"):
                    pos = exam_para.find("左室舒张末容量")
                    target_length = len("左室舒张末容量")
                    exam_dict[patient_id]['左室舒张末容量'] = read_value(exam_para[pos+target_length: pos+target_length+5])
                elif exam_para.__contains__("左心室舒张末容量"):
                    pos = exam_para.find("左心室舒张末容量")
                    target_length = len("左心室舒张末容量")
                    exam_dict[patient_id]['左室舒张末容量'] = read_value(exam_para[pos+target_length: pos+target_length+5])

                if exam_para.__contains__("左室收缩末容量"):
                    pos = exam_para.find("左室收缩末容量")
                    target_length = len("左室收缩末容量")
                    exam_dict[patient_id]['左室收缩末容量'] = read_value(exam_para[pos+target_length: pos+target_length+5])
                elif exam_para.__contains__("左心室收缩末容量"):
                    pos = exam_para.find("左心室收缩末容量")
                    target_length = len("左心室收缩末容量")
                    exam_dict[patient_id]['左室收缩末容量'] = read_value(exam_para[pos+target_length: pos+target_length+5])

                if exam_para.__contains__("射血分数"):
                    pos = exam_para.find("射血分数")
                    target_length = len("射血分数")
                    exam_dict[patient_id]['射血分数'] = read_value(exam_para[pos+target_length: pos+target_length+5])

                if exam_para.__contains__("缩短分数"):
                    pos = exam_para.find("缩短分数")
                    target_length = len("缩短分数")
                    exam_dict[patient_id]['缩短分数'] = read_value(exam_para[pos+target_length: pos+target_length+5])

                if exam_para.__contains__("左房前后径"):
                    pos = exam_para.find("左房前后径")
                    target_length = len("左房前后径")
                    exam_dict[patient_id]['左房内径'] = read_value(exam_para[pos+target_length: pos+target_length+5])
                elif exam_para.__contains__("左心房前后径"):
                    pos = exam_para.find("左心房前后径")
                    target_length = len("左心房前后径")
                    exam_dict[patient_id]['左房内径'] = read_value(exam_para[pos+target_length: pos+target_length+5])

                if exam_para.__contains__("升主动脉"):
                    pos = exam_para.find("升主动脉")
                    target_length = len("升主动脉")
                    exam_dict[patient_id]['升主动脉'] = read_value(exam_para[pos+target_length: pos+target_length+5])
                if exam_para.__contains__("主动脉瓣环径"):
                    pos = exam_para.find("主动脉瓣环径")
                    target_length = len("主动脉瓣环径")
                    exam_dict[patient_id]['主动脉瓣环径'] = read_value(exam_para[pos+target_length: pos+target_length+5])
                if exam_para.__contains__("窦内径"):
                    pos = exam_para.find("窦内径")
                    target_length = len("窦内径")
                    exam_dict[patient_id]['窦内径'] = read_value(exam_para[pos+target_length: pos+target_length+5])
                if exam_para.__contains__("窦上径"):
                    pos = exam_para.find("窦上径")
                    target_length = len("窦上径")
                    exam_dict[patient_id]['窦上径'] = read_value(exam_para[pos+target_length: pos+target_length+5])

    for patient_id in exam_dict:
        pat_exam_dict = exam_dict[patient_id]
        if area_dict[patient_id] != str(-1) and pat_exam_dict['左室舒张末内径'] != str(-1) and \
                pat_exam_dict['室间隔厚度'] != str(-1) and pat_exam_dict['左室后壁厚度'] != str(-1):
            lvdd = float(pat_exam_dict['左室舒张末内径'])
            ivst = float(pat_exam_dict['室间隔厚度'])
            pwt = float(pat_exam_dict['左室后壁厚度'])
            pat_exam_dict['左室质量指数'] = \
                (0.8 * 1.04 * (float(lvdd+ivst+pwt)**3 - float(lvdd)**3) + 0.6)/float(area_dict[patient_id])/1000
        if area_dict[patient_id] != str(-1) and pat_exam_dict['左室舒张末容量'] != -1:
            pat_exam_dict['左室舒张末容量指数'] = float(pat_exam_dict['左室舒张末容量'])/float(area_dict[patient_id])

    with open(path, 'w', encoding='utf-8-sig', newline="") as file:
        matrix_to_write = []
        csv_writer = csv.writer(file)
        head = ['pat_id']
        # write head
        for patient_id in exam_dict:
            for item in exam_dict[patient_id]:
                head.append(item)
            break
        matrix_to_write.append(head)
        for patient_id in exam_dict:
            line = list()
            line.append(patient_id)
            for item in exam_dict[patient_id]:
                line.append(exam_dict[patient_id][item])
            matrix_to_write.append(line)
        csv_writer.writerows(matrix_to_write)
    return exam_dict


def get_hospitalized_day(visit_dict, path):
    conn = connection.get_connection()
    hospitalized_dict = dict()
    for patient_id in visit_dict:
        hospitalized_dict[patient_id] = -1

    with conn.cursor() as cursor:
        sql = "select PATIENT_ID, VISIT_ID, ADMISSION_DATE_TIME, DISCHARGE_DATE_TIME from PAT_VISIT "

        for row in cursor.execute(sql):
            patient_id, visit_id, admit, discharge = row

            if admit is None:
                continue
            elif len(admit) > 12:
                admit = datetime.datetime.strptime(admit, '%Y/%m/%d %H:%M:%S')
            else:
                admit = datetime.datetime.strptime(admit, '%Y/%m/%d')

            if discharge is None:
                continue
            elif len(discharge) > 12:
                discharge = datetime.datetime.strptime(discharge, '%Y/%m/%d %H:%M:%S')
            else:
                discharge = datetime.datetime.strptime(discharge, '%Y/%m/%d')

            if visit_dict.__contains__(patient_id) and str(visit_dict[patient_id]) == str(visit_id):
                hospitalized_dict[patient_id] = (discharge-admit).days

    with open(path, 'w', encoding='utf-8-sig', newline="") as file:
        matrix_to_write = []
        csv_writer = csv.writer(file)
        head = ['pat_id', 'LOS']
        matrix_to_write.append(head)
        for patient_id in hospitalized_dict:
            line = list()
            line.append(patient_id)
            line.append(hospitalized_dict[patient_id])
            matrix_to_write.append(line)
        csv_writer.writerows(matrix_to_write)

    return hospitalized_dict


def read_latest_visit_id(path):
    visit_dict = dict()
    with open(path, 'r', newline="", encoding='utf-8-sig') as file:
        csv_reader = csv.reader(file)
        row_index = 0
        for row in csv_reader:
            if row_index == 0:
                row_index += 1
            else:
                visit_dict[row[0]] = row[1]
    return visit_dict


def read_vital_sign(path):
    sbp_dict = dict()
    dbp_dict = dict()
    hr_dict = dict()
    height_dict = dict()
    weight_dict = dict()
    bmi_dict = dict()
    area_dict = dict()

    with open(path, 'r', newline="", encoding='utf-8-sig') as file:
        csv_reader = csv.reader(file)
        row_index = 0
        for row in csv_reader:
            if row_index == 0:
                row_index += 1
            else:
                sbp_dict[row[0]] = row[1]
                dbp_dict[row[0]] = row[2]
                hr_dict[row[0]] = row[3]
                height_dict[row[0]] = row[4]
                weight_dict[row[0]] = row[5]
                bmi_dict[row[0]] = row[6]
                area_dict[row[0]] = row[7]
    return sbp_dict, dbp_dict, hr_dict, height_dict, weight_dict, bmi_dict, area_dict


def read_exam_item(path):
    exam_dict = dict()
    with open(path, 'r', newline="", encoding='utf-8-sig') as file:
        csv_reader = csv.reader(file)
        head_index = dict()
        row_index = 0
        for row in csv_reader:
            if row_index == 0:
                for i in range(len(row)):
                    head_index[i] = row[i]
                row_index += 1
            else:
                exam_dict[row[0]] = dict()
                for i in range(1, len(row)):
                    exam_dict[row[0]][head_index[i]] = row[i]
    return exam_dict


def read_labtest(path):
    lab_test_dict = dict()
    with open(path, 'r', newline="", encoding='utf-8-sig') as file:
        csv_reader = csv.reader(file)
        head_index = dict()
        row_index = 0
        for row in csv_reader:
            if row_index == 0:
                for i in range(len(row)):
                    head_index[i] = row[i]
                row_index += 1
            else:
                lab_test_dict[row[0]] = dict()
                for i in range(1, len(row)):
                    lab_test_dict[row[0]][head_index[i]] = row[i]
    return lab_test_dict


def read_hospitalized_day(path):
    hospitalized_day_dict = dict()
    with open(path, 'r', newline="", encoding='utf-8-sig') as file:
        csv_reader = csv.reader(file)
        for row in csv_reader:
            hospitalized_day_dict[row[0]] = row[1]
    return hospitalized_day_dict


def read_sex(path):
    sex_dict = dict()
    with open(path, 'r', newline="", encoding='utf-8-sig') as file:
        csv_reader = csv.reader(file)
        for row in csv_reader:
            sex_dict[row[0]] = row[1]
    return sex_dict


def read_age(path):
    age_dict = dict()
    with open(path, 'r', newline="", encoding='utf-8-sig') as file:
        csv_reader = csv.reader(file)
        for row in csv_reader:
            age_dict[row[0]] = row[1]
    return age_dict


def read_pharmacy(path):
    pharmacy_dict = dict()
    with open(path, 'r', newline="", encoding='utf-8-sig') as file:
        csv_reader = csv.reader(file)
        head_index = dict()
        row_index = 0
        for row in csv_reader:
            if row_index == 0:
                for i in range(len(row)):
                    head_index[i] = row[i]
                row_index += 1
            else:
                pharmacy_dict[row[0]] = dict()
                for i in range(1, len(row)):
                    pharmacy_dict[row[0]][head_index[i]] = row[i]
    return pharmacy_dict


def read_diagnosis(path):
    diagnosis_dict = dict()
    with open(path, 'r', newline="", encoding='utf-8-sig') as file:
        csv_reader = csv.reader(file)
        head_index = dict()
        row_index = 0
        for row in csv_reader:
            if row_index == 0:
                for i in range(len(row)):
                    head_index[i] = row[i]
                row_index += 1
            else:
                diagnosis_dict[row[0]] = dict()
                for i in range(1, len(row)):
                    diagnosis_dict[row[0]][head_index[i]] = row[i]
    return diagnosis_dict


def get_feature(path, read_from_file):
    if read_from_file['visit']:
        # 以入院的Visit表中的数据为所有数据起算的基准数据
        visit_dict = read_latest_visit_id(os.path.join(path, 'visit.csv'))
    else:
        visit_dict = get_latest_visit_id(os.path.join(path, 'visit.csv'))
    print('visit_finish')

    if read_from_file['age']:
        age_dict = read_age(os.path.join(path, 'age.csv'))
    else:
        age_dict = get_age(visit_dict, os.path.join(path, 'age.csv'))
    print('age_finish')

    if read_from_file['hospitalized']:
        hospitalized_dict = read_hospitalized_day(os.path.join(path, 'hospitalized.csv'))
    else:
        hospitalized_dict = get_hospitalized_day(visit_dict, os.path.join(path, 'hospitalized.csv'))
    print('hospitalized_finish')

    if read_from_file['sex']:
        sex_dict = read_sex(os.path.join(path, 'sex.csv'))
    else:
        sex_dict = get_sex(visit_dict, os.path.join(path, 'sex.csv'))
    print('sex_finish')

    if read_from_file['diagnosis']:
        diagnosis_dict = read_diagnosis(os.path.join(path, 'diagnosis.csv'))
    else:
        diagnosis_dict = get_diagnosis(visit_dict, os.path.join(path, 'diagnosis.csv'))
    print('diagnosis_finish')

    if read_from_file['vital_sign']:
        sbp_dict, dbp_dict, hr_dict, height_dict, weight_dict, bmi_dict, area_dict = \
            read_vital_sign(os.path.join(path, 'vital_sign.csv'))
    else:
        sbp_dict, dbp_dict, hr_dict, height_dict, weight_dict, bmi_dict, area_dict = \
            get_vital_sign(visit_dict, os.path.join(path, 'vital_sign.csv'))
    print('vital_sign_finish')

    if read_from_file['exam']:
        exam_dict = read_exam_item(os.path.join(path, 'exam.csv'))
    else:
        exam_dict = get_exam_item(visit_dict, area_dict, os.path.join(path, 'exam.csv'))
    print('exam_dict_finish')

    if read_from_file['labtest']:
        labtest_dict = read_labtest(os.path.join(path, 'labtest.csv'))
    else:
        labtest_dict = get_labtest(visit_dict, os.path.join(path, 'labtest.csv'))
    print('labtest_finish')

    if read_from_file['pharmacy']:
        pharmacy_list = read_pharmacy(os.path.join(path, 'pharmacy.csv'))
    else:
        mapping_file = os.path.abspath(os.path.join(path, '药品名称映射.csv'))
        pharmacy_list = get_pharmacy(visit_dict, mapping_file, os.path.join(path, 'pharmacy.csv'))
    print('pharmacy_finish')

    feature_dict = {}
    for patient_id in visit_dict:
        feature_dict[patient_id] = dict()
        feature_dict[patient_id]['住院日'] = hospitalized_dict[patient_id]
        feature_dict[patient_id]['性别'] = sex_dict[patient_id]
        feature_dict[patient_id]['年龄'] = age_dict[patient_id]

        feature_dict[patient_id]['收缩压'] = sbp_dict[patient_id]
        feature_dict[patient_id]['舒张压'] = dbp_dict[patient_id]
        feature_dict[patient_id]['心率'] = hr_dict[patient_id]
        feature_dict[patient_id]['身高'] = height_dict[patient_id]
        feature_dict[patient_id]['体重'] = weight_dict[patient_id]
        feature_dict[patient_id]['BMI'] = bmi_dict[patient_id]
        feature_dict[patient_id]['体表面积'] = area_dict[patient_id]

        for item in pharmacy_list[patient_id]:
            if pharmacy_list[patient_id][item] == 'False':
                feature_dict[patient_id][item] = 0
            else:
                feature_dict[patient_id][item] = 1
        for item in labtest_dict[patient_id]:
            feature_dict[patient_id][item] = labtest_dict[patient_id][item]
        for item in exam_dict[patient_id]:
            feature_dict[patient_id][item] = exam_dict[patient_id][item]
        for item in diagnosis_dict[patient_id]:
            if diagnosis_dict[patient_id][item] == 'True':
                feature_dict[patient_id][item] = 1
            else:
                feature_dict[patient_id][item] = 0
    print('finish')
    return feature_dict


def eliminate_incomplete_data(feature_dict):
    # 定义所有数据项中，丢失数据大于十个的为缺失过多的数据，直接删除
    eliminate_id_set = set()
    for patient_id in feature_dict:
        lost_count = 0
        for item in feature_dict[patient_id]:
            if feature_dict[patient_id][item] == '-1' or feature_dict[patient_id][item] == -1:
                lost_count += 1
        if lost_count > 10:
            eliminate_id_set.add(patient_id)

    for patient_id in eliminate_id_set:
        feature_dict.pop(patient_id)
    return feature_dict


def main():
    path = os.path.abspath('..\\resource\\')
    read_from_file = {'visit': True, 'vital_sign': True, 'exam': True, 'labtest': True, 'hospitalized': True,
                      'sex': True, 'age': True, 'pharmacy': True, 'diagnosis': True}
    feature_dict = get_feature(path, read_from_file)
    feature_dict = eliminate_incomplete_data(feature_dict)
    # write head
    head_list = ['住院号']
    # 此ID号为任意选择，无特殊意义
    for pat_id in feature_dict:
        feature_name = feature_dict[pat_id]
        for item in feature_name:
            head_list.append(item)
        break

    # 全部数据的结果
    feature_list = list()
    feature_list.append(head_list)
    for patient_id in feature_dict:
        single_case = [patient_id]
        for item in feature_dict[patient_id]:
            single_case.append(feature_dict[patient_id][item])
        feature_list.append(single_case)
    with open(os.path.join(path, 'general_stat_no_impute.csv'), 'w', encoding='utf-8-sig', newline="") as file:
        csv_writer = csv.writer(file)
        csv_writer.writerows(feature_list)


if __name__ == '__main__':
    main()
