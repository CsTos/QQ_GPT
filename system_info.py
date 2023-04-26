import platform
import sys
import psutil
import cpuinfo

def cs_systinfo():
    cs_input = '---系统信息---\n'
    # 获取系统名称
    cs_input = cs_input + '操作系统: ' + str(platform.system()) + '\n'
    # 获取 CPU 信息
    cpu_info = cpuinfo.get_cpu_info()
    cs_input = cs_input + 'CPU信息: ' + cpu_info['brand_raw'] + '\n'
    cs_input = cs_input + 'CPU频率: ' + cpu_info['hz_actual_friendly'] + '\n'
    # 获取 CPU 使用率
    cs_input = cs_input + 'CPU: ' + str(psutil.cpu_percent()) + ' %\n'
    # 获取内存使用率
    cs_input = cs_input + '内存: ' + str(psutil.virtual_memory().percent) + ' %\n'
    # 获取硬盘使用率
    cs_input = cs_input + '硬盘: ' + str(psutil.disk_usage('/').percent) + ' %\n'
    cs_input = cs_input + '---由CsTos提供---'
    return cs_input
if __name__ == '__main__':
    path =cs_systinfo()
    print(path)
