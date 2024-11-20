def init_user(session['user']):
    # 如果 current_analysis_id 为空
        if not user['current_analysis_id']:
            cursor.execute("""
                SELECT * FROM image_data 
                WHERE status = 'unlabeled' 
                ORDER BY id ASC 
                LIMIT 1
            """)
            image_data = cursor.fetchone()

            if image_data:
                image_id = image_data['id']

                # 查询第一个 image_analysis 数据
                cursor.execute("""
                    SELECT * FROM image_analysis 
                    WHERE image_id = %s 
                    ORDER BY id ASC 
                    LIMIT 1
                """, (image_id,))
                image_analysis = cursor.fetchone()

                if image_analysis:
                    current_analysis_id = image_analysis['id']

                    # 更新用户表
                    cursor.execute("""
                        UPDATE user 
                        SET image_id = %s, current_analysis_id = %s, position = %s
                        WHERE id = %s
                    """, (image_id, current_analysis_id, 1, user['id']))
                    conn.commit()

                    # 更新用户对象
                    user['image_id'] = image_id
                    user['current_analysis_id'] = current_analysis_id
                    user['position'] = 1

        conn.close()

        # 将用户信息存储到会话中
        session['user'] = user