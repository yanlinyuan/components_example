# 使用官方Python基础镜像
FROM python:3.9-slim

# 安装系统依赖和生物信息学工具
RUN apt-get update && apt-get install -y \
    wget \
    unzip \
    hmmer \          # 包含hmmsearch
    clustalw \       # 多序列比对工具
    && rm -rf /var/lib/apt/lists/*

# 安装seqkit（Go编译的二进制工具）
RUN wget https://github.com/shenwei356/seqkit/releases/download/v2.3.0/seqkit_linux_amd64.tar.gz \
    && tar -zxvf seqkit_linux_amd64.tar.gz \
    && mv seqkit /usr/local/bin/ \
    && rm seqkit_linux_amd64.tar.gz

# 设置工作目录
WORKDIR /streamlit_app

# 复制Python依赖文件
COPY requirements.txt .

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY . .

# 设置启动命令
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
