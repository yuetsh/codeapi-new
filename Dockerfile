# 使用 Python 3.12 官方镜像作为基础镜像
FROM python:3.12-slim

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PIP_NO_CACHE_DIR=1
ENV PIP_INDEX_URL=https://pypi.mirrors.ustc.edu.cn/simple/

# 复制依赖文件
COPY requirements.txt ./

# 安装依赖（使用中科大 PyPI 镜像）
# clang-format 使用 PyPI 的二进制 wheel，避免 apt 拉取 LLVM 全家桶；
# 所有依赖都有预编译 wheel，不需要 gcc
RUN pip install -r requirements.txt clang-format

# 复制应用代码
COPY . .

# 暴露端口
EXPOSE 8080

# 设置启动命令
CMD ["python", "main.py"]
