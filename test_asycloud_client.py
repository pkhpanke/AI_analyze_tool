import aiohttp
import asyncio
import json
import logging
import base64
import os
import winreg

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class PSOCloudClient:
    def __init__(self, host='http://127.0.0.1:5000', proxy=None):
        self.host = host
        self.proxy = proxy

    async def login(self, key):
        url = f"{self.host}/login"
        data = {'key': 'sk-Q6qyMsryBQ5LDrIvFV3DgIJ6a718LI8NGM5iUKyXanLy0mCV'}
        async with aiohttp.ClientSession() as session:
            async with session.post(url, data=data, timeout=10) as response:
                return await response.json()

    # async def analyze_reviews_file(self, session, key, type, host, product_name, file_path):
    #     url = f"{self.host}/analyze_file"
    #     if os.path.isfile(file_path):
    #         filename = os.path.basename(file_path)
    #         with open(file_path, 'rb') as file:
    #             file_content = file.read()
    #         file_content_base64 = base64.b64encode(file_content).decode('utf-8')
    #         data = {
    #             'prompt': '',
    #             'key': key,
    #             'session_id': session,
    #             'type': type,
    #             'host': host,
    #             'product_name': product_name,
    #             'filename': filename,
    #             'file_content': file_content_base64
    #         }
    #         async with aiohttp.ClientSession() as session:
    #             async with session.post(url, data=data, timeout=10) as response:
    #                 return await response.json()
    async def analyze_reviews_file(self, session, key, type, host, product_name, file_path):
        url = f"{self.host}/analyze_file"
        if os.path.isfile(file_path):
            filename = os.path.basename(file_path)
            # 使用 aiohttp FormData 来构建 multipart/form-data 请求体
            data = aiohttp.FormData()
            data.add_field('prompt', '')
            data.add_field('key', key)
            data.add_field('session_id', session)
            data.add_field('type', type)
            data.add_field('host', host)
            data.add_field('product_name', product_name)
            # 打开文件并添加到 FormData
            with open(file_path, 'rb') as file:
                data.add_field('file', file, filename=filename, content_type='application/octet-stream')

                async with aiohttp.ClientSession() as session:
                    async with session.post(url, data=data, timeout=30) as response:
                        return await response.json()
        else:
            return {"error": "File does not exist"}

    async def get_analysis_result(self, session):
        url = f"{self.host}/get_analysis_result"
        data = {'session_id': session}
        async with aiohttp.ClientSession() as session:
            async with session.post(url, data=data, timeout=30) as response:
                return await response.json()

async def main():
    client = PSOCloudClient()
    key = 'sk-Q6qyMsryBQ5LDrIvFV3DgIJ6a718LI8NGM5iUKyXanLy0mCV'
    response = await client.login(key)
    print("logging_info:")
    logging.info(response)

    # Assuming you have a valid session_id from the login process
    session_id =response['session_id']
    response = await client.analyze_reviews_file(session_id, key, 'overall', 'remote3', 'Philips 60-Watt Equivalent A19 LED Smart Wi-Fi Color Changing Smart Light Bulb powered by WiZ with Bluetooth (1-Pack) 562702 - The Home Depot', 'Hampton Bay Lakeshore 13 in. Brushed Nickel Color Changing and Adjustable CCT Integrated LED Smart Flush Mount Powered by Hubspace SMACADER-MAGD01 - The Home Depot.csv')
    logging.info(response)

    # response = await client.get_analysis_result(session_id)
    # logging.info(response)

if __name__ == '__main__':
    asyncio.run(main())