import aiohttp
import asyncio
import json
import logging
import base64
import os
import winreg

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
# https://toll-cddpbre0ffgrc7hv.canadacentral-01.azurewebsites.net
# http://127.0.0.1:5000
class PSOCloudClientHTTP:
    def __init__(self, host='http://127.0.0.1:5000', proxy=None):
        self.host = host
        self.proxy = proxy

    async def login(self, key):
        url = f"{self.host}/login"
        data = {'key': 'sk-Q6qyMsryBQ5LDrIvFV3DgIJ6a718LI8NGM5iUKyXanLy0mCV'}
        async with aiohttp.ClientSession() as session:
            async with session.post(url, data=data, timeout=20) as response:
                # 打印响应状态码
                print(f"Status: {response.status}")
                # 打印响应内容
                response_text = await response.text()
                print(f"Response: {response_text}")
                # 如果您希望返回 JSON 数据，确保服务器返回的是 JSON 格式的响应
                try:
                    return await response.json()
                except aiohttp.ContentTypeError:
                    # 如果响应不是 JSON 格式，返回响应文本
                    return response_text

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
                    async with session.post(url, data=data, timeout=60) as response:
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
    client = PSOCloudClientHTTP()
    key = 'sk-Q6qyMsryBQ5LDrIvFV3DgIJ6a718LI8NGM5iUKyXanLy0mCV'
    response = await client.login(key)
    print("logging_info:")
    logging.info(response)

    # Assuming you have a valid session_id from the login process
    session_id =response['session_id']
    response = await client.analyze_reviews_file(session_id, key, 'overall', 'remote3', 'Philips', 'THD_VOC_Bot_Temp\White Cordless Room Darkening Vinyl Mini Blinds with 1 in. Slats-23 in. W x 72 in. L (Actual Size 22.5 in. W x 72 in. L) 10793478354023 - The Home Depot_r12.txt')
    logging.info(response)

    response = await client.get_analysis_result(session_id)
    logging.info(response)

if __name__ == '__main__':
    asyncio.run(main())
    