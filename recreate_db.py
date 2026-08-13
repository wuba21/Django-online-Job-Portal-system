import pymysql
try:
    conn = pymysql.connect(host='127.0.0.1', user='root', password='')
    cursor = conn.cursor()
    cursor.execute("DROP DATABASE IF EXISTS django_jobs_db;")
    cursor.execute("CREATE DATABASE django_jobs_db CHARACTER SET utf8 COLLATE utf8_general_ci;")
    print("Database 'django_jobs_db' recreated successfully with utf8.")
except Exception as e:
    print(f"Error: {e}")
