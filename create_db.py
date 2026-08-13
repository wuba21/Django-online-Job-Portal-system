import pymysql
try:
    conn = pymysql.connect(host='127.0.0.1', user='root', password='')
    cursor = conn.cursor()
    cursor.execute("CREATE DATABASE IF NOT EXISTS django_jobs_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
    print("Database 'django_jobs_db' created successfully.")
except Exception as e:
    print(f"Error: {e}")
