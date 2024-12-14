import mysql.connector

def get_db_connection():
    conn = mysql.connector.connect(
        host='121.40.127.186',
        user='root',
        password='llm_image',
        database='llm_image',
        charset="utf8mb4"
    )
    return conn

# 获取上一张图片的ID
def get_previous_image_id(image_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT id FROM image_analysis
        WHERE id < %s
        ORDER BY id DESC
        LIMIT 1
    """, (image_id,))
    previous_image = cursor.fetchone()
    conn.close()
    return previous_image['id'] if previous_image else None

# 获取下一张图片的ID
def get_next_image_id(image_id):
    # print(image_id)
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT id FROM image_analysis
        WHERE id > %s
        ORDER BY id ASC
        LIMIT 1
    """, (image_id,))
    next_image = cursor.fetchone()
    conn.close()
    # print(next_image['id'])
    return next_image['id'] if next_image else None

# 获取依据 type 字段进行的答案选项
def get_mal_type_options(type_field, original_id):
    image_type = original_id.split('_')[-2]
    # 根据 type 字段进行更细致的划分
    if type_field == '安氏分类':
        return ['安氏I类', '安氏II类', '安氏III类']
    elif type_field == '骨性分类':
        return ['骨性I类', '骨性II类', '骨性III类']
    elif type_field in ['中线', '矢状关系']:
        return ['正常', '异常']
    elif type_field == '错合类型':
        if image_type == '侧位片':
            return ['开合', '牙前突', '上颌前突', '上颌发育不足', '下颌前突', '下颌后缩', '前牙反合']
        elif image_type == '口内正位像':
            return ['深覆合', '深覆盖', '开合', '前牙反合']
        elif image_type in ['口内左侧位像', '口内右侧位像']:
            return ['深覆合', '深覆盖', '前牙反合', '后牙锁合', '后牙反合']
        elif image_type in ['上牙列像', '下牙列像']:
            return ['拥挤', '牙列间隙']
        else:
            return ['拥挤', '牙列间隙', '深覆合', '深覆盖', '开合', '牙前突', '上颌前突', '上颌发育不足', '下颌前突', '下颌后缩', '前牙反合', '后牙锁合', '后牙反合']
    elif type_field == '面型':
        return [ '正常', '上颌前突', '上颌发育不足', '下颌前突', '下颌后缩']
    else:
        return ['是', '否']

def get_new_position(data_id, image_id):
    conn = get_db_connection() 
    cursor = conn.cursor(dictionary=True)  

    try:
        # 查询与该 image_id 相同的所有记录，按 id 排序
        cursor.execute("""
            SELECT id
            FROM image_analysis
            WHERE image_id = %s
            ORDER BY id
        """, (image_id,))
        records = cursor.fetchall()

        # 确定当前数据的顺序（1-based index）
        ids = [record['id'] for record in records]
        new_position = ids.index(data_id) + 1  # 索引加1得到顺序

        return new_position
    finally:
        cursor.close()
        conn.close()

def get_ratio(image_id, position):
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # 查询 count 值
        cursor.execute("""
            SELECT data_count FROM image_data WHERE id = %s
        """, (image_id,))
        count_result = cursor.fetchone()
        if not count_result:
            return {"error": "Invalid image_id or no data found."}, 404
        count = count_result[0]

        ratio = f"({position}/{count})"
        return ratio

    except Exception as e:
        return {"error": str(e)}, 500
    finally:
        cursor.close()
        conn.close()

def get_next_unlabeled_image(current_user_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    last_image_id = None  

    while True:
        # 查询下一个未标记的图像，避免重复
        query = """
            SELECT * FROM image_data 
            WHERE status = 'unlabeled'
        """
        if last_image_id is not None:
            query += " AND id > %s"  

        query += " ORDER BY id ASC LIMIT 1"

        cursor.execute(query, (last_image_id,) if last_image_id is not None else ())
        image_data = cursor.fetchone()

        if not image_data:
            cursor.close()
            conn.close()
            return None

        image_id = image_data['id']
        n = image_id // 11889
        k = image_id % 11889
        related_ids = []
        if n != 1:
            related_ids.append(1 * 11889 + k)
        if n != 2:
            related_ids.append(2 * 11889 + k)
        if n != 3:
            related_ids.append(3 * 11889 + k)

        if related_ids:  
            placeholders = ', '.join(['%s'] * len(related_ids))
            cursor.execute(f"""
                SELECT user_id FROM image_data 
                WHERE id IN ({placeholders})
            """, related_ids)
            user_ids = cursor.fetchall()

            # 检查 user_id 是否与当前用户相同
            if all(user_id['user_id'] != current_user_id for user_id in user_ids):
                last_image_id = image_id  
                cursor.close()
                conn.close()
                return image_data
        
        last_image_id = image_id


# if __name__ == '__main__':
#     data = get_next_unlabeled_image(23)
#     print(data['id'])