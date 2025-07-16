#SERVER_CONFIG = {'PORT': 5001}
import mysql.connector

# 服务器配置
SERVER_CONFIG = {
    'PORT': 5001,
    'DEBUG': True
}

# 数据库连接配置
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'Sunjia1+1=2',  # ← 改成你真实的密码
    'database': 'sittingwatch',
    'raise_on_warnings': True
}
def get_db_connection():
    return mysql.connector.connect(**DB_CONFIG)
POSTURE_THRESHOLD = -0.255
LOG_FILE = './logs/posture_log.csv'
SAMPLING_INTERVAL = 3       # seconds between frames
ANOMALY_WINDOW = 10         # seconds window
ANOMALY_THRESHOLD = ANOMALY_WINDOW // SAMPLING_INTERVAL

EMAIL_FROM = 'SittingWatch@qq.com'
EMAIL_PASSWORD = 'urjlznsxfcxtbchi'
EMAIL_TO = ''  # 动态指定
MAIL_SERVER = 'smtp.qq.com'
MAIL_PORT = 465
MAIL_USE_SSL = True # 使用SSL
