from flask import Flask, redirect, request, render_template_string, session, url_for,jsonify
from scraper import urltest
import os
import claude_web
from reviews_analysis import ChatGPTReviewAnalyzer 
from database_handler import DatabaseHandler
from reviews_analyze_model import ReviewsAnalyzeModel
import hashlib
import time
import base64
import logging
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

    brand = session.get('brand', 'None')
    
    # 读取模板文件内容
    with open('templates/index.html', 'r') as file:
        template_content = file.read()
    
    # 替换按钮文本
    rendered_template = template_content.replace('None', brand)
    
    return render_template_string(rendered_template)

# 处理表单提交的路由
@app.route('/submit', methods=['POST'])
def submit():
    if request.method == 'POST':
        product_link = request.form['linkInput']
        print("Received product link:", product_link)
        
        # 检查 product_link 中是否包含 "THD"
        session['brand']=urltest(product_link)
        
        # 重定向回首页
        return redirect(url_for('index'))

    return redirect(url_for('index'))

# @app.route('/login', methods=['POST'])
# def login():
#     key = request.form['key']
#     # 这里应该是调用PSOCloudClient的login方法
#     return jsonify({'status': 'logged in', 'key': key})

# @app.route('/analyze', methods=['POST'])
# def analyze():
#     session = request.form['session']
#     key = request.form['key']
#     type = request.form['type']
#     host = request.form['host']
#     product_name = request.form['productName']
#     file = request.files['file']
    
#     # 这里应该是调用PSOCloudClient的analyze_reviews_file方法
#     # 由于演示目的，我们不处理文件上传
#     return jsonify({
#         'status': 'analysis sent',
#         'session': session,
#         'key': key,
#         'type': type,
#         'host': host,
#         'product_name': product_name
#     })

# @app.route('/result', methods=['POST'])
# def result():
#     session = request.form['session']
#     # 这里应该是调用PSOCloudClient的get_analysis_result方法
#     return jsonify({'status': 'result received', 'session': session})

@app.route('/login', methods=['POST'])
def login():
    # DatabaseHandler.initialize_pool(host="aitoolsql-aitoolsql.g.aivencloud.com",port='21968', database="defaultdb", user="avnadmin", password="AVNS_cnTwp6q_no-QkuZoNmW")
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

if __name__ == '__main__':
    # print("尝试连接数据库")
#     config = {
#     'host': 'aianalysis.mysql.database.azure.com',     # 数据库服务器地址
#     'user': '<ZDHH25U>',         # 数据库用户名
#     'port':'3306',
#     'password': '<Pp2766466225.>',         # 数据库密码
#     'database': '<pso_voc_tool>'   # 数据库名
# }
    # DatabaseHandler.initialize_pool(host="aitoolsql-aitoolsql.g.aivencloud.com",port='21968', database="defaultdb", user="avnadmin", password="AVNS_cnTwp6q_no-QkuZoNmW")
    # print("连接成功")
    # app.run(ssl_context=('/home/lighthouse/server/ssl_key/hubspace.run.place_nginx/hubspace.run.place_bundle.crt', '/home/lighthouse/server/ssl_key/hubspace.run.place_nginx/hubspace.run.place.key'),debug=True,host='0.0.0.0',port=443)
    app.run(debug=True)
#     config = {
#   'host':'aitoolsql-aitoolsql.g.aivencloud.com',
#   'port': '21968',
#   'user':'avnadmin',
#   'password':'AVNS_cnTwp6q_no-QkuZoNmW',
#   'database':'defaultdb'
# }