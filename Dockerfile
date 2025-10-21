# 使用 Python 3.12 官方镜像作为基础镜像
FROM python:3.12-slim

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# 配置中科大镜像源
# 配置 apt 镜像源
RUN sed -i 's/deb.debian.org/mirrors.ustc.edu.cn/g' /etc/apt/sources.list.d/debian.sources && \
    sed -i 's/security.debian.org/mirrors.ustc.edu.cn/g' /etc/apt/sources.list.d/debian.sources

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# 复制项目文件
COPY pyproject.toml ./
COPY uv.lock ./

# 安装 uv 包管理器（使用中科大 PyPI 镜像）
RUN pip install -i https://pypi.mirrors.ustc.edu.cn/simple/ uv

# 配置中科大 PyPI 镜像源
RUN uv config set global.index-url https://pypi.mirrors.ustc.edu.cn/simple/

# 使用 uv 安装 Python 依赖
RUN uv sync --frozen

# 复制应用代码
COPY . .

# 暴露端口
EXPOSE 8080

# 设置启动命令
CMD ["uv", "run", "python", "main.py"]
