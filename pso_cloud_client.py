import socket
import json
import os
import logging
import base64
import requests
import winreg

def get_proxy_settings_windows():
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, 'Software\\Microsoft\\Windows\\CurrentVersion\\Internet Settings') as key:
            proxy_enabled = winreg.QueryValueEx(key, 'ProxyEnable')[0]
            if proxy_enabled:
                proxy_server = winreg.QueryValueEx(key, 'ProxyServer')[0]
                # 构建代理字典
                proxies = {
                    'http': f'{proxy_server}',
                    'https': f'{proxy_server}'
                }
                return proxies
    except Exception as e:
        print(f"An error occurred: {e}")
        return None  # 返回 None 或空字典 {}


# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
HOST_SOCKET = '43.134.112.182'
PORT_SOCKET = 12345

HOST_HTTP = 'http://127.0.0.1:5000'
PORT_HTTP = 443

class ResponseData():
    def __init__(self,status_code, text):
        self.status_code = status_code
        self.text = text

    def json(self):
        return json.loads(self.text)



class PSOCloudClient():
    def __init__(self, host = None, port = None, method = 'socket', proxy = get_proxy_settings_windows()) -> None:
        self.host = host if host is not None else (HOST_SOCKET if method == 'socket' else HOST_HTTP)
        self.port = port if port is not None else (PORT_SOCKET if method == 'socket' else PORT_HTTP)
        self.method = method
        self.proxy = get_proxy_settings_windows()

    def login(self, key):
        if self.method == 'socket':
            return self.socket_login(key)
        else:
            return self.RESTful_login_hubspace_cloud(key)
    
    def analyze_reviews_file(self,session, key, type,host, product_name ,file_path):
        if self.method == 'socket':
            return self.socket_analyze_reviews_file(session, key, type,host, product_name ,file_path)
        else:
            return self.RESTful_analyze_reviews_file(session, key, type,host, product_name ,file_path)
    
    def get_analysis_result(self,session):
        if self.method == 'socket':
            return self.socket_get_analysis_result(session)
        else:
            return self.RESTful_get_analysis_result(session)
            
    def socket_post_request(self, path, data):
        content = json.dumps(data)  # Convert dict to json string
        content_length = len(content)

        # Prepare the POST request
        request = f"POST {path} HTTP/1.1\r\n" \
                    f"Host: {self.host}\r\n" \
                    f"Content-Type: application/json\r\n" \
                    f"Content-Length: {content_length}\r\n" \
                    f"Connection: close\r\n\r\n" \
                    f"{content}"


        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((self.host, self.port))
            s.sendall(request.encode('utf-8'))
            response = b''
            # Read the entire response
            while True:
                part = s.recv(4096)
                if not part:
                    break  # No more data, stop reading
                response += part
            
            s.close()
            status_code = self._extract_status_code(response.decode())
            # Split response into headers and body
            headers, _, body = response.decode().partition('\r\n\r\n')
            response = ResponseData(status_code, body)
            return response
            return({'status_code':status_code, 'text': json.loads(body)})

    def _extract_status_code(self, full_http_response):
        # The status line is the first line of the response
        status_line = full_http_response.split('\r\n')[0]
        # Split status line into components
        components = status_line.split(' ')
        # Typically, the status code is the second component (index 1)
        status_code = components[1]
        return int(status_code)  # Convert it to an integer before returning

    def socket_login(self, key):
        path = '/login'
        data = {'key': key}
        response = self.socket_post_request(path, data)
        # logging.info(response)
        return response
        if response['status_code'] == 200:
            # session_id = json.loads(response['text'])['session_id']
            # logging.info(f"session id: {session_id}")
            return session_id
        else:
            return None

    def socket_analyze_reviews_file(self,session, key, type,host, product_name ,file_path):
        # File part
        if file_path and os.path.isfile(file_path):
            filename = os.path.basename(file_path)
            with open(file_path, 'rb') as file:
                file_content = file.read()
            
            # Encode file_content with base64
            file_content_base64 = base64.b64encode(file_content).decode('utf-8')

        path = '/analyze_file'
        data = {
                'prompt': '',
                'key': key,
                'session_id': session,
                'type': type,
                'host': host,
                'product_name': product_name,
                'filename':filename, 'file_content':file_content_base64
            }

        response = self.socket_post_request(path, data)
        return response
        # logging.info(response)
        if response['status_code'] == 200:
            data = json.loads(response['text'])
            logging.info(f"Reviews sent and analysis result received successfully: {data['analysis_result']}")
            return {'success':True, 'response':data['analysis_result']}
        else:
            logging.error(f'Failed to send reviews or receive analysis result. Server returned:+ {response.status_code} + {response.text}')
            return {'success':False, 'response':response.text, 'message':response.text}

    def socket_get_analysis_result(self,session):
        
        path = '/get_analysis_result'
        data = {
                'session_id': session,
            }

        response = self.socket_post_request(path, data)
        return response
        # logging.info(response)
        if response['status_code'] == 200:
            data = json.loads(response['text'])
            logging.info(f"Reviews sent and analysis result received successfully: {data['analysis_result']}")
            return {'success':True, 'response':data['analysis_result']}
        else:
            logging.error(f"Failed to send reviews or receive analysis result. Server returned:+ {response['status_code']} + {response['text']}")

            return {'success':False, 'response':response['text'], 'message':response['text']}

    def RESTful_login_hubspace_cloud(self,key):
        url = f"{self.host}/login"
        data = {
            'key': key
        }
        # response = requests.post(url, data=data, timeout= 3, proxies= get_proxy_settings_windows())
        print("logining")
        response = requests.post(url, data=data, timeout= 10,proxies=None)
        print(response)
        return response
    
    def RESTful_analyze_reviews_file(self,session, key, type,host, product_name ,file_path):
        url = f"{self.host}/analyze_file"
        data = {
            'prompt': '',
            'key': key,
            'session_id': session,
            'type': type,
            'host': host,
            'product_name': product_name
        }
        files = {'file': open(file_path, 'rb')}
        # response = requests.post(url, data=data, files=files,timeout= 240, proxies=self.proxy)
        response = requests.post(url, data=data, timeout= 10)
        # print("Analyze File Test:", response.status_code, response.text)
        return response
    def RESTful_get_analysis_result(self,session):
        url = f"{self.host}/get_analysis_result"
        data = {
            'session_id': session,
        }
        response = requests.post(url, data=data,timeout= 3, proxies=self.proxy)
        # print("Analyze File Test:", response.status_code, response.text)
        return response

        
if __name__ == '__main__':
    client = PSOCloudClient(method = 'https')
    response =client.login('sk-Q6qyMsryBQ5LDrIvFV3DgIJ6a718LI8NGM5iUKyXanLy0mCV')
    logging.info((response))
    # logging.info((response.json()))

    # if session_id:
    #     client.analyze_reviews_file(session_id, 'sk-Q6qyMsryBQ5LDrIvFV3DgIJ6a718LI8NGM5iUKyXanLy0mCV','overall','remote3','Philips 60-Watt Equivalent A19 LED Smart Wi-Fi Color Changing Smart Light Bulb powered by WiZ with Bluetooth (1-Pack) 562702 - The Home Depot', 'C:/Users/d87wvh/THD_VOC_Bot/Philips 60-Watt Equivalent A19 LED Smart Wi-Fi Color Changing Smart Light Bulb powered by WiZ with Bluetooth (1-Pack) 562702 - The Home Depot.txt')
    # get_analysis_result('CnxsRP/OXoCH0auGBKDolW0VMUBOcVtkerSiV83Kdao=')
    
