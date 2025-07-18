import logging
from utils.config import SERVER_CONFIG, DB_CONFIG
from utils.config import get_db_connection

import mysql.connector
import pandas as pd
from flask import Flask, jsonify, request, Response, render_template, render_template_string, send_file
from flask_mail import Mail
from flask_cors import CORS
import cv2
import numpy as np
import os
import time
import json
import hashlib

from core.analyzer import Analyzer
from core.capture import CameraCapture
from core.scheduler import Scheduler
from models.report_generator import ReportGenerator
from utils.config import SERVER_CONFIG
from core.classifier import Classifier

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "http://localhost:8000"}}, supports_credentials=True)
mail = Mail(app)
camera_instance = CameraCapture()  # 全局唯一摄像头实例
s = Scheduler(mail, app,camera_instance)  # 传入app实例

analyzer_instance = Analyzer()  # 全局Analyzer实例，避免重复初始化
classifier_instance = Classifier()  # 全局Classifier实例

#USERS_FILE = os.path.join(os.path.dirname(__file__), "users.json")

# def load_users():
#     if not os.path.exists(USERS_FILE):
#         return {}
#     with open(USERS_FILE, "r", encoding="utf-8") as f:
#         try:
#             return json.load(f)
#         except:
#             return {}
#
#
# def save_users(users):
#     with open(USERS_FILE, "w", encoding="utf-8") as f:
#         json.dump(users, f, ensure_ascii=False, indent=2)


def hash_pwd(pwd):
    return hashlib.sha256(pwd.encode('utf-8')).hexdigest()


@app.route('/api/register', methods=['POST'])
def api_register():
    data = request.get_json()

    print("收到登录请求")  # 添加调试输出
    print("请求头:", request.headers)

    name = data.get('name', '').strip()
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')
    if not name or not email or not password:
        return jsonify({'error': '信息不完整'}), 400
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

    # users = load_users()
    # if email in users:
    #     return jsonify({'error': '该邮箱已注册'}), 400
    # users[email] = {
    #     'name': name,
    #     'email': email,
    #     'password': hash_pwd(password)
    # }
    # save_users(users)
    # return jsonify({'email': email})
        # 插入新用户
        hashed_password = hash_pwd(password)
        cursor.execute(
            "INSERT INTO users (name, email, password) VALUES (%s, %s, %s)",
            (name, email, hashed_password)
        )
        conn.commit()
        return jsonify({'email': email})

    except mysql.connector.Error as err:
        print(f"注册数据库错误: {err}")
        return jsonify({'error': '注册失败，请稍后再试'}), 500

    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()


@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.get_json()
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # 查询用户
        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        user = cursor.fetchone()
        if not user or user['password'] != hash_pwd(password):
            return jsonify({'error': '邮箱或密码错误'}), 400

        return jsonify({'email': email})

    except mysql.connector.Error as err:
        print(f"登录数据库错误: {err}")
        return jsonify({'error': '登录失败，请稍后再试'}), 500

    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()


@app.route('/video_feed')
def video_feed():
    def generate():
        # camera = CameraCapture()  # 不再新建，改为用全局实例
        while True:
            frame = camera_instance.get_frame()
            # 实时分析不做预处理
            image, posture_status, hunchback_status, metrics = analyzer_instance.analyze(frame, preprocessing=False)
            ret, jpeg = cv2.imencode('.jpg', image)
            if not ret:
                continue
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + jpeg.tobytes() + b'\r\n')
    return Response(generate(), mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/analyze', methods=['POST'])
def analyze_image():
    if 'image' not in request.files:
        return jsonify({'error': "未上传图片"}), 400

    file = request.files['image']
    print(f"收到文件: {file.filename}")

    if file.filename == '':
        return jsonify({'error': "未选择图片"}), 400

    # 读取图片为OpenCV格式
    file_bytes = np.frombuffer(file.read(), np.uint8)
    img = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
    print(f"图片读取成功: {img is not None}")

    if img is None:
        return jsonify({'error': "图片格式错误"}), 400

    # 进行预处理和姿势分析（不写入日志）
    image, posture_status, hunchback_status, metrics = analyzer_instance.analyze(img, preprocessing=True)

    # 保存标注后图片到 static/tmp 目录
    tmp_dir = os.path.join(os.path.dirname(__file__), "static", "tmp")
    if not os.path.exists(tmp_dir):
        os.makedirs(tmp_dir)
    filename = f"analyzed_{int(time.time())}.jpg"
    out_path = os.path.join(tmp_dir, filename)
    cv2.imwrite(out_path, image)
    print(f"处理后图片保存路径: {out_path}")

    # 返回分析结果和图片下载链接
    return jsonify({
        'ear_shoulder': metrics['ear_shoulder'],
        'shoulder_hip': metrics['shoulder_hip'],
        'posture_status': '异常' if posture_status else '正常',
        'hunchback_status': '异常' if hunchback_status else '正常',
        'spine_angle': metrics.get('spine_angle', ''),
        'filename': filename
    })


@app.route('/classify', methods=['POST'])
def classify_image():
    if 'image' not in request.files:
        return jsonify({'error': "未上传图片"}), 400

    file = request.files['image']
    if file.filename == '':
        return jsonify({'error': "未选择图片"}), 400
    try:
        # 读取图片为字节流
        image_bytes = file.read()
        # 调用分类方法
        result = classifier_instance.classify_image(image_bytes)
        # 添加调试输出
        print(f"分类结果: {result}")

        # 确保返回结果包含姿态和置信度
        if 'class' in result and 'conf' in result:
            return jsonify({
                'posture': result['class'],  # good 或 bad
                'confidence': float(result['conf'])  # 置信度
            })
        else:
            return jsonify({'error': "无效的分类结果"}), 500

    except Exception as e:
        print(f"处理分类请求时出错: {str(e)}")
        return jsonify({'error': f"处理请求时发生错误: {str(e)}"}), 500


@app.route('/download_analyzed')
def download_analyzed():
    filename = request.args.get('filename')
    tmp_dir = os.path.join(os.path.dirname(__file__), "logs", "tmp")
    file_path = os.path.join(tmp_dir, filename) if filename else None

    if not file_path or not os.path.exists(file_path):
        return "文件不存在", 404
    return send_file(file_path, mimetype='image/jpeg')



@app.route('/api/daily_report', methods=['GET'])
def daily_report():
    date_str = request.args.get('date')

    if not date_str:
        return jsonify({"error": "缺少日期参数"}), 400

    try:
        logging.debug(f"Received request for date: {date_str}")
        report_generator = ReportGenerator()
        report_data = report_generator.generate_daily_report(date_str)
        logging.debug(f"Generated report data: {report_data}")
        return jsonify(report_data)

    except Exception as e:
        logging.error(f"Error generating report: {str(e)}")
        return jsonify({
            "error": str(e),
            "date": date_str
        }), 500

@app.route("/api/latest_postures")
def get_latest_postures():
    try:
        # 1. CSV 路径
        filepath = os.path.join('logs', 'posture_log.csv')

        # 2. 读取 CSV 文件
        df = pd.read_csv(filepath)

        # 3. 只保留需要的字段
        columns_to_keep = ["Timestamp", "EarShoulderDiff", "ShoulderHipDiff", "PostureStatus"]
        df = df[columns_to_keep]

        # 4. 替换 NaN/inf 为 None（防止 JSON 无法解析）
        df.replace({np.nan: None, np.inf: None, -np.inf: None}, inplace=True)

        # 5. 获取最近 20 条记录
        last_20_rows = df.tail(20)

        # 6. 转换为 JSON 响应
        return jsonify(last_20_rows.to_dict(orient='records'))

    except Exception as e:
        print("读取或处理日志数据失败：", str(e))
        return jsonify({'error': str(e)}), 500


def start_background_tasks():
    s.start()


if __name__ == '__main__':
    try:
        start_background_tasks()
        app.run(host='0.0.0.0', port=SERVER_CONFIG['PORT'])
    finally:
        camera_instance.release()
