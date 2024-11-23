import mysql.connector
import json
from itertools import groupby

malocclusion = ['安氏分类', '骨性分类', '错合类型', '拥挤', '牙列间隙', '深覆合', '深覆盖', '开合', '牙前突', '上颌前突', '上颌发育不足', 
                '下颌前突', '下颌后缩', '前牙反合', '后牙锁合', '后牙反合', '中线', '矢状关系', '面型']
disease = ['龋坏', '牙齿扭转', '色素沉着', '牙周病', '楔状缺损', '脱钙', '软垢', '牙列拥挤', '牙颜色异常', '牙列间隙', '牙磨损', 
           '阻生牙', '修复冠', '根管填充', '填充物', '连接桥', '根尖周炎', '残根', '骨岛', '种植体', '埋伏牙', '残冠', '贴面', 
           '囊肿', '乳牙萌出空间不足', '预判阻生', '牙结石', '全部']

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
    

# 创建数据表
def create_table():
    conn = get_db_connection()
    cursor = conn.cursor()

    create_table_query = """
    CREATE TABLE IF NOT EXISTS image_analysis (
        id INT AUTO_INCREMENT PRIMARY KEY,           -- 自增主键
        original_id VARCHAR(255),                   
        image_id INT,
        image_path VARCHAR(255),                      -- 图片路径
        question TEXT,                               -- 问题
        rationale TEXT,                              -- 推理
        answer VARCHAR(255),                         -- 答案
        type VARCHAR(255),                           -- 关键词
        updated_question TEXT,                       -- 修改后的问题
        updated_rationale TEXT,                      -- 修改后的推理
        updated_answer VARCHAR(255),                 -- 修改后的答案
        status ENUM('unlabeled', 'labeling', 'labeled') DEFAULT 'unlabeled',  -- 状态
        FOREIGN KEY (image_id) REFERENCES image_data(id) ON DELETE CASCADE  -- 关联 image_data 表
    ) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
    """
    cursor.execute(create_table_query)  
    conn.commit()  
    conn.close()   

# 读取数据
def load_data_from_json(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        data = json.load(file)
    return data

# 提取 type 字段
def extract_type_from_id(id):
    return str(id).split('_')[-1]

def sort_data_by_image_group(data, malocclusion, disease):
    """
    对数据按照 image 进行分组，并根据 malocclusion 或 disease 列表顺序进行排序。
    """
    # 创建用于存储分组数据的字典
    image_groups = {}

    # 分组数据
    for item in data:
        item_id = item['id']
        image = "_".join(item_id.split("_")[1:3])  # 提取 image 部分
        category = item_id.split("_")[0]  # 提取类型（mal 或 dis）

        # 初始化该 image 组
        if image not in image_groups:
            image_groups[image] = {'type': category, 'items': []}

        # 检查类型是否一致
        if image_groups[image]['type'] != category:
            raise ValueError(f"Image group {image} has inconsistent categories (mal and dis).")

        # 将数据添加到对应的组
        image_groups[image]['items'].append(item)

    # 定义排序函数
    def get_sort_order(item, malocclusion, disease):
        """
        根据 item 的类别决定排序顺序。
        """
        item_id = item['id']
        category = item_id.split("_")[3]  # 提取类别

        # 判断类别在 malocclusion 或 disease 列表中的位置
        if category in malocclusion:
            return malocclusion.index(category)
        elif category in disease:
            return disease.index(category)
        else:
            return float('inf')  # 如果类别不在列表中，返回最大值（排序最后）

    # 对每个 image 组内的数据进行排序
    for image, group in image_groups.items():
        category_type = group['type']
        items = group['items']

        # 根据类型选择排序列表
        if category_type == 'mal':
            items.sort(key=lambda item: get_sort_order(item, malocclusion, disease))
        elif category_type == 'dis':
            items.sort(key=lambda item: get_sort_order(item, malocclusion, disease))

        # # 打印分组和排序结果
        # print(f"\nImage Group: {image}")
        # print(f"  Category Type: {category_type}")
        # print(f"  Sorted Items: {[item['id'] for item in items]}")

    # 返回排序后的分组数据
    return image_groups


def get_image_id_mapping():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, image FROM image_data")
    
    # 创建字典
    image_id_map = {image: image_id for image_id, image in cursor.fetchall()}
    conn.close()
    return image_id_map


# 将数据插入数据库
def insert_data_into_db(data):
    conn = get_db_connection()
    cursor = conn.cursor()

    # sorted_data = sort_data_by_image_group(data, malocclusion, disease)
    # image_id_map = get_image_id_mapping()

    # 插入数据
    for record in data: 
        original_id = record['original_id']
        # image = "_".join(original_id.split("_")[1:3])
        # image_id = image_id_map.get(image, None)  
            
        # if image_id is None:
        #     print(f"Warning: Image path {image} not found in image_data table.")
        #     continue  
        image_id = record['image_id']
        image_path = record['image_path']
        question = record['question']
        rationale = record['rationale']
        answer = record['answer']
        type_field = record['type']
        updated_question = record['question']
        updated_rationale = record['rationale']
        updated_answer = record['answer']

        insert_query = """
        INSERT INTO image_analysis (original_id, image_id, image_path, question, rationale, answer, type, updated_question, updated_rationale, updated_answer, status)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(insert_query, (original_id, image_id, image_path, question, rationale, answer, type_field, updated_question, updated_rationale, updated_answer, 'unlabeled'))
            
    conn.commit()  
    conn.close()   

def export_data(path):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    query = "SELECT * FROM image_analysis"
    cursor.execute(query)
    
    with open(path, 'w', encoding='utf-8') as f:
        f.write('[')  
        first = True
        
        for row in cursor:
            if not first:
                f.write(',\n')  
            else:
                first = False
            
            f.write(json.dumps(row, ensure_ascii=False, default=str))
        
        f.write(']')  

# def add_columns_to_table():
#     conn = get_db_connection()
#     cursor = conn.cursor()

#     try:
#         # 使用 ALTER TABLE 来添加修改后的推理和答案列
#         alter_table_query = """
#         ALTER TABLE image_analysis
#         ADD COLUMN updated_rationale TEXT DEFAULT NULL,  -- 添加修改后的推理
#         ADD COLUMN updated_answer VARCHAR(255) DEFAULT NULL; -- 添加修改后的答案
#         """
        
#         cursor.execute(alter_table_query)  # 执行修改表结构的查询
#         conn.commit()  
#     except mysql.connector.Error as err:
#         print(f"Error: {err}")
#     finally:
#         conn.close()  

def backup_data_as_json(data, output_file):
    sorted_data = sort_data_by_image_group(data, malocclusion, disease)
    image_id_map = get_image_id_mapping()

    backup_list = []
    for image, group_data in sorted_data.items():
        for record in group_data['items']:
            original_id = record['id']
            image = "_".join(original_id.split("_")[1:3])
            image_id = image_id_map.get(image, None)

            if image_id is None:
                print(f"Warning: Image path {image} not found in image_data table.")
                continue  

            image_path = record['image_path']
            question = record['question']
            rationale = record['rationale']
            answer = record['answer']
            # type_field = extract_type_from_id(record['id'])
            type_field = record['type']

            # 按数据库格式创建备份条目
            backup_record = {
                "original_id": original_id,
                "image_id": image_id,
                "image_path": image_path,
                "question": question,
                "rationale": rationale,
                "answer": answer,
                "type": type_field,
                # "updated_question": question,  # 初始值与原始数据相同
                # "updated_rationale": rationale,
                # "updated_answer": answer,
                "status": "unlabeled"  # 默认状态
            }
            backup_list.append(backup_record)

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(backup_list, f, ensure_ascii=False, indent=4)
    print(f"Backup successfully saved to {output_file}")


if __name__ == '__main__':
    # create_table()  
    json_data = load_data_from_json('/home/web_image/sampled_data/image_analysis_update.json')  
    # backup_data_as_json(json_data, '/home/web_image/sampled_data/image_analysis_update.json')
    insert_data_into_db(json_data)  
    # export_data('/home/web_image/sample/output.json')


# ALTER TABLE image_analysis
# ADD COLUMN start_time DATETIME DEFAULT NULL,
# ADD COLUMN end_time DATETIME DEFAULT NULL,
# ADD COLUMN time_diff INT DEFAULT 0,  
# ADD COLUMN label_count INT DEFAULT 0; 

# DELIMITER $$

# -- 在状态变为 labeling 时，设置 start_time
# CREATE TRIGGER before_status_labeling
# BEFORE UPDATE ON image_analysis
# FOR EACH ROW
# BEGIN
#     IF NEW.status = 'labeling' AND OLD.status != 'labeling' THEN
#         SET NEW.start_time = NOW();
#     END IF;
# END$$

# CREATE TRIGGER before_status_labeled
# BEFORE UPDATE ON image_analysis
# FOR EACH ROW
# BEGIN
#     IF NEW.status = 'labeled' AND OLD.status != 'labeled' THEN
#         SET NEW.end_time = NOW();
#         -- 检查 start_time 是否设置且与当前时间间隔大于 3 秒
#         IF NEW.start_time IS NOT NULL AND TIMESTAMPDIFF(SECOND, NEW.start_time, NEW.end_time) > 3 THEN
#             -- 累积时间差
#             SET NEW.time_diff = TIMESTAMPDIFF(SECOND, NEW.start_time, NEW.end_time) + OLD.time_diff;
#             -- 增加标注次数
#             SET NEW.label_count = OLD.label_count + 1;
#         END IF;
#     END IF;
# END$$

# DELIMITER ;
