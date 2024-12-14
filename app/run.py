import argparse
import mysql.connector
from werkzeug.security import check_password_hash as checkpw
from flask import Flask, request, render_template, redirect, url_for, session, flash, abort, make_response
from bcrypt import checkpw
from web_env.get_data import get_image_data, get_user_data
from web_env.data_tool import get_previous_image_id, get_next_image_id, get_mal_type_options, get_new_position, get_ratio, get_next_unlabeled_image

# 参数解析
parser = argparse.ArgumentParser(description='Flask Application')
parser.add_argument("--server-port", type=int, default=5000, help="Demo server port.")
args = parser.parse_args()

app = Flask(__name__, template_folder='./templates/')
app.secret_key = 'secret_key'

# 配置MySQL数据库连接
def get_db_connection():
    conn = mysql.connector.connect(
        host='121.40.127.186',
        user='root',
        password='llm_image',
        database='llm_image',
        charset="utf8mb4"
    )
    return conn

def verify_password(plain_password, hashed_password):
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

# 登录路由
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # 从表单获取数据
        username = request.form.get('username')
        password = request.form.get('password')
        user = get_user_data(username)
        # conn = get_db_connection()
        # cursor = conn.cursor(dictionary=True)

        # # 查询用户信息
        # cursor.execute("SELECT * FROM user WHERE username = %s", (username,))
        # user = cursor.fetchone()
        # cursor.close()
        # conn.close()

        if user and checkpw(password.encode('utf-8'), user['password'].encode('utf-8')):
            # 将用户信息存储到会话中
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['image_id'] = user['image_id']
            session['current_analysis_id'] = user['current_analysis_id']
            session['position'] = user['position']

            resp = make_response(redirect(url_for('index')))
            resp.set_cookie('access_token', str(user['id']), max_age=3600, httponly=True, secure=False)  
            return resp

            flash('登录成功！', 'success')
        else:
            flash('用户名或密码错误！', 'danger')
    return render_template('login.html')  

# 退出登录
@app.route('/logout')
def logout():
    # 清除会话
    session.clear()
    
    # 清除 Cookie
    resp = make_response(redirect(url_for('login')))
    resp.set_cookie('access_token', '', expires=0)  

    flash('您已成功退出登录!', 'info')
    return resp

# 分发影像
@app.route('/dispatch')
def dispatch():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT current_analysis_id FROM user WHERE id = %s", (session['user_id'],))
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    return render_template('dispatch.html', data_id = result['current_analysis_id'], user_data=get_user_data(session['username']))

@app.route('/dispatch_image', methods=['POST'])    
def dispatch_image():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            UPDATE image_data 
            SET status = %s
            WHERE id = %s
        """, ('labeled', session['image_id']))
        conn.commit()
    except Exception as e:
        conn.rollback()
        print(f"Error: {e}")
    finally:
        cursor.close()
        conn.close()
    session['current_analysis_id'] = None
    return redirect(url_for('index'))
    
# 登录状态保护机制
@app.before_request
def require_login():
    allowed_routes = ['login', 'static']
    if request.endpoint not in allowed_routes and 'user_id' not in session:
        flash('请先登录！', 'warning')
        return redirect(url_for('login'))

@app.context_processor
def inject_functions():
    return {'get_mal_type_options': get_mal_type_options, 'get_ratio':get_ratio}

# 主页
@app.route('/')
def index():
    if 'user_id' in session:
        user_id = session['user_id']

        if not session['current_analysis_id']:
            image_data = get_next_unlabeled_image(user_id)
            
            if image_data:
                image_id = image_data['id']

                # 查询第一个 image_analysis 数据
                conn = get_db_connection()
                cursor = conn.cursor(dictionary=True)
                cursor.execute("""
                    SELECT * FROM image_analysis 
                    WHERE image_id = %s 
                    ORDER BY id ASC 
                    LIMIT 1
                """, (image_id,))
                image_analysis = cursor.fetchone()
                cursor.close()
                conn.close()

                if image_analysis:
                    current_analysis_id = image_analysis['id']

                    conn = get_db_connection()
                    cursor = conn.cursor(dictionary=True)

                    try:
                        # 更新用户的影像信息
                        cursor.execute("""
                            UPDATE user 
                            SET image_id = %s, current_analysis_id = %s, position = %s
                            WHERE id = %s;
                        """, (image_id, current_analysis_id, 1, session['user_id']))
                        
                        # 更新影像的状态
                        cursor.execute("""
                            UPDATE image_data 
                            SET status = %s, user_id = %s
                            WHERE id = %s;
                        """, ('labeling', session['user_id'], image_id))

                        cursor.execute("""
                            UPDATE image_analysis
                            SET status = %s
                            WHERE id = %s
                            """, ('labeling', current_analysis_id))
                        
                        conn.commit()
                    except Exception as e:
                        conn.rollback()
                        print(f"Error: {e}")
                    finally:
                        cursor.close()
                        conn.close()

                    session['image_id'] = image_id
                    session['current_analysis_id'] = current_analysis_id
                    session['position'] = 1
                else:
                    abort(404, description="未找到影像！")
            else:
                abort(404, description="校对完成，暂无可分配影像！")

        if session['current_analysis_id']:
            # conn = get_db_connection()
            # cursor = conn.cursor(dictionary=True)
            # try:
            #     cursor.execute("SELECT current_analysis_id FROM user WHERE id = %s", (session['user_id'],))
            user_data = get_user_data(session['username'])
            current_analysis_id = user_data['current_analysis_id']
            # except Exception as e:
            #     print(f"Database error: {e}")
            # finally:
            #     cursor.close()
            #     conn.close()

            image_data = get_image_data(current_analysis_id)

            if image_data:
                session['image_id'] = image_data.get('image_id')
                session['position'] = get_new_position(current_analysis_id, session['image_id'])
                image_path = image_data.get('image_path')
                return render_template('index.html', image_data=image_data, user_data=get_user_data(session['username']), image_path=image_path)
            else:
                abort(404, description="未找到影像！")
        else:
            abort(404, description="未分配影像数据！")
        
    return redirect(url_for('login'))        

# 切换到下一张或上一张图片
@app.route('/images/<int:data_id>')
def image(data_id):
    if data_id:
        user_data = get_user_data(session['username'])
        # conn = get_db_connection()
        # cursor = conn.cursor(dictionary=True)
        # try:
            # cursor.execute("SELECT current_analysis_id FROM user WHERE id = %s", (session['user_id'],))
            # user_data = cursor.fetchone()
        current_analysis_id = user_data['current_analysis_id']
        if data_id not in {current_analysis_id, current_analysis_id + 1, current_analysis_id - 1}:
            flash('您暂无权限访问！', 'danger')
            return redirect(url_for('index'))
        # except Exception as e:
        #     print(f"Database error: {e}")
        # finally:
        #     cursor.close()
        #     conn.close()

        image_data = get_image_data(data_id)

        if image_data['image_id'] == session['image_id']:
            # 如果能找到对应的图片数据
            if image_data:
                image_path = image_data['image_path']  
                
                # 更新 position 和 current_analysis_id
                new_position = get_new_position(data_id, image_data['image_id'])
                session['position'] = new_position
                session['current_analysis_id'] = data_id

                conn = get_db_connection()
                cursor = conn.cursor(dictionary=True)
                try:
                    cursor.execute("""
                                    UPDATE image_analysis
                                    SET status = %s
                                    WHERE id = %s
                                    """, ('labeling', data_id))
                    cursor.execute("""
                                    UPDATE user 
                                    SET current_analysis_id = %s, position = %s
                                    WHERE id = %s
                                """, (data_id, new_position, session['user_id']))
                    conn.commit()
                except Exception as e:
                    conn.rollback()
                    print(f"Error: {e}")
                finally:
                    cursor.close()
                    conn.close()
                
                # print(session)
                return render_template('index.html', image_data=image_data, user_data=get_user_data(session['username']), image_path=image_path)
            else:
                abort(404, description="未找到影像！")

        elif int(image_data['image_id']) > int(session['image_id']):
            return redirect(url_for('dispatch'))

        else:
            abort(404, description="您的访问已越界，请返回！")
    else:
        abort(404, description="未找到影像！")


# 更新推理和答案，并跳转到上一张图片
@app.route('/update_previous', methods=['POST'])
def update_previous():
    # new_question = request.form['question']
    # new_rationale = request.form['rationale']
    new_answer = request.form.getlist('answer')  # 获取所有选中的答案（复选框）
    if new_answer:
        new_answer = ','.join(new_answer)  # 将选中的答案列表转换为逗号分隔的字符串
    else:
        new_answer = request.form['answer']  # 对于单选，只获取一个值
    image_id = request.form['image_id']
    confidence_level = request.form['confidence_level']

    # 更新数据库中的推理和答案
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            UPDATE image_analysis
            SET updated_answer = %s, status = 'labeled', confidence_level = %s
            WHERE id = %s
        """, (new_answer, confidence_level, image_id))
        conn.commit()
    except Exception as e:
        conn.rollback()
        print(f"Error: {e}")
    finally:
        cursor.close()
        conn.close()

    previous_image_id = get_previous_image_id(image_id)

    if previous_image_id:
        return redirect(url_for('image', data_id=previous_image_id))
    else:
        # 如果没有上一张图片，返回 404
        abort(404, description="您的访问已越界，请返回！")


# 修改推理和答案，并跳转到下一张图片
@app.route('/update_next', methods=['POST'])
def update_next():
    # new_question = request.form['question']
    # new_rationale = request.form['rationale']
    new_answer = request.form.getlist('answer')  # 获取所有选中的答案（复选框）
    if new_answer:
        new_answer = ','.join(new_answer)  # 将选中的答案列表转换为逗号分隔的字符串
    else:
        new_answer = request.form['answer']  # 对于单选，只获取一个值
    image_id = request.form['image_id']
    confidence_level = request.form['confidence_level']

    # 更新数据库中的推理和答案
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            UPDATE image_analysis
            SET updated_answer = %s, status = 'labeled', confidence_level = %s
            WHERE id = %s
        """, (new_answer, confidence_level, image_id))
        conn.commit()
    except Exception as e:
        conn.rollback()
        print(f"Error: {e}")
    finally:
        cursor.close()
        conn.close()

    # 获取下一张图片 ID
    next_image_id = get_next_image_id(image_id)

    if next_image_id:
        return redirect(url_for('image', data_id=next_image_id))
    else:
        return redirect(url_for('dispatch'))


# 捕获404错误并返回自定义信息
@app.errorhandler(404)
def page_not_found(e):
    referer_url = request.referrer
    return render_template('404.html', error_message=e.description, referer_url=referer_url), 404

@app.before_request
def check_access_token():
    if request.path == url_for('login'):
        return 
    access_token = request.cookies.get('access_token')  # 从 Cookie 中获取令牌
    if not access_token:
        flash('请先登录！', 'warning')
        return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=args.server_port, debug=True)
