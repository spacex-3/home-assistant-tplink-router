FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# 复制requirements文件并安装Python依赖
COPY tplink-device-manager/backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY tplink-device-manager/backend/ ./

# 复制前端模板文件
COPY tplink-device-manager/backend/templates/ ./templates/

# 暴露端口
EXPOSE 8080

# 设置环境变量
ENV FLASK_APP=app.py
ENV FLASK_ENV=production

# 运行应用
CMD ["python", "app.py"]