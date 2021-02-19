# -*- coding: utf8 -*-
import json
import time
import requests
import urllib.parse
from bs4 import BeautifulSoup

# 强烈建议部署在非大陆区域，例如HK、SG等

USERNAME = '' # 这里填用户名，邮箱也可
PASSWORD = ''  # 这里填密码

# Server酱 http://sc.ftqq.com/?c=code
SCKEY = '' # 这里填Server酱的key，无需推送可不填 示例: SCU646xxxxxxxxdacd6a5dc3f6

# 酷推 https://cp.xuthus.cc
CoolPush_Skey = ''
# 通知类型 CoolPush_MODE的可选项有（默认send）：send[QQ私聊]、group[QQ群聊]、wx[个微]、ww[企微]
CoolPush_MODE = 'send'

# PushPlus https://pushplus.hxtrip.com/message
PushPlus_Token = ''

# Bark https://github.com/Finb/Bark
Bark_Url = '' # 这里填Bark服务器的URL，注意最后的/要保留 示例：https://api.day.app/yourkey/

# Power Automate https://flow.microsoft.com/ 自行定义触发后的动作，可请求其它webhook或直接发邮件
PowerAutomate_Url = '' # 设置“当收到 HTTP 请求时”触发器后自动生成的“HTTP POST URL” 示例：https://prod-09.southeastasia.logic.azure.com:443/workflows/xxxxxxx/triggers/manual/paths/invoke?api-version=xxxxxxxx
PowerAutomate_Json = {"title": "", "body": "", "automaticallyCopy": 0, "isArchive": 1, "sound": "horn"} # 设置“当收到 HTTP 请求时”触发器时定义的“请求正文 JSON 架构”，请自定义，并需同时修改后面def PowerAutomate():里的代码，此处以Bark的参数为例


desp = '' # 不用动
isFailed = False # 不用动


def print_(info):
    print(info)
    global desp
    desp = desp + info + '\n\n'


def login(username, password) -> (str, requests.session):
    headers = {
        "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 11_2_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.182 Safari/537.36",
        "origin": "https://www.euserv.com",
        "host": "support.euserv.com"
    }
    login_data = {
        "email": username,
        "password": password,
        "form_selected_language": "en",
        "Submit": "Login",
        "subaction": "login"
    }
    url = "https://support.euserv.com/index.iphp"
    session = requests.Session()
    f = session.post(url, headers=headers, data=login_data, verify=False)
    f.raise_for_status()
    if f.text.find('Hello') == -1:
        return '-1', session
    # print_(f.request.url)
    sess_id = f.request.url[f.request.url.index('=') + 1:len(f.request.url)]
    return sess_id, session


def get_servers(sess_id, session) -> {}:
    d = {}
    url = "https://support.euserv.com/index.iphp?sess_id=" + sess_id
    headers = {
        "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 11_2_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.182 Safari/537.36",
        "origin": "https://www.euserv.com",
        "host": "support.euserv.com"
    }
    f = session.get(url=url, headers=headers, verify=False)
    f.raise_for_status()
    soup = BeautifulSoup(f.text, 'html.parser')
    for tr in soup.select('#kc2_order_customer_orders_tab_content_1 .kc2_order_table.kc2_content_table tr'):
        server_id = tr.select('.td-z1-sp1-kc')
        if not len(server_id) == 1:
            continue
        flag = True if tr.select('.td-z1-sp2-kc .kc2_order_action_container')[
                           0].get_text().find('Contract extension possible from') == -1 else False
        d[server_id[0].get_text()] = flag
    return d


def renew(sess_id, session, password, order_id) -> bool:
    url = "https://support.euserv.com/index.iphp"
    headers = {
        "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 11_2_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.182 Safari/537.36",
        "Host": "support.euserv.com",
        "origin": "https://support.euserv.com",
        "Referer": "https://support.euserv.com/index.iphp"
    }
    data = {
        "Submit": "Extend contract",
        "sess_id": sess_id,
        "ord_no": order_id,
        "subaction": "choose_order",
        "choose_order_subaction": "show_contract_details"
    }
    session.post(url, headers=headers, data=data, verify=False)
    data = {
        "sess_id": sess_id,
        "subaction": "kc2_security_password_get_token",
        "prefix": "kc2_customer_contract_details_extend_contract_",
        "password": password
    }
    f = session.post(url, headers=headers, data=data, verify=False)
    f.raise_for_status()
    if not json.loads(f.text)["rs"] == "success":
        return False
    token = json.loads(f.text)["token"]["value"]
    data = {
        "sess_id": sess_id,
        "ord_id": order_id,
        "subaction": "kc2_customer_contract_details_extend_contract_term",
        "token": token
    }
    session.post(url, headers=headers, data=data, verify=False)
    time.sleep(5)
    return True


def check(sess_id, session):
    print_("...复查结果...")
    d = get_servers(sess_id, session)
    global isFailed
    for key, val in d.items():
        if val:
            isFailed = True
            print_("ServerID: %s 续期失败!" % key)
    if isFailed == False:
        print_("全部完成！")


# Server酱 http://sc.ftqq.com/?c=code
def server_chan():
    text = 'EUserv续费'
    global isFailed
    text += '失败' if isFailed else '成功'
    data = (
        ('text', text),
        ('desp', desp)
    )
    response = requests.post('https://sc.ftqq.com/' + SCKEY + '.send', data=data)
    if response.status_code != 200:
        print("Server酱 推送失败！")
    else:
        print("Server酱 推送成功！")


# 酷推 https://cp.xuthus.cc/
def CoolPush():
    c = 'EUserv续费'
    global isFailed
    c += '失败' if isFailed else '成功'
    c += '\n\n' + desp
    data = json.dumps({'c': c})
    url = 'https://push.xuthus.cc/' + CoolPush_MODE + '/' + CoolPush_Skey
    response = requests.post(url, data=data)
    if response.status_code != 200:
        print('酷推 推送失败')
    else:
        print('酷推 推送成功')


# PushPlus https://pushplus.hxtrip.com/message
def PushPlus():
    title = 'EUserv续费'
    global isFailed
    title += '失败' if isFailed else '成功'
    data = (
        ('token', PushPlus_Token),
        ('title', title),
        ('content', desp)
    )
    url = 'http://pushplus.hxtrip.com/send'
    response = requests.post(url, data=data)
    if response.status_code != 200:
        print('PushPlus 推送失败')
    else:
        print('PushPlus 推送成功')


# Bark https://github.com/Finb/Bark
def Bark():
    title = 'EUserv续费'
    global isFailed
    title += '失败' if isFailed else '成功'
    body = urllib.parse.quote_plus(desp.replace('\n\n', '\n'))
    response = requests.get(Bark_Url + title + '/' + body)
    if response.status_code != 200:
        print("Bark 推送失败！")
    else:
        print("Bark 推送成功！")


# Power Automate https://flow.microsoft.com/ 自行定义触发后的动作，可请求其它webhook或直接发邮件
def PowerAutomate():
    title = 'EUserv续费'
    global isFailed
    title += '失败' if isFailed else '成功'
    PowerAutomate_Json['title'] = title
    PowerAutomate_Json['body'] = desp.replace('\n\n', '\n')
    response = requests.post(PowerAutomate_Url, json=PowerAutomate_Json)
    if response.status_code != 200:
        print("PowerAutomate 推送失败！")
    else:
        print("PowerAutomate 推送成功！")


def main_handler(event, context):
    isNeeded = False
    if not USERNAME or not PASSWORD:
        print_("你没有添加任何账户！")
        exit(1)
    user_list = USERNAME.strip().split()
    passwd_list = PASSWORD.strip().split()
    if len(user_list) != len(passwd_list):
        print_("用户名密码个数不匹配！")
        exit(1)
    for i in range(len(user_list)):
        print('*' * 30)
        print_("正在续费第 %d 个账号..." % (i + 1))
        sessid, s = login(user_list[i], passwd_list[i])
        if sessid == '-1':
            print_("第 %d 个账号登陆失败，请检查登录信息!" % (i + 1))
            continue
        SERVERS = get_servers(sessid, s)
        print_("检测到第 {} 个账号有 {} 台VPS，正在尝试续期...".format(i + 1, len(SERVERS)))
        for k, v in SERVERS.items():
            if v:
                isNeeded = True
                if not renew(sessid, s, passwd_list[i], k):
                    print_("ServerID: %s 续期失败！" % k)
                else:
                    print_("ServerID: %s 续期成功！" % k)
            else:
                print_("ServerID: %s 无需续期！" % k)
        time.sleep(15)
        check(sessid, s)
        time.sleep(5)


    # 5个通知渠道至少选取1个
    if isNeeded:
        SCKEY and server_chan()
        CoolPush_MODE  and CoolPush_Skey and CoolPush()
        PushPlus_Token and PushPlus()
        Bark_Url and Bark()
        PowerAutomate_Url and PowerAutomate_Json and PowerAutomate()

    print('*' * 30)
