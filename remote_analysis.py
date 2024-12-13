import requests
import winreg
from datetime import datetime, timedelta
import socket,os,json
from time import sleep 
from pso_cloud_client import PSOCloudClient
from PySide6.QtCore import QObject, Signal
BASE_URL = "https://hubspace.run.place"
class ReviewAnalysisClient(QObject):
    logSignal = Signal(str)
    def __init__(self,key,host='remote3'):
        super(ReviewAnalysisClient, self).__init__() 
        self.proxy = None
        self.key = key
        self.server_url = 'http://43.134.112.182:8080/upload'
        self.host = host
        # self.file_to_upload = 'C:/Users/d87wvh/THD_VOC_Bot/EcoSmart 100-Watt Equivalent Smart A21 Color Changing CEC LED Light Bulb with Voice Control (1-Bulb) Powered by Hubspace 11A21100WRGBWH1 - The Home Depot.txt'
        # @staticmethod
    def log_error(self,message):
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f"[ERROR] {timestamp}: {message}")
        self.logSignal.emit(f"[ERROR] {timestamp}: {message}")
    
    # @staticmethod
    def log_debug(self,message):
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f"[DEBUG] {timestamp}: {message}")
        self.logSignal.emit(f"[DEBUG] {timestamp}: {message}")

    def get_proxy_settings_windows(self):
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, 'Software\\Microsoft\\Windows\\CurrentVersion\\Internet Settings') as key:
                proxy_enabled = winreg.QueryValueEx(key, 'ProxyEnable')[0]
                if proxy_enabled:
                    proxy_server = winreg.QueryValueEx(key, 'ProxyServer')[0]
                    return proxy_server
        except Exception as e:
            pass

    def configure_proxy(self):
        proxy_settings = self.get_proxy_settings_windows()
        
        if proxy_settings:
            self.proxy = {"http":f"{proxy_settings}", 'https':f"{proxy_settings}"}
            self.log_debug(f"Current System Proxy is {proxy_settings}, configuring the client to use Proxy Server: {self.proxy}")
            return 
            if "http" in proxy_settings or "https" in proxy_settings:
                parts = proxy_settings.split(';')
                http_part = next((part for part in parts if part.startswith("http=")), None)
                self.proxy = http_part.replace("=", "://")
            else:
                self.proxy = "http://" + proxy_settings
            
            self.log_debug(f"Current System Proxy is {proxy_settings}, configuring the client to use Proxy Server: {self.proxy}")
        else:
            self.log_debug("No proxy is enabled.")
            self.proxy = None

    def send_reviews_and_get_analysis(self,file_to_upload,type = 'overall'):
        method = 'socket_old'
        try:
            self.configure_proxy()
            if type == 'overall':
                prompt_text = """You will be presented with customer reviews and your job is to identify and list below 6 sections.
                1. top 5 most mentioned positive aspects (Pros) with their respective counts
                2. top 5 most mentioned negative aspects (Cons) with their respective counts
                3. top 5 most mentioned issues with their respective counts 
                4. top 5 most Purchase Motivations with their respective counts, 
                5. top 5 most mentioned customer Expectation with their respective counts
                6. top 5 suggestions for improvement. 
    Please aware use a json data to contain these information. make the section title as first level name of json data, the itmes and mentioned number as second level name and value of json data."""
            else:
                 prompt_text = """You will be presented with negative part of customer reviews and your job is to identify and list below 3 sections.
            1. top 5 most mentioned issues with their number of reviews mentioned.
            2. top 5 dislike or complaint from customer with their number of reviews mentioned. 
            3. point of view and valuable summary (more than 200 words).
Please aware use a json data to contain these information. make the section title as first level name of json data, the items and mentioned number as second level name and value of json data."""
            
            # key = "sk-DkK3A9CQcOVvv3bWZRaN55r7ek2XS0iUtAtKdasaBvm8INv6@15570"
            
            if method == 'socket_old':
                data = {'key': self.key, 'type':type, 'host' : self.host,'file_name':os.path.basename(file_to_upload),'file_size':os.path.getsize(file_to_upload)}
                server_address = ('43.134.112.182', 12345)
                # Create a socket
                client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                # Connect to the server
                client_socket.connect(server_address)
                file_info_json = json.dumps(data)
                client_socket.send(file_info_json.encode())

                try:
                    client_socket.settimeout(3)
                    msg = client_socket.recv(1024).decode()
                    if "valid_access" in msg:
                        self.log_debug(f"[SERVER]: {msg}")
                    else:
                        self.log_error(f"[SERVER]: {msg}")
                        client_socket.close()
                        return {'success': False, 'response': msg, 'message':msg}
                except socket.timeout:
                    self.log_error("[SERVER]: Timeout occurred")
                    client_socket.close()
                    return {'success': False, 'response': 'Timeout occurred','message':'Timeout occurred'}
                except Exception as e:
                    self.log_error(f"[SERVER]: An error occurred - {str(e)}")
                    client_socket.close()
                    return {'success': False, 'response': str(e), 'message':str(e)}
                file = open(file_to_upload, 'rb')
                while chunk := file.read(65535):
                    client_socket.send(chunk)
                    print(f"send: {len(chunk)}")
                          
                        
                """ Closing the file. """
                file.close()
                self.log_debug("finished to send file, close file")
                self.log_debug("waiting for analysis result... ...")
                client_socket.settimeout(10)
                result = client_socket.recv(65535)
                self.log_debug(f"received from server: {result}")
                while 'analysis' not in result.decode():
                    self.log_debug("waiting for analysis result... ...")
                    client_socket.settimeout(300)
                    result = client_socket.recv(65535)
                    self.log_debug(f"received from server: {result}")
                client_socket.send("ready to receive analysis result".encode())
                message = ""
                message_length = None
                message_icon, message_length = result.decode().split(":", 1)
                message_length = int(message_length)

                while True:
                    message_temp = client_socket.recv(1024)  # Adjust the buffer size as needed
                    if not message_temp:
                        break
                    
                    message_temp = message_temp.decode()
                    message += message_temp

                    if len(message) == message_length:
                        break

                self.log_debug(f"Received analysis message:{message}")
                
                client_socket.send("received result".encode())
                client_socket.close()
                return eval(message)
           
            else:
                if method == 'socket':
                    client = PSOCloudClient(method = 'socket')
                else:
                    client = PSOCloudClient(method = 'http')
                response = client.login(self.key)
                self.log_debug(f"Login: {response.status_code},{ response.text}")
                if response.status_code == 200:
                    session = response.json()['session_id']
                elif response.status_code == 401:
                    return {'success':False, 'response':response.json()['error'], 'message':response.json()['error']}
                else:
                    return {'success':False, 'response':'server error','message':'server error'}
                
                first_post_time = datetime.now()
                try:
                    response = client.analyze_reviews_file(session,self.key, type,self.host, os.path.basename(file_to_upload) ,file_to_upload)
                    if response.status_code == 200:
                        data = response.json()
                        self.log_debug(f"Reviews sent and analysis result received successfully: {data['analysis_result']}")
                        return {'success':True, 'response':data['analysis_result']}
                    else:
                        self.log_error(f'Failed to send reviews or receive analysis result. Server returned:+ {response.status_code} + {response.text}')
                        return {'success':False, 'response':response.text, 'message':response.text}
                    
                except FileNotFoundError:
                    # Handle file not found error
                    self.log_error("File not found error occurred.")
                    return {'success': False, 'response': None, 'message': 'File not found'}

                except PermissionError:
                    # Handle file permission error
                    self.log_error("File permission error occurred.")
                    return {'success': False, 'response': None, 'message': 'File permission error'}

                except Exception as e:
                # Handle other exceptions
                    self.log_error(f"An error occurred in _analyze_reviews_file: {e}")
                    retry = 0
                    while True:
                        response = client.get_analysis_result(session)
                        
                        if response.status_code == 200:
                            data = response.json()
                            if data['analysis_result'] is not None or data['analysis_result'] != '':
                                self.log_debug(f"_get_analysis_result received successfully: {data['analysis_result']}")
                                return {'success':True, 'response':data['analysis_result']}
                        
                        self.log_error(f'Failed to _get_analysis_result. Server returned:+ {response.status_code} + {response.text}')
                        retry +=1
                        if retry >=15:
                            break
                        current_time = datetime.now()
                        time_difference = current_time - first_post_time

                        if time_difference >= timedelta(minutes=3):
                            sleep_time = 3
                        else:
                            sleep_time = 20

                        sleep(sleep_time)

                    self.log_error(f'Failed to _get_analysis_result. Server returned:+ {response.status_code} + {response.text}')
                    return {'success':False, 'response':response.text, 'message':response.text}
        except Exception as e:
            self.log_error('An error occurred:' + str(e))
            return {'success':False, 'response':e, 'message':e}

if __name__ == "__main__":
    client = ReviewAnalysisClient('sk-Q6qyMsryBQ5LDrIvFV3DgIJ6a718LI8NGM5iUKyXanLy0mCV')
    client.send_reviews_and_get_analysis('C:/Users/d87wvh/THD_VOC_Bot/EcoSmart 16.4 ft. Smart RGBWIC Dynamic Color Changing Dimmable Plug-In LED Neon Flex Strip Light Powered by Hubspace AL-NF-RGBICTW-1 - The Home Depot.txt')