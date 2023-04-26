import asyncio
from EdgeGPT import Chatbot, ConversationStyle
from copy import deepcopy
from config_file import config_data


nb_sessions = {}
tmp_session = {
    "id": ""
}


# 和New Bing交互的方法
async def chat_whit_nb(sessionid, msg):
    session = get_nb_session(sessionid)
    bot = session['bot']
    try:
        if "h3relaxedimg" == config_data['new_bing']['conversation_style']:
            obj = await bot.ask(prompt=msg, conversation_style=ConversationStyle.creative)
        elif "galileo" == config_data['new_bing']['conversation_style']:
            obj = await bot.ask(prompt=msg, conversation_style=ConversationStyle.balanced)
        else:
            obj = await bot.ask(prompt=msg, conversation_style=ConversationStyle.precise)
        print("NewBing 接口返回: ")
        print(obj)
        return obj["item"]["messages"][1]["adaptiveCards"][0]["body"][0]["text"]
    except Exception as e:
        print("New Bing接口报错: " + str(e))
        return "New Bing接口报错: " + str(e)


# 重置会话
def reset_nb_session(sessionid):
    session = get_nb_session(sessionid)
    bot = session['bot']
    bot.reset()


# 存储New Bing session
def get_nb_session(sessionid):
    global nb_sessions
    session = nb_sessions.get(sessionid)
    if session is None:
        session = deepcopy(tmp_session)
        session['id'] = sessionid
        session['bot'] = Chatbot(cookiePath=config_data['new_bing']['cookie_path'])
        nb_sessions[sessionid] = session
    return nb_sessions.get(sessionid)


if __name__ == "__main__":
    print(asyncio.run(chat_whit_nb("123", "你好")))

