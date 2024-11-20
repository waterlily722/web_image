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

def get_image_data(image_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM image_analysis WHERE id = %s", (image_id,))
    image_data = cursor.fetchone()
    conn.close()
    return image_data