# 极客云签到
import requests
import json
import os
from gotify import Gotify

# 读取用户名和密码
email = os.environ.get("jike_email")
passwd = os.environ.get("jike_password")
gotify_host = os.environ.get("gotify_host")
gotify_token = os.environ.get("gotify_token")

class jikeCheckin():
    proxies = {
        # "http":"http://127.0.0.1:10809",
        # "https":"http://127.0.0.1:10809"
    }

    session = requests.session()

    gotifyClient = None
    if gotify_token is not None and gotify_host is not None:
        gotifyClient = Gotify(base_url=gotify_host,app_token=gotify_token)

    def getResponse(self,url):
        if len(self.proxies)>0:
            return self.session.get(url,proxies=self.proxies)
        else:
            return self.session.get(url)

    def postResponse(self,url,data={}):
        if len(self.proxies)>0:
            return self.session.post(url=url,data=data,proxies=self.proxies)
        else:
            return self.session.post(url=url,data=data)

    def readResponse(self,response):
        response.encoding = response.apparent_encoding

    def login(self,loginUrl = "https://jike138.com/auth/login"):
        data = {
            "email":email,
            "passwd":passwd
        }
        response = self.postResponse(url=loginUrl,data=data)
        result = json.loads(response.text)
        flag = result["ret"]
        if flag == 1:
            return True
        else:
            return False

    def checkIn(self):
        response = self.postResponse("https://jike138.com/user/checkin")
        result = json.loads(response.text)
        return result

    def run(self):
        result = None
        flag=self.login()
        gotify_text = ''
        gotify_title =''
        if flag is not None and flag:
            print("登录成功！正在签到……")
            result = self.checkIn()
            if result is not None and result["ret"] == 1:
                gotify_title="签到成功！"
                print("签到成功！成功信息如下：")
            else:
                gotify_title="签到失败"
                print("签到失败！失败原因如下：")
            print(result["msg"])
            gotify_text=result["msg"]
        else:
            gotify_title="登录失败"
            gotify_text="登陆失败！"
            print("登录失败")
        if self.gotifyClient is not None:
            self.gotifyClient.create_message(
                title=gotify_title,
                message=gotify_text,
                priority=0,
            )
        return result


if __name__ == '__main__':
    jike = jikeCheckin()
    for i in range(3):
        result = jike.run()
        if result:
            break;
