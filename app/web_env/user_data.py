import mysql.connector
import json
import bcrypt
import sys

def hash_password(plain_password):
    # 生成盐值并加密密码
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(plain_password.encode('utf-8'), salt)
    return hashed_password.decode('utf-8')

def verify_password(plain_password, hashed_password):
    # 验证密码是否匹配
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

# 创建数据库连接
def get_db_connection():
    conn = mysql.connector.connect(
        host='121.40.127.186',
        user='root',
        password='llm_image',
        database='llm_image',
        charset="utf8mb4"
    )
    return conn

def create_user_table():
    conn = get_db_connection()
    cursor = conn.cursor()

    # 创建用户数据表，并修改 image 为 image_id，设置外键约束
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS user (
        id INT AUTO_INCREMENT PRIMARY KEY,          -- 自增主键
        username VARCHAR(50) NOT NULL,              -- 用户名
        password VARCHAR(255) NOT NULL,             -- 密码
        image_id INT,                               -- 当前分配的影像ID
        current_analysis_id INT,                    -- 当前处理的数据ID
        position VARCHAR(100),                      
        FOREIGN KEY (image_id) REFERENCES image_data(id) ON DELETE SET NULL, -- 关联 image_data 表
        FOREIGN KEY (current_analysis_id) REFERENCES image_analysis(id) ON DELETE SET NULL  -- 关联 image_analysis 表
    ) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

    ''')
    conn.commit()
    conn.close()


def insert_user(username, password, image_id=None, current_analysis_id=None, position=None):
    conn = get_db_connection()
    cursor = conn.cursor()

    # 加密密码
    hashed_password = hash_password(password)

    # 插入数据到用户表
    cursor.execute('''
    INSERT INTO user (username, password, image_id, current_analysis_id, position)
    VALUES (%s, %s, %s, %s, %s)
    ''', (username, hashed_password, image_id, current_analysis_id, position))


    conn.commit()
    conn.close()

if __name__ == '__main__':
    # create_user_table()
    if len(sys.argv) > 1:
        insert_user(sys.argv[1], sys.argv[2])
    else:
        insert_user("test", "test")
    
    
