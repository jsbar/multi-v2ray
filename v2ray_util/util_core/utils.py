#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import re
import sys
import tty
import socket
import termios
import pkg_resources
import urllib.request
from enum import Enum, unique

class ColorStr:
    RED = '\033[31m'       # 红色
    GREEN = '\033[32m'     # 绿色
    YELLOW = '\033[33m'    # 黄色
    BLUE = '\033[34m'      # 蓝色
    FUCHSIA = '\033[35m'   # 紫红色
    CYAN = '\033[36m'      # 青蓝色
    WHITE = '\033[37m'     # 白色
    #: no color
    RESET = '\033[0m'      # 终端默认颜色

    @classmethod
    def red(cls, s):
        return cls.RED + s + cls.RESET

    @classmethod
    def green(cls, s):
        return cls.GREEN + s + cls.RESET

    @classmethod
    def yellow(cls, s):
        return cls.YELLOW + s + cls.RESET

    @classmethod
    def blue(cls, s):
        return cls.BLUE + s + cls.RESET

    @classmethod
    def cyan(cls, s):
        return cls.CYAN + s + cls.RESET

    @classmethod
    def fuchsia(cls, s):
        return cls.FUCHSIA + s + cls.RESET

    @classmethod
    def white(cls, s):
        return cls.WHITE + s + cls.RESET

@unique
class StreamType(Enum):
    TCP = 'tcp'
    TCP_HOST = 'tcp_host'
    SOCKS = 'socks'
    SS = 'ss'
    MTPROTO = 'mtproto'
    H2 = 'h2'
    WS = 'ws'
    QUIC = 'quic'
    KCP = 'kcp'
    KCP_UTP = 'utp'
    KCP_SRTP = 'srtp'
    KCP_DTLS = 'dtls'
    KCP_WECHAT = 'wechat'
    KCP_WG = 'wireguard'

def stream_list():
    return [ 
        StreamType.KCP_WG, 
        StreamType.KCP_DTLS, 
        StreamType.KCP_WECHAT, 
        StreamType.KCP_UTP, 
        StreamType.KCP_SRTP, 
        StreamType.MTPROTO, 
        StreamType.SOCKS,
        StreamType.SS
    ]

def header_type_list():
    return ("none", "srtp", "utp", "wechat-video", "dtls", "wireguard")

def ss_method():
    return ("aes-256-cfb", "aes-128-cfb", "chacha20", 
        "chacha20-ietf", "aes-256-gcm", "aes-128-gcm", "chacha20-poly1305")

def get_ip():
    """
    获取本地ip
    """
    my_ip = ""
    try:
        my_ip = urllib.request.urlopen('http://api.ipify.org').read()
    except Exception:
        my_ip = urllib.request.urlopen('http://icanhazip.com').read()
    return bytes.decode(my_ip).strip()

def port_is_use(port):
    """
    判断端口是否占用
    """
    cmd = "lsof -i:" + str(port)
    result = os.popen(cmd).readlines()
    return result != []

def is_email(email):
    """
    判断是否是邮箱格式
    """
    str = r'^[a-zA-Z0-9_-]+(\.[a-zA-Z0-9_-]+){0,4}@[a-zA-Z0-9_-]+(\.[a-zA-Z0-9_-]+){0,4}$'
    return re.match(str, email)

def is_ipv4(ip):
    try:
        socket.inet_pton(socket.AF_INET, ip)
    except AttributeError:  # no inet_pton here, sorry
        try:
            socket.inet_aton(ip)
        except socket.error:
            return False
        return ip.count('.') == 3
    except socket.error:  # not a valid ip
        return False
    return True
 
def is_ipv6(ip):
    try:
        socket.inet_pton(socket.AF_INET6, ip)
    except socket.error:  # not a valid ip
        return False
    return True
 
def check_ip(ip):
    return is_ipv4(ip) or is_ipv6(ip)

def bytes_2_human_readable(number_of_bytes, precision=1):
    """
    流量bytes转换为kb, mb, gb等单位
    """
    if number_of_bytes < 0:
        raise ValueError("!!! number_of_bytes can't be smaller than 0 !!!")
 
    step_to_greater_unit = 1024.
 
    number_of_bytes = float(number_of_bytes)
    unit = 'bytes'
 
    if (number_of_bytes / step_to_greater_unit) >= 1:
        number_of_bytes /= step_to_greater_unit
        unit = 'KB'
 
    if (number_of_bytes / step_to_greater_unit) >= 1:
        number_of_bytes /= step_to_greater_unit
        unit = 'MB'
 
    if (number_of_bytes / step_to_greater_unit) >= 1:
        number_of_bytes /= step_to_greater_unit
        unit = 'GB'
 
    if (number_of_bytes / step_to_greater_unit) >= 1:
        number_of_bytes /= step_to_greater_unit
        unit = 'TB'
 
    number_of_bytes = round(number_of_bytes, precision)
 
    return str(number_of_bytes) + ' ' + unit

def gen_cert(domain):
    service_name = ["nginx", "httpd", "apache2"]
    start_cmd = "systemctl start {}  >/dev/null 2>&1"
    stop_cmd = "systemctl stop {} >/dev/null 2>&1"

    if not os.path.exists("/root/.acme.sh/acme.sh"):
        os.system("curl https://get.acme.sh | sh")

    get_ssl_cmd = "bash /root/.acme.sh/acme.sh --issue -d " + domain + " --debug --standalone --keylength ec-256"

    if not os.path.exists("/.dockerenv"):
        for name in service_name:
            os.system(stop_cmd.format(name))
    os.system(get_ssl_cmd)
    if not os.path.exists("/.dockerenv"):
        for name in service_name:
            os.system(start_cmd.format(name))

def calcul_iptables_traffic(port, ipv6=False):
    network = "1" if ipv6 else ""
    traffic_result = os.popen("bash {0} {1} {2}".format(pkg_resources.resource_filename("v2ray_util", "global_setting/calcul_traffic.sh"), str(port), network)).readlines()
    if traffic_result:
        traffic_list = traffic_result[0].split()
        upload_traffic = bytes_2_human_readable(int(traffic_list[0]), 2)
        download_traffic = bytes_2_human_readable(int(traffic_list[1]), 2)
        total_traffic = bytes_2_human_readable(int(traffic_list[2]), 2)
        return "{0}:  upload:{1} download:{2} total:{3}".format(ColorStr.green(str(port)), 
                ColorStr.cyan(upload_traffic), ColorStr.cyan(download_traffic), ColorStr.cyan(total_traffic))

def clean_iptables(port):
    from .loader import Loader
    iptable_way = "iptables" if Loader().profile.network == "ipv4" else "ip6tables" 

    clean_cmd = "{} -D {} {}"
    check_cmd = "{} -nvL {} --line-number|grep -w \"{}\"|awk '{print $1}'|sort -r"

    input_result = os.popen(check_cmd.format(iptable_way, "INPUT", str(port))).readlines()
    for line in input_result:
        os.system(clean_cmd.format(iptable_way, "INPUT", str(line)))

    output_result = os.popen(check_cmd.format(iptable_way, "OUTPUT", str(port))).readlines()
    for line in output_result:
        os.system(clean_cmd.format(iptable_way, "OUTPUT", str(line)))

def open_port():
    input_cmd = "{} -I INPUT -p {} --dport {} -j ACCEPT"
    output_cmd = "{} -I OUTPUT -p {} --sport {}"
    check_cmd = "{} -nvL --line-number|grep -w \"{}\""

    from .loader import Loader

    profile = Loader().profile
    iptable_way = "iptables" if profile.network == "ipv4" else "ip6tables" 
    group_list = profile.group_list

    port_set = set([group.port for group in group_list])

    for port in port_set:
        port_str = str(port)
        if len(os.popen(check_cmd.format(iptable_way, port_str)).readlines()) > 0:
            continue
        os.system(input_cmd.format(iptable_way, "tcp", port_str))
        os.system(input_cmd.format(iptable_way, "udp", port_str))
        os.system(output_cmd.format(iptable_way, "tcp", port_str))
        os.system(output_cmd.format(iptable_way, "udp", port_str))

def loop_input_choice_number(input_tip, length):
    """
    循环输入选择的序号,直到符合规定为止
    """
    while True:
        print("")
        if length >= 10:
            choice = input(input_tip)
        else:
            choice = readchar(input_tip)
        if not choice:
            return
        if choice.isnumeric():
            choice = int(choice)
        else:
            print(ColorStr.red(_("input error, please input again")))
            continue
        if (choice <= length and choice > 0):
            return choice
        else:
            print(ColorStr.red(_("input error, please input again")))

def readchar(prompt=""):
    if prompt:
        sys.stdout.write(prompt)
        sys.stdout.flush()
        
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(sys.stdin.fileno())
        ch = sys.stdin.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

    print("")
    return ch.strip()