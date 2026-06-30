#!/bin/bash
# ModelSelector 组件测试运行脚本
# 用于验证前后端功能是否可用

set -e

echo "==================================="
echo "ModelSelector 组件测试"
echo "==================================="
echo ""

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检查 Docker 服务
check_docker() {
    echo -e "${YELLOW}检查 Docker 服务...${NC}"
    if ! docker ps &> /dev/null; then
        echo -e "${RED}错误: Docker 未运行或权限不足${NC}"
        exit 1
    fi
    echo -e "${GREEN}✓ Docker 服务正常${NC}"
    echo ""
}

# 检查后端服务
check_backend() {
    echo -e "${YELLOW}检查后端服务...${NC}"
    if curl -s http://localhost:8080/health > /dev/null; then
        echo -e "${GREEN}✓ 后端服务运行中 (http://localhost:8080)${NC}"
    else
        echo -e "${RED}错误: 后端服务未运行${NC}"
        echo "请先启动后端服务："
        echo "  cd server/python && uv run python manage.py runserver"
        exit 1
    fi
    echo ""
}

# 运行后端测试
run_backend_tests() {
    echo "==================================="
    echo "运行后端 API 集成测试"
    echo "==================================="
    echo ""

    cd server/python

    echo -e "${YELLOW}1. 运行默认模型 API 测试...${NC}"
    uv run pytest tests/ai/integration/test_default_model_api.py -v --tb=short

    if [ $? -eq 0 ]; then
        echo ""
        echo -e "${GREEN}✓ 后端测试通过${NC}"
    else
        echo ""
        echo -e "${RED}✗ 后端测试失败${NC}"
        exit 1
    fi

    cd ../..
    echo ""
}

# 运行前端测试
run_frontend_tests() {
    echo "==================================="
    echo "运行前端组件单元测试"
    echo "==================================="
    echo ""

    cd web/vue

    echo -e "${YELLOW}1. 检查依赖...${NC}"
    if [ ! -d "node_modules" ]; then
        echo "安装依赖..."
        pnpm install
    fi

    echo ""
    echo -e "${YELLOW}2. 运行 AiModelSelector 组件测试...${NC}"
    pnpm test:unit tests/ai/unit/components/AiModelSelector.spec.ts --run

    if [ $? -eq 0 ]; then
        echo ""
        echo -e "${GREEN}✓ 前端测试通过${NC}"
    else
        echo ""
        echo -e "${RED}✗ 前端测试失败${NC}"
        exit 1
    fi

    cd ../..
    echo ""
}

# 手动测试提示
show_manual_test_guide() {
    echo "==================================="
    echo "手动测试指南"
    echo "==================================="
    echo ""
    echo "后端 API 测试："
    echo ""
    echo "1. 获取模型列表："
    echo "   curl http://localhost:8080/ai/console/v1/models"
    echo ""
    echo "2. 设置默认模型："
    echo "   curl -X POST http://localhost:8080/ai/console/v1/plugins/default-models \\"
    echo "     -H 'Content-Type: application/json' \\"
    echo "     -d '{\"model_type\":\"llm\",\"plugin_id\":\"openai\",\"model_name\":\"gpt-4o-mini\"}'"
    echo ""
    echo "3. 获取默认模型："
    echo "   curl 'http://localhost:8080/ai/console/v1/plugins/default-models?model_type=llm'"
    echo ""
    echo "前端 UI 测试："
    echo ""
    echo "1. 访问 http://localhost:3000/ai"
    echo "2. 点击模型选择器，验证模型列表显示"
    echo "3. 选择模型，验证状态更新"
    echo "4. 刷新页面，验证模型选择保持"
    echo ""
}

# 生成测试报告
generate_report() {
    echo "==================================="
    echo "测试总结"
    echo "==================================="
    echo ""
    echo -e "${GREEN}所有自动化测试已通过！${NC}"
    echo ""
    echo "后续步骤："
    echo "1. 查看详细测试文档：docs/testing-model-selector.md"
    echo "2. 执行手动测试验证完整功能"
    echo "3. 检查前端 UI 是否正常显示"
    echo ""
}

# 主流程
main() {
    echo "开始测试..."
    echo ""

    # 检查环境
    check_docker
    check_backend

    # 运行测试
    run_backend_tests
    run_frontend_tests

    # 显示手动测试指南
    show_manual_test_guide

    # 生成报告
    generate_report
}

# 运行主流程
main
