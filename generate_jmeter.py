import random
import re
import numpy as np


def create_jmx_file(f_workload, time, system):
    if system == 'OpenMRS':
        print('OpenMRS next running workload+configuration')

    if system == 'TeaStore':
        print('TeaStore next running workload+configuration')

    n = str(time)
    file_name0 = "test" + n + ".jmx"
    file_name = "test.jmx"
    file = open(file_name, "r")
    data = file.readlines()
    k = 0
    for i in range(0, len(data) - 1):
        if re.search("ConstantTimer.delay", data[i]):
            element = re.split('(<|>)', data[i])
            # print(str(s[k]))
            element[4] = str(s[k]).replace(".0", "")
            # print(element[4])
            str_element = ""
            for e in element:
                str_element += e
            data[i] = str_element
        if re.search("RandomTimer.range", data[i]):
            element = re.split('(<|>)', data[i])
            rn = random.randint(100, 500)
            element[4] = str(rn).replace(".0", "")
            str_element = ""
            for e in element:
                str_element += e
            data[i] = str_element
            k += 1

    file.close()
    file_write = open(file_name0, "w")
    file_write.writelines(data)
    file_write.close()
    file_write = open(file_name, "w")
    file_write.writelines(data)
    file_write.close()
    return 0
