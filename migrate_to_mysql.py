import mysql.connector
import json
import csv
from datetime import datetime

# 数据库配置（
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'Sunjia1+1=2',  # 改成你的 MySQL 密码
    'database': 'sittingwatch'
}

# 读取 users.csv（实际上是 JSON 格式）
with open('users.json', 'r') as f:
    users_data = json.load(f)

# 连接数据库
conn = mysql.connector.connect(**db_config)
cursor = conn.cursor()

# 插入用户数据
print("[*] 正在导入用户数据...")
for email, user_info in users_data.items():
    try:
        cursor.execute(
            "INSERT INTO users (email, name, password) VALUES (%s, %s, %s)",
            (email, user_info['name'], user_info['password'])
        )
    except mysql.connector.Error as e:
        print(f"插入用户失败 {email}: {e}")

# 插入姿势日志数据
print("[*] 正在导入姿势日志数据...")

user_email = list(users_data.keys())[0]  # 默认只有一个用户，对应 posture_log.csv

with open('logs/posture_log.csv', 'r') as f:
    reader = csv.DictReader(f)
    for row in reader:
        try:
            timestamp = datetime.strptime(row['Timestamp'].split('.')[0], "%Y-%m-%d %H:%M:%S")
            ear_shoulder = float(row['EarShoulderDiff']) if row['EarShoulderDiff'] else None
            shoulder_hip = float(row['ShoulderHipDiff']) if row['ShoulderHipDiff'] else None
            posture_status = row['PostureStatus'].strip().lower() == 'true'
            spine_angle = float(row['SpineAngle']) if row['SpineAngle'] else None
            hunchback_status = int(row['HunchbackStatus']) if row['HunchbackStatus'] else None

            cursor.execute(
                """INSERT INTO posture_logs 
                   (user_email, timestamp, ear_shoulder, shoulder_hip, posture_status, spine_angle, hunchback_status)
                   VALUES (%s, %s, %s, %s, %s, %s, %s)""",
                (user_email, timestamp, ear_shoulder, shoulder_hip, posture_status, spine_angle, hunchback_status)
            )
        except Exception as e:
            print(f"插入姿势日志失败: {row} -> {e}")

# 提交事务
conn.commit()
cursor.close()
conn.close()
print("[+] 数据导入完成！")
