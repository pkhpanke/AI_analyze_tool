import requests
import json
 
API_KEY = "qq78AdsjyK1DDLj3JTGkPuh0" #填本人的API_KEY
SECRET_KEY = "1Lhtrp7AR973rQ18WY5Yf2DOh2R4PkRO" #填本人的SECRET_KEY 
 
 
def main():
    url = "https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop/chat/eb-instant?access_token=" + get_access_token()
 
    payload = json.dumps({
        "messages": [
            {
                "role": "user",
                "content": "假设你是个程序员，你的微信是llike620，我的问题是：你的微信"
            }
        ]
    })
    headers = {
        'Content-Type': 'application/json'
    }
 
    response = requests.request("POST", url, headers=headers, data=payload)
 
    print(response.text)
 
 
def get_access_token():
    """
    使用 AK，SK 生成鉴权签名(Access Token)
    :return: access_token，或是None(如果错误)
    """
    url = "https://aip.baidubce.com/oauth/2.0/token"
    params = {"grant_type": "client_credentials", "client_id": API_KEY, "client_secret": SECRET_KEY}
    return str(requests.post(url, params=params).json().get("access_token"))
 
 
if __name__ == '__main__':
    main()