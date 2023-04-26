import json
import re
from cs_listbk import csbk_list #模块作用 查询 或写入 黑名单

def cs_set_cfg(set_cfg,cs_data):
    # 判断配置文件是否存在，如果不存在则创建新的配置文件
    # 配置文件路径
    config_file_path = "cs_ls.json"
    cs_etc = csbk_list('10000','查询')
    cs_i = set_cfg
    if set_cfg == 'qzls':
        set_cfg = 'qz'
    if set_cfg == 'qzset':
        set_cfg = 'qz'
    if cs_etc == 0:
        print('OK')
    try:
        with open(config_file_path, "r") as f:
            json.load(f)
    except FileNotFoundError:
        with open(config_file_path, "w") as f:
            json.dump({"cs_cfg": {set_cfg: 'true'}}, f)
    # 读取配置文件
    with open(config_file_path, "r") as f:
        config = json.load(f)
    # print('N:',config)
    # 如果配置文件中还没有 "cs_cfg" 这个元素，则新增此元素
    if "cs_cfg" not in config:
        config["cs_cfg"] = {set_cfg: 'false'}
    if set_cfg not in config['cs_cfg']:
        config["cs_cfg"][set_cfg] = 'false'
    if cs_data == '查询':
        return config['cs_cfg'][set_cfg]
    if cs_data == '关闭':
        config["cs_cfg"][set_cfg] = 'false'
        cs_cfg_ok(config_file_path,config)
        return 'ok'
    if cs_data == '开启':
        config["cs_cfg"][set_cfg] = 'true'
        cs_cfg_ok(config_file_path,config)
        return 'ok'
    if cs_i == 'qzls':
        if set_cfg != 'qz':
            config["cs_cfg"] = {'qz': '//1//'}
            return config["cs_cfg"]['qz']
        return config['cs_cfg']['qz'].strip()
    if cs_i == 'qzset':
        cs_data = cs_data.strip()
        config["cs_cfg"]['qz'] = cs_data
        cs_cfg_ok(config_file_path,config)
        return 'ok'
    return 'no'

def cs_cfg_ok(cs_file,cs_data):
    with open(cs_file, "w") as f:
        json.dump(cs_data, f)
        return 'ok'

# print(cs_set_cfg('at','开启'))
#print(cs_set_cfg('qzls','qz'))
