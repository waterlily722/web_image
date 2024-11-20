# 使用官方 Python 镜像作为基础镜像
FROM python:3.8.10

# 安装 Flask 和依赖
# RUN pip install --upgrade Flask Werkzeug

# 设置工作目录
WORKDIR /app

# 复制本地的 Flask 应用程序代码到容器中
COPY . /app

# 安装 Flask 应用程序所需的 Python 包
RUN pip install --no-cache-dir -r requirements.txt

# 暴露 Flask 应用程序运行的端口
EXPOSE 5000

# 运行 Flask 应用程序
CMD ["python", "run.py"]