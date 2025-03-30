# 使用官方Python镜像
FROM python:3.9-slim

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    wget \
    unzip \
    hmmer \
    clustalw \
    && rm -rf /var/lib/apt/lists/*

# 安装seqkit
RUN wget https://github.com/shenwei356/seqkit/releases/download/v2.6.0/seqkit_linux_amd64.tar.gz \
    && tar -zxvf seqkit_linux_amd64.tar.gz \
    && mv seqkit /usr/local/bin/ \
    && chmod +x /usr/local/bin/seqkit \
    && rm seqkit_linux_amd64.tar.gz

# 设置工作目录
WORKDIR /streamlit_app

# 复制Python依赖文件
COPY requirements.txt .

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制所有代码
COPY . .

# 暴露端口
EXPOSE 8501

# 启动命令
CMD ["streamlit", "run", "streamlit_app.py", "--server.port=8501", "--server.address=0.0.0.0"]
