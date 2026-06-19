"""
响应格式专项测试

验证 Success 和 SuccessExtra 响应类的正确性。
"""

import json

from framework.schemas.base import Fail, Success, SuccessExtra


class TestSuccessResponse:
    """Success 响应测试"""

    def test_default_values(self):
        """测试默认值"""
        response = Success()

        assert response.status_code == 200

        content = json.loads(response.body.decode("utf-8"))
        assert content["code"] == 200
        assert content["msg"] == "OK"
        assert content["data"] is None

    def test_custom_msg(self):
        """测试自定义 msg"""
        response = Success(msg="操作成功")

        content = json.loads(response.body.decode("utf-8"))
        assert content["msg"] == "操作成功"

    def test_with_data(self):
        """测试带 data"""
        response = Success(data={"id": "123", "name": "test"})

        content = json.loads(response.body.decode("utf-8"))
        assert content["data"]["id"] == "123"
        assert content["data"]["name"] == "test"

    def test_with_list_data(self):
        """测试列表 data"""
        response = Success(data=[{"id": "1"}, {"id": "2"}])

        content = json.loads(response.body.decode("utf-8"))
        assert isinstance(content["data"], list)
        assert len(content["data"]) == 2

    def test_with_extra_fields(self):
        """测试额外字段通过 kwargs 扩展"""
        response = Success(
            data={"message": "hello"},
            conversation_id="conv-123",
            has_more=True,
        )

        content = json.loads(response.body.decode("utf-8"))
        assert content["conversation_id"] == "conv-123"
        assert content["has_more"] is True

    def test_custom_code(self):
        """测试自定义状态码"""
        response = Success(code=201, msg="创建成功", data={"id": "new"})

        assert response.status_code == 201
        content = json.loads(response.body.decode("utf-8"))
        assert content["code"] == 201
        assert content["msg"] == "创建成功"

    def test_null_data(self):
        """测试 data 为 null"""
        response = Success(data=None)

        content = json.loads(response.body.decode("utf-8"))
        assert content["data"] is None

    def test_empty_string_msg(self):
        """测试空字符串 msg"""
        response = Success(msg="")

        content = json.loads(response.body.decode("utf-8"))
        assert content["msg"] == ""

    def test_none_msg(self):
        """测试 msg 为 None"""
        response = Success(msg=None)

        content = json.loads(response.body.decode("utf-8"))
        assert content["msg"] is None


class TestSuccessExtraResponse:
    """SuccessExtra 分页响应测试"""

    def test_default_values(self):
        """测试默认值"""
        response = SuccessExtra()

        assert response.status_code == 200

        content = json.loads(response.body.decode("utf-8"))
        assert content["code"] == 200
        assert content["msg"] is None  # SuccessExtra 默认 msg=None
        assert content["data"] is None
        assert content["total"] == 0
        assert content["page"] == 1
        assert content["page_size"] == 20

    def test_pagination_fields(self):
        """测试分页字段"""
        response = SuccessExtra(
            data=[{"id": "1"}, {"id": "2"}],
            total=100,
            page=2,
            page_size=10,
        )

        content = json.loads(response.body.decode("utf-8"))
        assert content["total"] == 100
        assert content["page"] == 2
        assert content["page_size"] == 10
        assert len(content["data"]) == 2

    def test_custom_msg(self):
        """测试自定义 msg"""
        response = SuccessExtra(
            data=[],
            total=0,
            msg="查询成功",
        )

        content = json.loads(response.body.decode("utf-8"))
        assert content["msg"] == "查询成功"

    def test_with_extra_fields(self):
        """测试额外字段"""
        response = SuccessExtra(
            data=[],
            total=100,
            extra_field="extra_value",
        )

        content = json.loads(response.body.decode("utf-8"))
        assert content["extra_field"] == "extra_value"

    def test_empty_data_list(self):
        """测试空数据列表"""
        response = SuccessExtra(data=[], total=0, page=1, page_size=20)

        content = json.loads(response.body.decode("utf-8"))
        assert content["data"] == []
        assert content["total"] == 0

    def test_large_dataset(self):
        """测试大数据集"""
        large_data = [{"id": str(i)} for i in range(1000)]
        response = SuccessExtra(
            data=large_data,
            total=10000,
            page=1,
            page_size=1000,
        )

        content = json.loads(response.body.decode("utf-8"))
        assert len(content["data"]) == 1000
        assert content["total"] == 10000

    def test_pagination_boundary_values(self):
        """测试分页边界值"""
        # 第一页
        response = SuccessExtra(data=[], total=100, page=1, page_size=20)
        content = json.loads(response.body.decode("utf-8"))
        assert content["page"] == 1

        # 最后一页
        response = SuccessExtra(data=[], total=100, page=5, page_size=20)
        content = json.loads(response.body.decode("utf-8"))
        assert content["page"] == 5

        # 大页码
        response = SuccessExtra(data=[], total=1000, page=100, page_size=10)
        content = json.loads(response.body.decode("utf-8"))
        assert content["page"] == 100


class TestFailResponse:
    """Fail 响应测试"""

    def test_default_values(self):
        """测试默认值"""
        response = Fail()

        assert response.status_code == 400

        content = json.loads(response.body.decode("utf-8"))
        assert content["code"] == 400
        assert content["msg"] is None
        assert content["data"] is None

    def test_custom_msg(self):
        """测试自定义错误消息"""
        response = Fail(msg="参数错误")

        content = json.loads(response.body.decode("utf-8"))
        assert content["msg"] == "参数错误"

    def test_custom_code(self):
        """测试自定义错误码"""
        response = Fail(code=500, msg="服务器内部错误")

        assert response.status_code == 500
        content = json.loads(response.body.decode("utf-8"))
        assert content["code"] == 500

    def test_with_error_details(self):
        """测试带错误详情"""
        response = Fail(
            msg="验证失败",
            data={"errors": ["字段 A 必填", "字段 B 格式错误"]},
        )

        content = json.loads(response.body.decode("utf-8"))
        assert content["data"]["errors"] == ["字段 A 必填", "字段 B 格式错误"]


class TestResponseComparison:
    """响应类对比测试"""

    def test_success_vs_success_extra_msg_default(self):
        """验证 Success 和 SuccessExtra 的 msg 默认值不同"""
        success = Success()
        success_extra = SuccessExtra()

        success_content = json.loads(success.body.decode("utf-8"))
        success_extra_content = json.loads(success_extra.body.decode("utf-8"))

        # Success 默认 msg="OK"
        assert success_content["msg"] == "OK"
        # SuccessExtra 默认 msg=None
        assert success_extra_content["msg"] is None

    def test_success_vs_success_extra_structure(self):
        """验证 Success 和 SuccessExtra 的响应结构"""
        success = Success(data={"id": "1"})
        success_extra = SuccessExtra(data=[{"id": "1"}], total=1)

        success_content = json.loads(success.body.decode("utf-8"))
        success_extra_content = json.loads(success_extra.body.decode("utf-8"))

        # Success 不包含分页字段
        assert "total" not in success_content
        assert "page" not in success_content
        assert "page_size" not in success_content

        # SuccessExtra 包含分页字段
        assert "total" in success_extra_content
        assert "page" in success_extra_content
        assert "page_size" in success_extra_content


class TestResponseIntegration:
    """响应集成测试"""

    def test_success_in_fastapi_context(self):
        """测试 Success 在 FastAPI 上下文中的使用"""
        from starlette.responses import JSONResponse

        response = Success(data={"message": "hello"})

        # 验证继承关系
        assert isinstance(response, JSONResponse)

    def test_success_extra_in_fastapi_context(self):
        """测试 SuccessExtra 在 FastAPI 上下文中的使用"""
        from starlette.responses import JSONResponse

        response = SuccessExtra(data=[], total=0)

        # 验证继承关系
        assert isinstance(response, JSONResponse)

    def test_response_body_is_bytes(self):
        """验证响应体是字节类型"""
        success = Success()
        success_extra = SuccessExtra()
        fail = Fail()

        assert isinstance(success.body, bytes)
        assert isinstance(success_extra.body, bytes)
        assert isinstance(fail.body, bytes)
