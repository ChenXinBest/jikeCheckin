# 极客云签到
import requests
import json
import os

# 读取用户名和密码
email = os.environ.get("jike_email")
passwd = os.environ.get("jike_password")

class jikeCheckin():
    proxies = {
        # "http":"http://127.0.0.1:10809",
        # "https":"http://127.0.0.1:10809"
    }

    session = requests.session()

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
        if flag is not None and flag:
            print("登录成功！正在签到……")
            result = self.checkIn()
            if result is not None and result["ret"] == 1:
                print("签到成功！成功信息如下：")
            else:
                print("签到失败！失败原因如下：")
            print(result["msg"])
        else:
            print("登录失败")
        return result


if __name__ == '__main__':
    jike = jikeCheckin()
    for i in range(3):
        result = jike.run()
        if result:
            break;
