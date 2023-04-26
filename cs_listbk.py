import os
import json

BLACKLIST_FILE = "cs_bk.json"    # 黑名单文件名

def create_file_if_not_exists():    # 如果黑名单文件不存在则创建该文件
    if not os.path.exists(BLACKLIST_FILE):
        with open(BLACKLIST_FILE, "w") as f:
            f.write(json.dumps({"blacklist": []}))

def read_blacklist():    # 读取黑名单列表
    create_file_if_not_exists()
    with open(BLACKLIST_FILE, "r") as f:
        data = json.load(f)
    return data["blacklist"]

def write_blacklist(blacklist):    # 写入黑名单列表
    with open(BLACKLIST_FILE, "w") as f:
        f.write(json.dumps({"blacklist": blacklist}))

def csbk_list(user_id, action):       # 对用户进行拉黑、查询、移除黑名单的操作
    blacklist = read_blacklist()

    if action == "查询":
        if user_id in blacklist:
            return 1
        else:
            return 0
    elif action == "拉黑":
        if user_id in blacklist:
            return 0
        else:
            blacklist.append(user_id)
            write_blacklist(blacklist)
            return 1
    elif action == "移除":
        if user_id in blacklist:
            blacklist.remove(user_id)
            write_blacklist(blacklist)
            return 1
        else:
            return 0
    else:
        raise ValueError("不支持的操作选项")    # 不支持的操作选项展示错误信息

