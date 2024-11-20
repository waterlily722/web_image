import mysql.connector
import json

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


def create_image_table():
    conn = get_db_connection()
    cursor = conn.cursor()

    # 创建数据表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS image_data (
        id INT AUTO_INCREMENT PRIMARY KEY,         -- 自增主键
        image TEXT NOT NULL,                       -- 影像路径
        data_count INT NOT NULL,                   -- 数据量
        status ENUM('unlabeled', 'labeling', 'labeled') DEFAULT 'unlabeled'  -- 状态
    ) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
    ''')
    conn.commit()  
    conn.close() 

def insert_image_table(json_file):
    conn = get_db_connection()
    cursor = conn.cursor()

    with open(json_file, 'r', encoding='utf-8') as file:
        data = json.load(file)

    # image_counts = {}
    # for item in data:
    #     item_id = item['id']
    #     parts = item_id.split("_")[1:3]
    #     image = "_".join(parts)

    #     if image in image_counts:
    #         image_counts[image] += 1
    #     else:
    #         image_counts[image] = 1

    try:
        for item in data:
            cursor.execute('''
            INSERT INTO image_data (image, data_count, status) 
            VALUES (%s, %s, %s)
            ''', (item['image'], item['count'], 'unlabeled'))
    except Exception as e:
        print(f"Error inserting data: {e}")

    # 提交并关闭连接
    conn.commit()
    conn.close()

def backup_data_as_json(input_file, output_file):
    with open(input_file, 'r', encoding='utf-8') as file:
        data = json.load(file)

    # 提取影像名称并统计数据量
    image_counts = {}
    for item in data:
        item_id = item['id']
        parts = item_id.split("_")[1:3]
        image = "_".join(parts)

        if image in image_counts:
            image_counts[image] += 1
        else:
            image_counts[image] = 1

    backup_list = []
    for image, count in image_counts.items():
        backup_record = {
                "image": image,
                "count": count
            }
        backup_list.append(backup_record)

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(backup_list, f, ensure_ascii=False, indent=4)
    print(f"Backup successfully saved to {output_file}")

if __name__ == '__main__':
    # create_image_table()
    # backup_data_as_json('/home/web_image/sampled_data_new/image_analysis.json', '/home/web_image/sampled_data_new/image_update.json')
    insert_image_table('/home/web_image/sampled_data_new/image_update.json')