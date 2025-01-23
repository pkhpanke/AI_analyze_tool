from flask import Flask, redirect, request, render_template_string, session, url_for,jsonify,send_file
from scraper import urltest,ScraperThread
import os
import claude_web
from reviews_analysis import ChatGPTReviewAnalyzer 
from database_handler import DatabaseHandler
from reviews_analyze_model import ReviewsAnalyzeModel
import hashlib
import time
import base64
import logging
from thd_reviews import THDReviews
import csv
from drawrating import generate_chart,generate_charts
import google.generativeai as genai
import aiohttp
import asyncio
from test_asycloud_client import PSOCloudClientHTTP
GEMINI_API_KEY = "AIzaSyAFN7Jn5lLXgeXPH0H7jc8CX63QGsMrzoE"
# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='[%(levelname)s] %(asctime)s - %(filename)s:%(funcName)s:%(lineno)d - %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')

app = Flask(__name__)
app.secret_key = "asdasdasdasd"
UPLOAD_FOLDER = 'THD_VOC_Bot_Temp'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# 渲染 index.html 页面的路由
@app.route('/', methods=['GET'])
@app.route('/', methods=['GET'])
def index():

    with open('templates/index.html', 'r') as file:
        template_content = file.read()

    return template_content

# 处理表单提交的路由
@app.route('/submit', methods=['POST'])
def submit():
    product_link = request.form['linkInput']
    brand = urltest(product_link)

    scraper=ScraperThread(product_link)
    scraper.start()  # 启动线程
    scraper.join()  # 等待线程完成
    if scraper.scrap_success:
        logging.info("Scraping successful.")
        # 这里可以处理 scraper_thread 中的数据
        print(f"Product Name: {scraper.productname}")
        print(f"Reviews Count: {len(scraper.reviews)}")
        for review in scraper.reviews:
            print(f"Review: {review}")
        if scraper.product_image_file_path:
            print(f"Image saved at: {scraper.product_image_file_path}")
        else:
            print("No image content available.")
    else:
        logging.info("Scraping failed.")
    # 评论已经抓取成功，需要反馈回页面
    columns_to_read = ['\ufeffTitle', 'ReviewText', 'Rating', 'SubmissionTime']

# 初始化一个空字典来存储列的索引
    column_indices = {column: None for column in columns_to_read}

# 打开CSV文件
    with open('data.csv', 'r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        column_names = reader.fieldnames


        # 找到你想要读取的列的索引
        for idx, column in enumerate(reader.fieldnames):
            if column in columns_to_read:
                column_indices[column] = idx


        csv_data = []

    # 检查是否所有列都找到了
        if None in column_indices.values():
            print("One or more columns not found in the CSV file.")
        else:
            logging.info("所有列都已找到。")

        for row in reader:
            selected_row = {}
            for column in columns_to_read:
                if column in row:
                    if row[column] == None or row[column] == '':
                        selected_row[column] = "None"
                    else:
                        selected_row[column] = row[column]
                else:
                    selected_row[column] = "Donthave"

            csv_data.append(selected_row)
        print(scraper.product_info)
        # 画图表
        generate_chart(scraper.product_info)
        generate_charts(scraper.product_info)
        print(scraper.product_info)
    return jsonify({'brand': brand, 'csvData': csv_data, 'productname': scraper.productname,'productinfo': scraper.product_info})

@app.route('/download-csv')
def download_csv():
    logging.info("点击成功")
    csv_file_path = 'data.csv'  # 确保这是你CSV文件的正确路径
    return send_file(csv_file_path, as_attachment=True)


@app.route('/login', methods=['POST'])
def login():
    DatabaseHandler.initialize_pool(host="aitoolsql-aitoolsql.g.aivencloud.com",port='21968', database="defaultdb", user="avnadmin", password="AVNS_cnTwp6q_no-QkuZoNmW")
    db = DatabaseHandler()
    db.connect()
    logging.info("Inite a database connection")
    key = request.form.get('key')
    user_details = db.is_user_access_valid(key)
    print(user_details)
    if user_details:
        logging.info(f"User ID: {user_details[0]}, User Name: {user_details[1]}")
        session_id = generate_session_id(key)
        db.insert_visit_log_login(user_details[0], user_details[1], session_id)
        # Return HTTP 200 status and JSON data with session_id
        db.close()
        logging.info("close a database connection")
        return jsonify({"session_id": session_id}), 200
    else:
        logging.error("Access not valid or user does not exist.")
        db.close()
        logging.info("close a database connection")
        return jsonify({"error": "Access not valid or user does not exist."}), 401
    

@app.route('/analyze_file', methods=['POST'])
def analyze_file():
    db = None  # Initialize db to None
    try:
        prompt = request.form.get('prompt')
        key = request.form.get('key')
        session_id = request.form.get('session_id')
        type = request.form.get('type')
        host = request.form.get('host')
        product_name = request.form.get('product_name')
        if prompt:
            logging.info(f'Received prompt: {prompt}')
        if type:
            logging.info(f'Received type:, {type}')
        if host:
            logging.info(f'Received type:, {host}')
        if product_name:
            logging.info(f'Received type:, {product_name}')
        if 'file' not in request.files:
            logging.error('No file part')
            return jsonify({"error": "No file part", "analysis_success": False}), 400


        file = request.files['file']
        
        if file.filename == '':
            return jsonify({"error": "No selected file", "analysis_success": False}), 400
        filename_prefix = file.filename[:6]
        # Ensure the folder exists, create it if necessary
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        # Save the file to the specified folder with its original filename

        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename_prefix)
        file.save(file_path)
        # Print the file path where the uploaded file is saved
        logging.info(f'File saved at:, {file_path}')

        db = DatabaseHandler()
        db.connect()
        logging.info("Inite a database connection")
        # ret = db.check_sessionid(session_id)
        db.close()
        logging.info("close a database connection")
        db = None
        # if ret is False:
        #     return jsonify({"error": "wrong session", "analysis_success": False}), 500
        analyzer = ReviewsAnalyzeModel(host)
        result = analyzer.analyze_reviews_from_file(file_path,type =type, product_name = product_name)
        logging.info(result)
        if result['status']:
            response = result['data']['analysis_result']
            model=  result['data']['metadata']['model']
            finish_reason =result['data']['metadata']['finish_reason']
            token_input =result['data']['metadata']['token_input']
            token_output =result['data']['metadata']['token_output']
            error_code = ''
            ret_code = 200
        else:
            response = ''
            model=  ''
            finish_reason =''
            token_input = 0
            token_output = 0
            error_code = result['message']
            ret_code = 500
        log_data = {
            'product_link': file.filename,
            'analysis_success': result['status'],
            'analysis_result': response,
            'error_code': error_code,
            'model':model,
            'finish_reason':finish_reason,
            'token_input': token_input,
            'token_output': token_output
        }
        db = DatabaseHandler()
        db.connect()
        logging.info("Inite a database connection")
        db.update_visit_log(session_id,log_data)
        db.update_user_usage(user_id = None, token_usage_increment=token_input+token_output, user_key=key)
        db.close()
        logging.info("close a database connection")
        db = None

        return jsonify({"analysis_success": result['status'], "analysis_result": response, "error": result['message']}), ret_code
    except Exception as e:
        # Log the exception for debugging purposes
        logging.error(f"An error occurred: {str(e)}")
        # Return a JSON response with the error details
        return jsonify({"error": str(e), "analysis_success": False}), 500
    finally:
        if db is not None:  # Check if db is defined
            db.close()
            logging.info("close a database connection")

@app.route('/get_analysis_result', methods=['POST'])
def get_analysis_result():
    db = None  # Initialize db to None
    try:
        session_id = request.form.get('session_id')

        db = DatabaseHandler()
        db.connect()
        logging.info("Inite a database connection")
        ret = db.check_sessionid(session_id)
        if ret is False:
            db.close()
            logging.info("close a database connection")
            db = None
            return jsonify({"error": "wrong session", "analysis_success": False}), 500
        result = db.get_analysis_result_fromdatabase(session_id)
        db.close()
        logging.info("close a database connection")
        db = None
        if result is None or result == '':
            return jsonify({"error": "please waiting for a moment", "analysis_success": False}), 500

        logging.info(result)
        return jsonify({"analysis_success": True, "analysis_result": result, "error": None}), 200
    except Exception as e:
        # Log the exception for debugging purposes
        logging.error(f"An error occurred: {str(e)}")
        # Return a JSON response with the error details
        return jsonify({"error": str(e), "analysis_success": False}), 500
    finally:
        if db is not None:  # Check if db is defined
            db.close()
            logging.info("close a database connection")



def generate_session_id(key):
    # Get the current timestamp
    timestamp = str(time.time())

    # Combine the key with the timestamp
    combined = key + timestamp

    # Create a SHA-256 hash of the combined string
    hash_object = hashlib.sha256(combined.encode())
    hashed_string = hash_object.digest()

    # Encode the hash in base64
    encoded = base64.b64encode(hashed_string)

    # Optionally, you can truncate or adjust the length. Here, we keep it as is
    # since base64 encoding of SHA-256 hash will be around 44 characters.
    return encoded.decode('utf-8')


# 添加一个新的路由 /ai
# @app.route('/ai', methods=['POST'])
# def ai():
#     # 从请求中获取 key
#     key = request.form.get('key')
#     if not key:
#         return jsonify({"error": "Key is required"}), 400

#     # 定义一个异步函数用于执行 AI 分析
#     async def main():
#         client = PSOCloudClientHTTP()
#         response = await client.login(key)
#         logging.info("logging_info:")
#         logging.info(response)

#         # Assuming you have a valid session_id from the login process
#         session_id = response.get('session_id')
#         if not session_id:
#             return jsonify({"error": "Login failed"}), 401

#         file_path = 'data.csv'  # 服务器端的 data.csv 文件路径
#         response = await client.analyze_reviews_file(session_id, key, 'overall', 'remote3', 'Philips', file_path)
#         logging.info(response)

#         response = await client.get_analysis_result(session_id)
#         logging.info(response)

#         return jsonify({"message": "AI analysis started"}), 200

#     # 使用 asyncio.run 运行异步函数
#     return asyncio.run(main())


# 用于测试页面的回报相应内容
@app.route('/ai', methods=['POST'])
def ai():
    key = request.form.get('key')
    if not key:
        return jsonify({"error": "Key is required"}), 400

    # 模拟的 response
    response = {
        "message": "AI analysis started",
        "analysis_success": True,
        "Customer Persona": {
            "description": "The typical customer is a homeowner or DIY enthusiast who values smart lighting solutions for their home. They appreciate features such as adjustable color temperatures, ease of installation, and the ability to control lighting via smartphone apps. These customers tend to be tech-savvy and are looking for products that blend functionality with aesthetic appeal."
        },
        "Usage Scenarios": {
            "Home interior lighting": 20,
            "Dimming functionalities": 11,
            "Smart home integration": 8,
            "Easy installation": 7,
            "Outdoor lighting": 1
        },
        "Positive Aspects (Pros)": {
            "easy to install": 5,
            "adjust lighting color": 4,
            "smart controls (dimming, on/off, different colors)": 3,
            "works well": 3,
            "quality product": 2,
            "quick install": 2,
            "control each light individually or in a group": 1,
            "dim the recessed LED permanently": 1,
            "great illumination": 1,
            "economical replacement": 1
        },
        "Negative Aspects (Cons)": {
            "connectivity issues (Bluetooth, WiFi)": 4,
            "poor quality (buzzing, flickering)": 2,
            "lights go offline": 1,
            "defective products": 1
        },
        "Suggestions for Improvement": {
            "suggestion": "Improve the Wi-Fi connectivity reliability and Bluetooth performance. Address product quality issues related to dimming and flickering. Additionally, enhance the customer support experience for troubleshooting connection issues."
        }
    }

    return jsonify(response), 200

if __name__ == '__main__':

    DatabaseHandler.initialize_pool(host="aitoolsql-aitoolsql.g.aivencloud.com",port='21968', database="defaultdb", user="avnadmin", password="AVNS_cnTwp6q_no-QkuZoNmW")
    print("连接成功")
    app.run(debug=True)
