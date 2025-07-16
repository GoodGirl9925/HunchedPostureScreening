import mysql.connector

db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'Sunjia1+1=2',
    'database': 'sittingwatch'
}

try:
    conn = mysql.connector.connect(**db_config)
    print("✅ 数据库连接成功！")
    conn.close()
except mysql.connector.Error as err:
    print(f"❌ 数据库连接失败: {err}")
