import json
import os
import traceback
import uuid
import random
from copy import deepcopy
from flask import request, Flask
import openai #主机器模块 openai
import requests
import re
import base64 #base64 编码模块
print("\033[38;5;82m开始载入QBot...\033[0m")
print('\033[38;5;198m此为二次改进版\033\n\033[38;5;122m原版地址为:https://lucent.blog/?p=118\033[0m')
Qbot_v = "1.6v"
print ('\033[33m版本号:' + Qbot_v + "\033[0m")
try:
    print('\033[38;5;51m---开始检查配置文件...\033[0m')
    with open("config.json", "r", encoding='utf=8') as jsonfile:
        config_data = json.load(jsonfile)
        qq_no = config_data['qq_bot']['qq_no']
        print('\033[92m----配置文件无异常..\033[0m')
except UnicodeDecodeError:
    print('\033[32mERROR: ---配置文件编码错误！\n---检测到配置文件非utf-8格式,你可能多半是用了记事本修改本地config.json文件才导致此报错出现... \033[0m')
    print('---结束运行...')
    exit()
from text_to_image import text_to_image
from datetime import datetime
from datetime import timedelta
from datetime import timezone
import tiktoken
from text_to_speech import gen_speech
import asyncio
from new_bing import chat_whit_nb, reset_nb_session
from stable_diffusion import get_stable_diffusion_img
from config_file import config_data
from img2prompt import img_to_prompt
from credit_summary import get_credit_summary_by_index
from system_info import cs_systinfo #查询系统信息模块
import subprocess #???
from cs_listbk import csbk_list #模块作用 查询 或写入 黑名单
from cs_cfg import cs_set_cfg #模块作用 查询 或写入 配置

session_config = {
    'msg': [
        {"role": "system", "content": config_data['chatgpt']['preset']}
    ],
    'send_voice': False,
    'new_bing': False
}
cs_image = False #图片功能开关 处于false 状态则只有管理员可以操作
CS_FNSS = '//1//'
if 'true' == cs_set_cfg('at','查询'):
    CS_FNSS = CS_FNSS = "//1//"
else:
    CS_FNSS = cs_set_cfg('qzls','qz')
sessions = {}
current_key_index = 0
cs_LVE = 0 #直播状态码 个人用于直播时的开关

openai.api_base = "https://api.openai.com/v1"

def cs_at(qqat): #从艾特码中取出QQ
    pattern = r"\[CQ:at,qq=(\d+)\]"
    if '' == re.findall(pattern, qqat):
        print('未通过艾特码获取到QQ...')
        return '0'
    else:
        try:
            qqat = qqat.split("=")[1].replace("]", "")
            print('从艾特玛中获取QQ:',qqat)
            return qqat
        except IndexError:
            print('未从艾特玛中找到QQ:',qqat)
    return '0'

def cs_chat(ct_msg,cs_qq): #用于机器的 功能设定/查询信息 例如 菜单等
    ct_msg = str(ct_msg).lower().replace(str("[cq:at,qq=%s]" % qq_no), '')
    ct_msg = ct_msg.strip()
    if '指令说明2' == ct_msg.strip():
        return cs_menu2()
    if ct_msg.strip().startswith('添加权限'):
        if 2248721171 == int(cs_qq): #这里为主人的QQ号 防止其他管理员恶意添加
            ct_msg = ct_msg.strip()
            ct_msg = str(ct_msg).replace('添加权限', '')
            if '' == ct_msg:
                print('未从艾特码中获取到QQ',ct_msg)
            else:
                try:
                    ct_msg = ct_msg.split("=")[1].replace("]", "")
                    print('从艾特码中取出数据',ct_msg)
                except IndexError:
                    print('未找到 QQ 号码')
                    print('从艾特玛中取出数据',ct_msg)
            if '' == ct_msg:
                return '没有获取到成员账号,添加失败 :('
            ct_msg = ct_msg.strip()
            if int(ct_msg) < 10000:
                return '请输入有效的QQ号！'
            if cs_su(ct_msg) == 1:
                return '该成员已存在 请勿重复添加..'
            print('新增管理',ct_msg)
            config_data['qq_bot']['admin_qq'].append(str(ct_msg))
            with open('config.json', 'w', encoding='utf-8') as f:
                json.dump(config_data, f, ensure_ascii=False, indent=4 ,separators=(',', ':'))
            print('管理员列表:',config_data['qq_bot']['admin_qq'])
            return '已添加一名管理员权限。'
        else:
            return '权限并没有添加成功 :('
    if ct_msg.strip().startswith('删除权限'):
        if 2248721171 == int(cs_qq): #这里为主人的QQ号 防止其他管理员恶意添加
            ct_msg = ct_msg.strip()
            ct_msg = str(ct_msg).replace('删除权限', '')
            if '' == ct_msg:
                print ('未从艾特码中获取qq',ct_msg)
            else:
                try:
                    ct_msg = ct_msg.split("=")[1].replace("]", "")
                    print('从艾特码中取出数据',ct_msg)
                except IndexError:
                    print('未找到 QQ 号码')
                    print('从艾特玛中取出数据',ct_msg)
                if '' == ct_msg:
                    return '没有获取到成员账号,删除失败 :('
                ct_msg = ct_msg.strip()
                if int(ct_msg) < 10000:
                    return '请输入有效的QQ号！'
                if cs_su(ct_msg) == 0:
                    return '该成员并不存在 无需删除..'
                config_data['qq_bot']['admin_qq'].remove(str(ct_msg))
                with open('config.json', 'w', encoding='utf-8') as f:
                    json.dump(config_data, f, ensure_ascii=False, indent=4 ,separators=(',', ':'))
                print('管理员列表:',config_data['qq_bot']['admin_qq'])
                return '已删除一名管理员'
        else:
            return '权限并没有删除成功 :('
    if ct_msg.strip().startswith('加黑名单'):
        if cs_su(cs_qq) == 0:
            return '加黑名单并没有成功 :('
        ct_msg = ct_msg.replace('加黑名单', '')
        ct_msg = ct_msg.strip()
        if '' == ct_msg:
            return '请输入要拉黑的QQ'
        ct_at = cs_at(ct_msg)
        if ct_at != '0':
            ct_msg = ct_at
        if int(ct_msg) < 10000: #本来想用 网络查询 QQ号是否有效 还是算了
            return '请输入有效的QQ号'
        if qq_no in ct_msg:
            return '请不要拉黑我！'
        if cs_su(int(ct_msg)) == 1:
            return '不能将管理员拉黑！'
        bk_lh = csbk_list(ct_msg,"拉黑")
        if bk_lh == 0:
            return "加黑名单失败 对方已被拉黑 或 是管理员."
        else:
            return '成功拉黑:' + ct_msg
    if ct_msg.strip().startswith('删黑名单'):
        if cs_su(cs_qq) == 0:
            return '删黑名单并没有成功 :('
        ct_msg = ct_msg.replace('删黑名单', '')
        ct_msg = ct_msg.strip()
        if '' == ct_msg:
            return '请输入要要删除黑名单的QQ'
        ct_at = cs_at(ct_msg)
        if ct_at != '0':
            ct_msg = ct_at
        bk_lh = csbk_list(ct_msg,"移除")
        if bk_lh == 0:
            return '删除失败 对方并不在黑名单 或者您把QQ搞错了'
        else:
            return '已删除黑名单:' + ct_msg
    if ct_msg.strip().startswith('设定前缀'):
        FN_SS = 0
        if cs_su(int(cs_qq)) == 1:
            ct_msg = ct_msg.strip()
            ct_msg = str(ct_msg).replace('设定前缀', '')
            if '' == ct_msg:
                return '未找到你设定的前缀 请重新设定前缀 例如: \n @机器人 设定前缀 chat\n请注意:前缀设定完后不会有空格 请确认你要设定的前缀未包含空格等信息'
            FN_SS = cs_ATF(ct_msg,'TA')
            if FN_SS == 0:
                return '听君一席话，犹如听君一席话。 您现在成功让机器切换为 -艾特回复- 了'                  
            if FN_SS == 404:
                print('未知原因触发逻辑异常  代码定位:CT_002')
                return 'AI: ¿¿¿ 、\n代码定位ID:CT_002'  
            cs_set_cfg('at','关闭')
            ct_msg = ct_msg.strip()
            cs_set_cfg('qzset',ct_msg)
            return '已切换并开启 文本前缀回复 前缀为: ' + ct_msg + '\n前缀回复设定是在群里专用的\n如果要换回艾特请发送 切换艾特'
        else:
            return '前缀并没有设置成功 :('
    if ct_msg.strip().startswith('切换艾特'):
        N_SS = 0
        if cs_su(int(cs_qq)) == 1: 
            FN_SS = cs_ATF('0','AT')
            if FN_SS == 0:
                return '已经是艾特回复 请不要再重复设定'
            if FN_SS == 1:
                FN_SS = cs_set_cfg('at','开启')
                return '已切换艾特回复 请 艾特机器人进行对话 例如: \n @机器人 你好'
            if FN_SS == 404:
                print('未知原因触发逻辑异常  代码定位:CT_003')
                return '理论上这段永远不可能输出 但如果出现在了回复中 多半出了玄学问题... \n代码定位ID:CT_003'
            print('未知原因触发逻辑异常  代码定位:CT_004')
            return '理论上这段永远不可能输出 但如果出现在了回复中 多半出了玄学问题... \n代码定位ID:CT_004'
        else:
            return '艾特回复并没有设置成功 :('
    if '系统信息' == ct_msg.strip():
        return cs_systinfo()
            #cs_result = subprocess.run(["./your_cpp_program", "102"], capture_output=True, text=True)
            #ct_info = cs_result.stdout.strip()
            #return str(ct_info)
    # return "CsTos正在b站直播 我暂时无法提供对话服务..."
    return '0'

def cs_ATF(FNSS,FN_INFO): #用于设置前缀回复
    global CS_FNSS
    if FNSS == '//1//':
        return 0 #表示已存在的设定
    if FN_INFO == 'AT':
        if CS_FNSS == '//1//':
            return 0
        CS_FNSS = '//1//'
        return 1
    if FN_INFO == 'TA': 
        CS_FNSS = FNSS.strip()
        print(CS_FNSS)
        return 1
    return 404 #失败返回 404 以上条件都无法成立 则返回

def cs_su(ct_su): # 读管QQ理员列表
    TEXT_RE = str(ct_su)
    CS_list = config_data['qq_bot']['admin_qq']
    if TEXT_RE in CS_list:
        return 1 #对比成功返回 1
    else:
        return 0 #对比失败返回 0

def cs_menu (): #机器指令菜单
    return "指令如下(群内需@机器人)：\n1.[重置会话] 请发送 重置会话\n2.[设置人格] 请发送 设置人格+人格描述\n3.[AI绘图开关] 请发送 AI绘图开关 (暂时不可用...)\n4.[重置人格] 请发送 重置人格\n5.[指令说明] 请发送 " \
        "指令说明\n6.[指令说明2] 请发送 指令说明2\n注意：\n重置会话不会清空人格,重置人格会重置会话!\n设置人格后人格将一直存在，除非重置人格或重启BOT!"
def cs_menu2():
    return '指令说明如下(群内需@机器人)：\n1.[加黑名单] 请发送 加黑名单 + 对方QQ\n2.[删黑名单] 请发送 删黑名单 + 对方QQ\n3.[设定前缀] 请发送 设定前缀 + 前缀 \n例如: 设定前缀 chat\n4.[切换艾特] 请发送 切换艾特\n5.[系统信息] 请发送 系统信息\n6.[添加权限] 请发送 添加权限 + QQ号或艾特对方\n7.[删除权限] 请发送 删除权限 + QQ号或艾特对方\n3.[复读机] 请发送 复读机 + 复读内容\n....'
def cs_menu3():
    return '指令说明如下(群内需@机器人)：\n' #后续功能列表 于1.7v 版本添加
# 创建一个服务，把当前这个python文件当做一个服务
server = Flask(__name__)

# 测试接口，可以测试本代码是否正常启动
@server.route('/', methods=["GET"])
def index():
    return f"你好，世界!<br/>"
ct_title = "Li4jIyMjIyMuLiMjLi4uLi4jIy4uLi4jIyMuLi4uIyMjIyMjIyMuLi4uLi4uLi4uIyMjIyMjLi4uIyMjIyMjIyMuLiMjIyMjIyMjCi4jIy4uLi4jIy4jIy4uLi4uIyMuLi4jIy4jIy4uLi4uLiMjLi4uLi4uLi4uLi4uIyMuLi4uIyMuLiMjLi4uLi4jIy4uLi4jIy4uLgouIyMuLi4uLi4uIyMuLi4uLiMjLi4jIy4uLiMjLi4uLi4jIy4uLi4uLi4uLi4uLiMjLi4uLi4uLi4jIy4uLi4uIyMuLi4uIyMuLi4KLiMjLi4uLi4uLiMjIyMjIyMjIy4jIy4uLi4uIyMuLi4uIyMuLi4uIyMjIyMjIy4jIy4uLiMjIyMuIyMjIyMjIyMuLi4uLiMjLi4uCi4jIy4uLi4uLi4jIy4uLi4uIyMuIyMjIyMjIyMjLi4uLiMjLi4uLi4uLi4uLi4uIyMuLi4uIyMuLiMjLi4uLi4uLi4uLi4jIy4uLgouIyMuLi4uIyMuIyMuLi4uLiMjLiMjLi4uLi4jIy4uLi4jIy4uLi4uLi4uLi4uLiMjLi4uLiMjLi4jIy4uLi4uLi4uLi4uIyMuLi4KLi4jIyMjIyMuLiMjLi4uLi4jIy4jIy4uLi4uIyMuLi4uIyMuLi4uLi4uLi4uLi4uIyMjIyMjLi4uIyMuLi4uLi4uLi4uLiMjLi4u"
decoded_title = base64.b64decode(ct_title).decode('utf-8')
print('\033[38;5;51m\n' + decoded_title + '\n\033[0m')
print('\033[92m---------欢迎使用Qbot---------\033[0m')
print('\033[38;5;51m---帮助指令 请 @机器人 + 指令说明 例如:\n---@机器人 指令说明\033[0m')
print('\033有问题 请加QQ群:392193454 进行反馈 进群答案:反图灵\033[0m')
print('\033[32m---CsTos 于 2023/04/18 完成改进\033[0m')


# 获取账号余额接口
@server.route('/credit_summary', methods=["GET"])
def credit_summary():
    return get_credit_summary()


# qq消息上报接口，qq机器人监听到的消息内容将被上报到这里
@server.route('/', methods=["POST"])
def get_message():
    global CS_FNSS
    global CS_AET
    if request.get_json().get('message_type') == 'private':  # 如果是私聊信息
        uid = request.get_json().get('sender').get('user_id')  # 获取信息发送者的 QQ号码
        message = request.get_json().get('raw_message')  # 获取原始信息
        sender = request.get_json().get('sender')  # 消息发送者的资料
        print("收到私聊消息：")
        print(message)
        # 下面你可以执行更多逻辑，这里只演示与ChatGPT对话
        if csbk_list(str(uid),'查询') == 1:
            print('检测到黑名单',uid)
            return '0'
        cs_msg_tmp = cs_chat(message,str(uid))
        if '0' != cs_msg_tmp:
            send_private_message(uid, cs_msg_tmp, False)
            return '0'
        if message.strip().startswith('生成图像'):
            print('功能暂时不可用')
            return '0' #不要尝试删掉这段返回 下边的也别删 后边的代码存在问题！ 
        #因为以下代码无法正常把图像地址发到QQ那 我也不知道什么缘故 导致发出去的地址被转义了 没变成图片。
            if cs_image == False:
                if cs_su(uid) == 0:
                    res = requests.post(url=config_data['qq_bot']['cqhttp_url'] + "/send_group_msg",
                        params={'group_id': int(gid), 'message': 'AI画图并没开启 :('}).json()
                    return '0'
            message = str(message).replace('生成图像', '')
            session = get_chat_session('P' + str(uid))
            msg_text = chat(message, session)  # 将消息转发给ChatGPT处理
            # 将ChatGPT的描述转换为图画
            print('开始生成图像')
            pic_path = get_openai_image(msg_text)
            send_private_message_image(uid, pic_path, msg_text)
        elif message.strip().startswith('直接生成图像'):
            print('功能暂时不可用')
            return '0'
            if cs_image == False:
                if cs_su(uid) == 0:
                    res = requests.post(url=config_data['qq_bot']['cqhttp_url'] + "/send_group_msg",
                        params={'group_id': int(gid), 'message': 'AI画图并没开启 :('}).json()
                    return '0'
            message = str(message).replace('直接生成图像', '')
            print('开始直接生成图像')
            pic_path = get_openai_image(message)
            send_private_message_image(uid, pic_path, '')
        elif message.strip().startswith('/sd'):
            print('功能暂时不可用')
            return '0'
            if cs_image == False:
                if cs_su(uid) == 0:
                    res = requests.post(url=config_data['qq_bot']['cqhttp_url'] + "/send_group_msg",
                        params={'group_id': int(gid), 'message': 'AI画图并没开启 :('}).json()
                    return '0'
            print("开始stable-diffusion生成")
            pic_url = ""
            try:
                pic_url = sd_img(message.replace("/sd", "").strip())
            except Exception as e:
                print("stable-diffusion 接口报错: " + str(e))
                send_private_message(uid, "Stable Diffusion 接口报错: " + str(e), False)
            print("stable-diffusion 生成图像: " + pic_url)
            send_private_message_image(uid, pic_url, '')
        elif message.strip().startswith('[CQ:image'):
            print('功能暂时不可用')
            return '0'
            if cs_image == False:
                if cs_su(uid) == 0:
                    res = requests.post(url=config_data['qq_bot']['cqhttp_url'] + "/send_group_msg",
                        params={'group_id': int(gid), 'message': 'AI画图并没开启 :('}).json()
                    return '0'
            print("开始分析图像")
            # 定义正则表达式
            pattern = r'url=([^ ]+)'
            # 使用正则表达式查找匹配的字符串
            match = re.search(pattern, message.strip())
            prompt = img_to_prompt(match.group(1))
            send_private_message(uid, prompt, False)  # 将消息返回的内容发送给用户
        else:
            # 获得对话session
            session = get_chat_session('P' + str(uid))
            if session['new_bing']:
                msg_text = chat_nb(message, session)  # 将消息转发给new bing 处理
            else:
                msg_text = chat(message, session)  # 将消息转发给ChatGPT处理
            send_private_message(uid, msg_text, session['send_voice'])  # 将消息返回的内容发送给用户

    if request.get_json().get('message_type') == 'group':  # 如果是群消息
        gid = request.get_json().get('group_id')  # 群号
        uid = request.get_json().get('sender').get('user_id')  # 发言者的qq号
        message = request.get_json().get('raw_message')  # 获取原始信息
        
        # 判断当被@时才回答
        C_VSP = message
        if str("[cq:at,qq=%s]" % qq_no.lower()) in C_VSP:
            if 2854196310 == request.get_json().get('sender').get('user_id'):
                print ("已屏蔽--")
                return '0'
            C_VSP = str(C_VSP).lower().replace(str("[cq:at,qq=%s]" % qq_no), '')
            if C_VSP.strip().startswith('复读机'):
                print("复读机:")
                if cs_su(uid) == 1:
                    C_VSP = C_VSP.replace('复读机', '')
                    C_VSP = C_VSP.strip()
                    if res["status"] == "ok":
                        print('复读成功')
                        return C_VSP
                    else:
                        print("复读失败：" + str(res['wording']))
                        return "0"
                else:
                    res = requests.post(url=config_data['qq_bot']['cqhttp_url'] + "/send_group_msg",
                    params={'group_id': int(gid), 'message': '复读并没有成功 :('}).json()
                    return "0"
        
        CS_AET = False
        if CS_FNSS == '//1//':
            if str("[cq:at,qq=%s]" % qq_no) in message.lower():
                CS_AET = True
                message = message.lower().replace("[cq:at,qq=%s]" % qq_no, '')
        else:
            if message.strip().startswith(str(CS_FNSS)):
                CS_AET = True
                message = message.replace(str(CS_FNSS), '')
        if CS_AET == True:
            if csbk_list(str(uid),'查询') == 1:
                print('检测到黑名单',uid)
                return '0'
            cs_msg_tmp = ''
            cs_msg_tmp = cs_chat(message,uid)
            if '0' != cs_msg_tmp:
                res = requests.post(url=config_data['qq_bot']['cqhttp_url'] + "/send_group_msg",
                    params={'group_id': int(gid), 'message': cs_msg_tmp}).json()
                return '0'
            #print('原始信息:',message)
            message = message.replace('重置对话', '我是傻子')
            message = message.replace('退出角色扮演', '我是傻子')
            message = message.replace('角色扮演', '何种人物')
            message = message.replace('禁止扮演', '****')
            message = message.replace('扮演', '演戏')
            message = message.replace('退出', '返回')
            message = message.replace('禁止', '禁忌')
            message = message.lower().replace('[cq:at,qq=2960924712]', '')
            message = message.lower().replace('openai','***')
            #message = message.lower().replace('gpt','***')
            message = message.lower().replace('system','***')
            message = message.replace('机器人','傀儡')
            message = message.replace('机器','机傀')
            if CS_FNSS == '//1//':
                message = message.replace(CS_FNSS,'')
            sender = request.get_json().get('sender')  # 消息发送者的资料
            print("收到群聊消息：")
            print(message)
            if message.strip().startswith('生成图像'):
                print('功能暂时不可用')
                return '0'
                if cs_image == False:
                    if cs_su(uid) == 0:
                        res = requests.post(url=config_data['qq_bot']['cqhttp_url'] + "/send_group_msg",
                            params={'group_id': int(gid), 'message': 'AI画图并没开启 :('}).json()
                        return '0'
                message = str(message).replace('生成图像', '')
                session = get_chat_session('G' + str(gid))
                msg_text = chat(message, session)  # 将消息转发给ChatGPT处理
                # 将ChatGPT的描述转换为图画
                print('开始生成图像')
                pic_path = get_openai_image(msg_text)
                send_group_message_image(gid, pic_path, uid, msg_text)
            elif message.strip().startswith('直接生成图像'):
                print('功能暂时不可用')
                return '0'
                if cs_image == False:
                    if cs_su(uid) == 0:
                        res = requests.post(url=config_data['qq_bot']['cqhttp_url'] + "/send_group_msg",
                            params={'group_id': int(gid), 'message': 'AI画图并没开启 :('}).json()
                        return '0'
                message = str(message).replace('直接生成图像', '')
                print('开始直接生成图像')
                pic_path = get_openai_image(message)
                send_group_message_image(gid, pic_path, uid, '')
            elif message.strip().startswith('/sd'):
                print('功能暂时不可用')
                return '0'
                if cs_image == False:
                    if cs_su(uid) == 0:
                        res = requests.post(url=config_data['qq_bot']['cqhttp_url'] + "/send_group_msg",
                            params={'group_id': int(gid), 'message': 'AI画图并没开启 :('}).json()
                        return '0'
                print("开始stable-diffusion生成")
                try:
                    pic_url = sd_img(message.replace("/sd", "").strip())
                except Exception as e:
                    print("stable-diffusion 接口报错: " + str(e))
                    send_group_message(gid, "Stable Diffusion 接口报错: " + str(e), uid, False)
                print("stable-diffusion 生成图像: " + pic_url)
                send_group_message_image(gid, pic_url, uid, '')
            else:
                # 下面你可以执行更多逻辑，这里只演示与ChatGPT对话
                # 获得对话session
                session = get_chat_session('G' + str(uid))
                if session['new_bing']:
                    msg_text = chat_nb(message, session)  # 将消息转发给new bing处理
                else:
                    msg_text = chat(message, session)  # 将消息转发给ChatGPT处理
                send_group_message(gid, msg_text, uid, session['send_voice'])  # 将消息转发到群里

    if request.get_json().get('post_type') == 'request':  # 收到请求消息
        print("收到请求消息")
        request_type = request.get_json().get('request_type')  # group
        uid = request.get_json().get('user_id')
        flag = request.get_json().get('flag')
        comment = request.get_json().get('comment')
        print("配置文件 auto_confirm:" + str(config_data['qq_bot']['auto_confirm']) + " admin_qq: " + str(
            config_data['qq_bot']['admin_qq']))
        if request_type == "friend":
            print("收到加好友申请")
            print("QQ：", uid)
            print("验证信息", comment)
            # 如果配置文件里auto_confirm为 TRUE，则自动通过
            if config_data['qq_bot']['auto_confirm']:
                set_friend_add_request(flag, "true")
            else:
                if cs_su(uid) == 1:  # 否则只有管理员的好友请求会通过
                    print("管理员加好友请求，通过")
                    set_friend_add_request(flag, "true")
        if request_type == "group":
            print("收到群请求")
            sub_type = request.get_json().get('sub_type')  # 两种，一种的加群(当机器人为管理员的情况下)，一种是邀请入群
            gid = request.get_json().get('group_id')
            if sub_type == "add":
                # 如果机器人是管理员，会收到这种请求，请自行处理
                print("收到加群申请，不进行处理")
            elif sub_type == "invite":
                print("收到邀请入群申请")
                print("群号：", gid)
                # 如果配置文件里auto_confirm为 TRUE，则自动通过
                if config_data['qq_bot']['auto_confirm']:
                    set_group_invite_request(flag, "true")
                else:
                    if cs_su(uid) == 1:  # 否则只有管理员的拉群请求会通过
                        set_group_invite_request(flag, "true")
    return "ok"


# 测试接口，可以用来测试与ChatGPT的交互是否正常，用来排查问题
@server.route('/chat', methods=['post'])
def chatapi():
    requestJson = request.get_data()
    if requestJson is None or requestJson == "" or requestJson == {}:
        resu = {'code': 1, 'msg': '请求内容不能为空'}
        return json.dumps(resu, ensure_ascii=False)
    data = json.loads(requestJson)
    if data.get('id') is None or data['id'] == "":
        resu = {'code': 1, 'msg': '会话id不能为空'}
        return json.dumps(resu, ensure_ascii=False)
    print(data)
    try:
        s = get_chat_session(data['id'])
        msg = chat(data['msg'], s)
        if '查询余额' == data['msg'].strip():
            msg = msg.replace('\n', '<br/>')
        resu = {'code': 0, 'data': msg, 'id': data['id']}
        return json.dumps(resu, ensure_ascii=False)
    except Exception as error:
        print("接口报错")
        resu = {'code': 1, 'msg': '请求异常: ' + str(error)}
        return json.dumps(resu, ensure_ascii=False)


# 重置会话接口
@server.route('/reset_chat', methods=['post'])
def reset_chat():
    requestJson = request.get_data()
    if requestJson is None or requestJson == "" or requestJson == {}:
        resu = {'code': 1, 'msg': '请求内容不能为空'}
        return json.dumps(resu, ensure_ascii=False)
    data = json.loads(requestJson)
    if data['id'] is None or data['id'] == "":
        resu = {'code': 1, 'msg': '会话id不能为空'}
        return json.dumps(resu, ensure_ascii=False)
    # 获得对话session
    session = get_chat_session(data['id'])
    # 清除对话内容但保留人设
    del session['msg'][1:len(session['msg'])]
    resu = {'code': 0, 'msg': '重置成功'}
    return json.dumps(resu, ensure_ascii=False)


# 与new bing交互
def chat_nb(msg, session):
    try:
        uid = request.get_json().get('user_id') #获取成员QQ
        if msg.strip() == '':
            return '不知道怎么用 请 @我 加上 指令说明 例如: \n@机器人 指令说明'
        if '语音开启' == msg.strip():
            session['send_voice'] = True
            return '语音回复已开启'
        if '语音关闭' == msg.strip():
            session['send_voice'] = False
            return '语音回复已关闭'
        if '重置会话' == msg.strip():
            reset_nb_session(session['id'])
            return '会话已重置'
        if 'AI绘图开关' == msg.strip():
            if cs_su(uid) == 0 :
                return 'AI绘图并没有被开启· :('
            if cs_image == False:
                cs_image = True
                return 'AI绘图已开启'
            else:
                cs_image = False
                return 'AI绘图已关闭'
        if '指令说明' == msg.strip():
            return cs_menu()
        if "/gpt" == msg.strip():
            session['new_bing'] = False
            return '已切换至ChatGPT'
        print("问: " + msg)
        replay = asyncio.run(chat_whit_nb(session['id'], msg))
        print("New Bing 返回: " + replay)
        return replay
    except Exception as e:
        traceback.print_exc()
        return str('异常: ' + str(e))

# 与ChatGPT交互的方法
def chat(msg, session):
    try:
        pattern = r"\[CQ:at,qq=(\d+)\]"
        uid = request.get_json().get('user_id') #获取成员QQ
        if msg.strip() == '':
            cs_num = random.randint(2,6) # 生成2~5范围内的随机整数
            print(cs_num)
            if cs_num == 1:
                return '你在干啥'
            if cs_num == 2:
                return '你光艾特有个屁用??'
            if cs_num == 3:
                return '你艾特我都不说话有什么用？'
            if cs_num == 4:
                return '嗯 这个艾特就很特别啊,什么也没说'
            if cs_num == 5:
                return '无名人: 6'
            if cs_num == 6:
                return '不知道怎么用 请 @我 加上 指令说明 例如: \n@机器人 指令说明'
            print('未知原因触发逻辑异常 代码定位ID:CT_001') #比如 你多在随机数上 6 改成了7 并且未做判定 返回 就会跳到这里
            return '这段信息理论上不可能发出来 如果发出来多半是随机出问题了。\n代码定位ID:CT_001'
        if msg.strip().startswith('复读机'):
            if cs_su(uid) == 1:
                VSN = msg.strip()
                VSN = VSN.replace('复读机', '')
                return VSN
            else:
                return "复读并没有成功 :("
        if '语音开启' == msg.strip():
            session['send_voice'] = True
            return '语音回复已开启'
        if '语音关闭' == msg.strip():
            session['send_voice'] = False
            return '语音回复已关闭'
        if '重置会话' == msg.strip():
            # 清除对话内容但保留人设
            del session['msg'][1:len(session['msg'])]
            return "会话已重置"
        if '重置人格' == msg.strip():
            # 清空对话内容并恢复预设人设
            session['msg'] = [
                {"role": "system", "content": config_data['chatgpt']['preset']}
            ]
            return '人格已重置'
        if '查询余额' == msg.strip():
            uid = request.get_json().get('user_id')
            if cs_su(uid) == 1:
                text = ""
                for i in range(len(config_data['openai']['api_key'])):
                    text = text + get_credit_summary_by_index(i) + "\n"
                    return text    
            else:
                return "查询并没有成功 :("
        if 'AI绘图开关' == msg.strip():
            return '该功能暂时不可用'
            if cs_su(uid) == 0 :
                return 'AI绘图并没有被开启· :('
            if cs_image == False:
                cs_image = True
                return 'AI绘图已开启'
            else:
                cs_image = False
                return 'AI绘图已关闭'
        if '指令说明' == msg.strip():
            return cs_menu()
        if msg.strip().startswith('/img'):
            print('功能暂时不可用')
            return '功能暂时不可用 :('
            print('开始直接生成图像')
            msg = str(msg).replace('/img', '')
            pic_path = "![](" + get_openai_image(msg) + "]"
            print("地址:",pic_path)
            return pic_path
        if msg.strip().startswith('设置人格'):
            # 清空对话并设置人设
            if cs_su(uid) == 1:
                if '' == msg.strip().replace('设置人格', ''):
                    return '你设置的人格为空,所以设置人格并没有成功 :('
                session['msg'] = [
                {"role": "system", "content": msg.strip().replace('设置人格', '')}
            ]
                return '专属人格设置完成'
            else:
                return '设置并没有成功 :(' 
        if "/newbing" == msg.strip():
            if cs_su(uid) == 1:
                session['new_bing'] = True
                return '已切换至New Bing'
            return 'bing切换并没有成功 :('
        # 设置本次对话内容
        msg = str(msg).lower().replace(str("[cq:at,qq=%s]" % qq_no), '')
        msg = msg.strip()
        session['msg'].append({"role": "user", "content": msg})
        # 设置时间
        session['msg'][1] = {"role": "system", "content": "current time is:" + get_bj_time()}
        # 检查是否超过tokens限制
        while num_tokens_from_messages(session['msg']) > config_data['chatgpt']['max_tokens']:
            # 当超过记忆保存最大量时，重置对话
            message = chat_with_gpt(session['msg'])
            message = message + '\n \n（记忆已达上限）- 请重新对话'
            XZ = message
            del session['msg'][1:len(session['msg'])]
            return XZ
        # 与ChatGPT交互获得对话内容
        if cs_LVE == 1:
            return "CsTos正在b站直播 我暂时无法提供对话服务..."
        message = chat_with_gpt(session['msg'])
        # 记录上下文
        session['msg'].append({"role": "assistant", "content": message})
        message = message.lower().replace('openai','***')
        message = message.lower().replace('gpt','***')
        # message = message.replace('AI','***')
        if 'that model is currently overloaded with other requests.' in message:
            return("模型暂时被限速,等一会再试吧！")
        if 'HTTP code 504 from API' in message:
            return 'API 504 啦,重新和我说一遍吧 ！ '
        if 'Error communicating with OpenAI' in message:
            return '服务器连接失败 可能是主机代理引发的问题 请切换到其他代理节点尝试！\n如果没有代理 请想办法使用代理 再使用AI\n)【注意 如果机器不是你开的 请无视这段信息  因为这问题不在你身上】'
        if 'error communicating with ***' in message:
            return '链接失败 您可能没有本地开启代理 请尝试挂上梯子一类的代理后再重试..'
        message = message.replace('萌萌酱', '萌萌*')
        message = message.replace('SSS_NERS', '安全码')
        message = message.replace('[CQ:at,qq=2220137236]',"萌萌*")
        # message = message.replace('[CQ:at,qq=2220137236]',"-群管家-")
        message = message.replace('角色扮演','轮回')
        message = message.replace('原神','OP给👴爬')
        match = re.search(pattern, message)
        if match:
            at_qq = match.group(1)
            message = message.replace(at_qq, "10000")
        print("ChatGPT返回内容: ")
        print(message)
        return message
    except Exception as error:
        traceback.print_exc()
        return str('异常: ' + str(error))

# 获取北京时间
def get_bj_time():
    utc_now = datetime.utcnow().replace(tzinfo=timezone.utc)
    SHA_TZ = timezone(
        timedelta(hours=8),
        name='Asia/Shanghai',
    )
    # 北京时间
    beijing_now = utc_now.astimezone(SHA_TZ)
    fmt = '%Y-%m-%d %H:%M:%S'
    now_fmt = beijing_now.strftime(fmt)
    return now_fmt


# 获取对话session
def get_chat_session(sessionid):
    if sessionid not in sessions:
        config = deepcopy(session_config)
        config['id'] = sessionid
        config['msg'].append({"role": "system", "content": "current time is:" + get_bj_time()})
        sessions[sessionid] = config
    return sessions[sessionid]


def chat_with_gpt(messages):
    global current_key_index
    max_length = len(config_data['openai']['api_key']) - 1
    try:
        if not config_data['openai']['api_key']:
            return "请设置Api Key"
        else:
            if current_key_index > max_length:
                current_key_index = 0
                return "全部Key均已达到速率限制,请等待一分钟后再尝试"
            openai.api_key = config_data['openai']['api_key'][current_key_index]

        resp = openai.ChatCompletion.create(
            model=config_data['chatgpt']['model'],
            messages=messages
        )
        resp = resp['choices'][0]['message']['content']
    except openai.OpenAIError as e:
        if str(e).__contains__("Rate limit reached for default-gpt-3.5-turbo") and current_key_index <= max_length:
            # 切换key
            current_key_index = current_key_index + 1
            print("速率限制，尝试切换key")
            return chat_with_gpt(messages)
        elif str(e).__contains__(
                "Your access was terminated due to violation of our policies") and current_key_index <= max_length:
            print("请及时确认该Key: " + str(openai.api_key) + " 是否正常，若异常，请移除")
            if current_key_index + 1 > max_length:
                return str(e)
            else:
                print("访问被阻止，尝试切换Key")
                # 切换key
                current_key_index = current_key_index + 1
                return chat_with_gpt(messages)
        else:
            print('openai 接口报错: ' + str(e))
            resp = str(e)
    return resp


# 生成图片
def genImg(message):
    img = text_to_image(message)
    filename = str(uuid.uuid1()) + ".png"
    filepath = config_data['qq_bot']['image_path'] + str(os.path.sep) + filename
    img.save(filepath)
    print("图片生成完毕: " + filepath)
    return filename


# 发送私聊消息方法 uid为qq号，message为消息内容
def send_private_message(uid, message, send_voice):
    try:
        if send_voice:  # 如果开启了语音发送
            voice_path = asyncio.run(
                gen_speech(message, config_data['qq_bot']['voice'], config_data['qq_bot']['voice_path']))
            message = "[CQ:record,file=file://" + voice_path + "]"
            message = message.replace('\\',"/")
            # message = os.path.normpath(message)
        if len(message) >= config_data['qq_bot']['max_length'] and not send_voice:  # 如果消息长度超过限制，转成图片发送
            pic_path = genImg(message)
            message = "[CQ:image,file=" + pic_path + "]"
            message = message.replace('\\',"/")
        res = requests.post(url=config_data['qq_bot']['cqhttp_url'] + "/send_private_msg",
                            params={'user_id': int(uid), 'message': message}).json()
        if res["status"] == "ok":
            print("私聊消息发送成功")
        else:
            print(res)
            print("私聊消息发送失败，错误信息：" + str(res['wording']))

    except Exception as error:
        print("私聊消息发送失败")
        print(error)


# 发送私聊消息方法 uid为qq号，pic_path为图片地址
def send_private_message_image(uid, pic_path, msg):
    try:
        message = "[CQ:image,file=" + pic_path + "]"
        if msg != "":
            message = message.replace('\\',"/")
        res = requests.post(url=config_data['qq_bot']['cqhttp_url'] + "/send_private_msg",
                            params={'user_id': int(uid), 'message': message}).json()
        if res["status"] == "ok":
            print("私聊消息发送成功")
        else:
            print(res)
            print("私聊消息发送失败，错误信息：" + str(res['wording']))

    except Exception as error:
        print("私聊消息发送失败")
        print(error)


# 发送群消息方法
def send_group_message(gid, message, uid, send_voice):
    try:
        if send_voice:  # 如果开启了语音发送
            voice_path = asyncio.run(
                gen_speech(message, config_data['qq_bot']['voice'], config_data['qq_bot']['voice_path']))
            message = "[CQ:record,file=file://" + voice_path + "]"
            message = message.replace('\\',"/")
        if len(message) >= config_data['qq_bot']['max_length'] and not send_voice:  # 如果消息长度超过限制，转成图片发送
            pic_path = genImg(message)
            message = "[CQ:image,file=" + pic_path + "]"
            message = message.replace('\\',"/")
        if not send_voice:
            message = str('[CQ:at,qq=%s]\n' % uid) + message  # @发言人
            message = message.replace('\\',"/")
        res = requests.post(url=config_data['qq_bot']['cqhttp_url'] + "/send_group_msg",
                            params={'group_id': int(gid), 'message': message}).json()
        if res["status"] == "ok":
            print("群消息发送成功")
        else:
            print("群消息发送失败，错误信息：" + str(res['wording']))
    except Exception as error:
        print("群消息发送失败")
        print(error)


# 发送群消息图片方法
def send_group_message_image(gid, pic_path, uid, msg):
    try:
        message = "[CQ:image,file=" + pic_path + "]"
        if msg != "":
            message = msg + '\n' + message
        message = str('[CQ:at,qq=%s]\n' % uid).lower() + message  # @发言人
        res = requests.post(url=config_data['qq_bot']['cqhttp_url'] + "/send_group_msg",
                            params={'group_id': int(gid), 'message': message}).json()
        if res["status"] == "ok":
            print("群消息发送成功")
        else:
            print("群消息发送失败，错误信息：" + str(res['wording']))
    except Exception as error:
        print("群消息发送失败")
        print(error)


# 处理好友请求
def set_friend_add_request(flag, approve):
    try:
        requests.post(url=config_data['qq_bot']['cqhttp_url'] + "/set_friend_add_request",
                      params={'flag': flag, 'approve': approve})
        print("处理好友申请成功")
    except:
        print("处理好友申请失败")


# 处理邀请加群请求
def set_group_invite_request(flag, approve):
    try:
        requests.post(url=config_data['qq_bot']['cqhttp_url'] + "/set_group_add_request",
                      params={'flag': flag, 'sub_type': 'invite', 'approve': approve})
        print("处理群申请成功")
    except:
        print("处理群申请失败")


# openai生成图片
def get_openai_image(des):
    openai.api_key = config_data['openai']['api_key'][current_key_index]
    response = openai.Image.create(
        prompt=des,
        n=1,
        size=config_data['openai']['img_size']
    )
    image_url = response['data'][0]['url']
    print('图像已生成')
    print(image_url)
    return image_url


# 查询账户余额
def get_credit_summary():
    return get_credit_summary_by_index(current_key_index)


# 计算消息使用的tokens数量
def num_tokens_from_messages(messages, model="gpt-3.5-turbo"):
    try:
        encoding = tiktoken.encoding_for_model(model)
    except KeyError:
        encoding = tiktoken.get_encoding("cl100k_base")
    if model == "gpt-3.5-turbo":
        num_tokens = 0
        for message in messages:
            num_tokens += 4
            for key, value in message.items():
                num_tokens += len(encoding.encode(value))
                if key == "name":  # 如果name字段存在，role字段会被忽略
                    num_tokens += -1  # role字段是必填项，并且占用1token
        num_tokens += 2
        return num_tokens
    else:
        raise NotImplementedError(f"""当前模型不支持tokens计算: {model}.""")

# sd生成图片,这里只做了正向提示词，其他参数自己加
def sd_img(msg):
    res = get_stable_diffusion_img({
        "prompt": msg,
        "width": 768,
        "height": 512,
        "num_inference_steps": 20,
        "guidance_scale": 7.5,
        "negative_prompt": "",
        "scheduler": "K_EULER_ANCESTRAL",
        "seed": random.randint(1, 9999999)
    }, config_data['replicate']['api_token'])
    return res[0]

if __name__ == '__main__':
    server.run(port=5555, host='0.0.0.0', use_reloader=False)
