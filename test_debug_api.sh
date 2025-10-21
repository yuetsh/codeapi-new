u#!/bin/bash

# 测试 debug API 的脚本

BASE_URL="http://localhost:8080"

echo "开始测试 debug API..."
echo "API 地址: $BASE_URL"

# 等待服务器启动
echo "等待服务器启动..."
sleep 3

echo ""
echo "=== 测试简单 Python 代码执行 ==="

curl -X POST "$BASE_URL/debug" \
  -H "Content-Type: application/json" \
  -d '{
    "user_script": "x = 5\ny = 10\nz = x + y\nprint(f\"x = {x}, y = {y}, z = {z}\")",
    "raw_input_json": null
  }' \
  -w "\n状态码: %{http_code}\n" \
  -s

echo ""
echo "=== 测试带输入的 Python 代码 ==="

curl -X POST "$BASE_URL/debug" \
  -H "Content-Type: application/json" \
  -d '{
    "user_script": "name = input(\"请输入您的姓名: \")\nage = int(input(\"请输入您的年龄: \"))\nprint(f\"您好 {name}，您今年 {age} 岁\")",
    "raw_input_json": ["张三", "25"]
  }' \
  -w "\n状态码: %{http_code}\n" \
  -s

echo ""
echo "=== 测试带循环的 Python 代码 ==="

curl -X POST "$BASE_URL/debug" \
  -H "Content-Type: application/json" \
  -d '{
    "user_script": "numbers = [1, 2, 3, 4, 5]\ntotal = 0\nfor num in numbers:\n    total += num\n    print(f\"当前数字: {num}, 累计: {total}\")\nprint(f\"最终结果: {total}\")",
    "raw_input_json": null
  }' \
  -w "\n状态码: %{http_code}\n" \
  -s

echo ""
echo "=== 测试有错误的 Python 代码 ==="

curl -X POST "$BASE_URL/debug" \
  -H "Content-Type: application/json" \
  -d '{
    "user_script": "x = 10\ny = 0\nresult = x / y\nprint(f\"结果: {result}\")",
    "raw_input_json": null
  }' \
  -w "\n状态码: %{http_code}\n" \
  -s

echo ""
echo "=== 测试 Python 函数 ==="

curl -X POST "$BASE_URL/debug" \
  -H "Content-Type: application/json" \
  -d '{
    "user_script": "def fibonacci(n):\n    if n <= 1:\n        return n\n    return fibonacci(n-1) + fibonacci(n-2)\n\nresult = fibonacci(5)\nprint(f\"斐波那契数列第5项: {result}\")",
    "raw_input_json": null
  }' \
  -w "\n状态码: %{http_code}\n" \
  -s

echo ""
echo "所有测试完成!"
