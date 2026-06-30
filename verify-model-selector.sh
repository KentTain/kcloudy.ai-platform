#!/bin/bash
# ModelSelector 功能验证脚本
# 自动检测环境并运行测试

set -e

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$SCRIPT_DIR"

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}==================================="
echo "ModelSelector 组件功能验证"
echo -e "===================================${NC}"
echo ""

# 测试结果统计
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

# 1. 检查环境
check_environment() {
    echo -e "${YELLOW}[1/4] 检查环境...${NC}"

    # 检查 Python
    if command -v python3 &> /dev/null; then
        echo -e "  ${GREEN}✓ Python 可用${NC}"
    else
        echo -e "  ${RED}✗ Python 未安装${NC}"
        exit 1
    fi

    # 检查 uv
    if command -v uv &> /dev/null; then
        echo -e "  ${GREEN}✓ uv 可用${NC}"
    else
        echo -e "  ${RED}✗ uv 未安装${NC}"
        exit 1
    fi

    # 检查 pnpm
    if command -v pnpm &> /dev/null; then
        echo -e "  ${GREEN}✓ pnpm 可用${NC}"
    else
        echo -e "  ${RED}✗ pnpm 未安装${NC}"
        exit 1
    fi

    # 检查前端依赖
    if [ -d "$PROJECT_ROOT/web/vue/node_modules" ]; then
        echo -e "  ${GREEN}✓ 前端依赖已安装${NC}"
    else
        echo -e "  ${YELLOW}⚠ 前端依赖未安装，正在安装...${NC}"
        cd "$PROJECT_ROOT/web/vue" && pnpm install
        echo -e "  ${GREEN}✓ 前端依赖安装完成${NC}"
    fi

    echo ""
}

# 2. 运行前端测试
run_frontend_tests() {
    echo -e "${YELLOW}[2/4] 运行前端测试...${NC}"
    echo ""

    cd "$PROJECT_ROOT/web/vue"

    # 运行 AiModelSelector 组件测试
    if pnpm test:unit tests/ai/unit/components/AiModelSelector.spec.ts --run 2>&1 | tee /tmp/frontend-test.log; then
        echo ""
        echo -e "${GREEN}✓ 前端测试通过${NC}"

        # 提取测试数量
        TEST_COUNT=$(grep -o "Tests  [0-9]* passed" /tmp/frontend-test.log | grep -o "[0-9]*" || echo "0")
        TOTAL_TESTS=$((TOTAL_TESTS + TEST_COUNT))
        PASSED_TESTS=$((PASSED_TESTS + TEST_COUNT))

        echo -e "  ${GREEN}✓ 通过 ${TEST_COUNT} 个测试用例${NC}"
    else
        echo ""
        echo -e "${RED}✗ 前端测试失败${NC}"
        FAILED_TESTS=$((FAILED_TESTS + 1))
    fi

    echo ""
}

# 3. 检查后端服务
check_backend_service() {
    echo -e "${YELLOW}[3/4] 检查后端服务...${NC}"

    if curl -s http://localhost:8080/health > /dev/null 2>&1; then
        echo -e "  ${GREEN}✓ 后端服务运行中 (http://localhost:8080)${NC}"
        BACKEND_RUNNING=true
    else
        echo -e "  ${YELLOW}⚠ 后端服务未运行${NC}"
        echo ""
        echo -e "  ${BLUE}启动后端服务的方法：${NC}"
        echo ""
        echo "  方式 1 - Docker Compose（推荐）："
        echo "    docker-compose up -d backend"
        echo ""
        echo "  方式 2 - 直接运行："
        echo "    cd server/python"
        echo "    uv run python manage.py runserver"
        echo ""
        echo -e "  ${YELLOW}提示：后端集成测试需要运行的服务器${NC}"
        BACKEND_RUNNING=false
    fi

    echo ""
}

# 4. 运行后端测试（如果服务可用）
run_backend_tests() {
    echo -e "${YELLOW}[4/4] 运行后端测试...${NC}"
    echo ""

    if [ "$BACKEND_RUNNING" = true ]; then
        cd "$PROJECT_ROOT/server/python"

        # 运行默认模型 API 测试
        if uv run pytest tests/ai/integration/test_default_model_api.py -v --tb=short 2>&1 | tee /tmp/backend-test.log; then
            echo ""
            echo -e "${GREEN}✓ 后端测试通过${NC}"

            # 提取测试数量
            PASSED=$(grep -o "[0-9]* passed" /tmp/backend-test.log | grep -o "[0-9]*" || echo "0")
            FAILED=$(grep -o "[0-9]* failed" /tmp/backend-test.log | grep -o "[0-9]*" || echo "0")

            TOTAL_TESTS=$((TOTAL_TESTS + PASSED + FAILED))
            PASSED_TESTS=$((PASSED_TESTS + PASSED))
            FAILED_TESTS=$((FAILED_TESTS + FAILED))

            echo -e "  ${GREEN}✓ 通过 ${PASSED} 个测试用例${NC}"
            if [ "$FAILED" -gt 0 ]; then
                echo -e "  ${RED}✗ 失败 ${FAILED} 个测试用例${NC}"
            fi
        else
            echo ""
            echo -e "${RED}✗ 后端测试失败${NC}"
            FAILED_TESTS=$((FAILED_TESTS + 1))
        fi

    else
        echo -e "${YELLOW}跳过后端测试（服务未运行）${NC}"
        echo ""
        echo -e "${BLUE}手动运行后端测试：${NC}"
        echo "  cd server/python"
        echo "  uv run pytest tests/ai/integration/test_default_model_api.py -v"
    fi

    echo ""
}

# 5. 生成测试报告
generate_report() {
    echo -e "${BLUE}==================================="
    echo "测试总结"
    echo -e "===================================${NC}"
    echo ""

    echo -e "${GREEN}通过测试：${PASSED_TESTS}${NC}"
    if [ "$FAILED_TESTS" -gt 0 ]; then
        echo -e "${RED}失败测试：${FAILED_TESTS}${NC}"
    fi
    echo -e "${BLUE}总测试数：${TOTAL_TESTS}${NC}"
    echo ""

    if [ "$FAILED_TESTS" -eq 0 ]; then
        echo -e "${GREEN}✅ 所有测试通过！${NC}"
        echo ""
        echo "后续步骤："
        echo "  1. 查看详细报告：$PROJECT_ROOT/test-results.md"
        echo "  2. 手动测试前端 UI：http://localhost:3000/ai"
        echo "  3. 验证模型选择功能"
    else
        echo -e "${YELLOW}⚠️  部分测试失败，请检查日志${NC}"
        echo ""
        echo "故障排查："
        echo "  1. 检查后端服务状态：curl http://localhost:8080/health"
        echo "  2. 查看后端日志：docker logs <container>"
        echo "  3. 查看详细测试报告：$PROJECT_ROOT/test-results.md"
    fi

    echo ""
    echo -e "${BLUE}===================================${NC}"
}

# 主流程
main() {
    check_environment
    run_frontend_tests
    check_backend_service
    run_backend_tests
    generate_report
}

# 运行主流程
main
