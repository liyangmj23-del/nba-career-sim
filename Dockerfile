FROM python:3.11-slim

WORKDIR /app

# 安装依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制全部代码
COPY . .

# 确保数据目录存在
RUN mkdir -p data seeding/seed_cache

# HF Spaces 要求端口 7860
ENV PORT=7860
EXPOSE 7860

# 启动脚本：初始化数据库，启动服务器
CMD ["python", "hf_app.py"]
