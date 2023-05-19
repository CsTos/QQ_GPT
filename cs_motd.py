from mcstatus import JavaServer
import socket

# 连接服务器并获取MOTD
def cs_cmtd (cs_ip,cs_port):
    try:
        server_address = (cs_ip,cs_port)
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect(server_address)
        sock.send(b"\xfe\x01")
        data = sock.recv(1024)
        motd = ""
    except ConnectionRefusedError:
        return '服务器未响应，可能是因为服务器处于关闭状态'
    for i in range(3, len(data), 2):
        try:
            char = chr(data[i] * 256 + data[i + 1])
            if char.isprintable():
                motd += char
        except:
            pass
    sock.close()
    return motd

def text_ct(c_txt):
    start = c_txt.find('☪ ')
    end = c_txt.find('§r4288') - 5
    result = c_txt[start:end]
    return result
# dt = text_ct(cs_cmtd('xfk.mcone.cc',30000))
# print(dt)
def cs_motd(ct_ip):
    try:
        server = JavaServer.lookup(ct_ip)
        status = server.status()
    except ConnectionRefusedError:
        return '服务器未响应，可能是因为服务器处于关闭状态'
    return f"当前有 {status.players.online} 名玩家, 服务器延迟: {status.latency} ms"

def cs_xk(o_ip,o_port):
    dt_ip = o_ip + ':' + str(o_port)
    #print(dt_ip)
    dt_a = text_ct(cs_cmtd(o_ip,o_port))
    dt_b = cs_motd(dt_ip)
    return dt_a + '--\n' + dt_b
#print(cs_xk('xfk.mcone.cc',30000))
#print(cs_xk('mc2b2t.com',25565))
print(cs_motd('mc2b2t.com'))