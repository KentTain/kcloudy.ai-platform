"""
响应格式专项测试

验证 ApiResponse 响应类的正确性。
"""

import json

from framework.common.response import ApiResponse


class TestApiResponse:
    """ApiResponse 响应测试"""

    def test_success_default_values(self):
        """测试 success 默认值"""
        response = ApiResponse.success()

        assert response.status_code == 200

        content = json.loads(response.body.decode("utf-8"))
        assert content["code"] == 200
        assert content["msg"] == "OK"
        assert content["data"] is None

    def test_success_custom_msg(self):
        """测试自定义 msg"""
        response = ApiResponse.success(msg="操作成功")

        content = json.loads(response.body.decode("utf-8"))
        assert content["msg"] == "操作成功"

    def test_success_with_data(self):
        """测试带 data"""
        response = ApiResponse.success(data={"id": "123", "name": "test"})

        content = json.loads(response.body.decode("utf-8"))
        assert content["data"]["id"] == "123"
        assert content["data"]["name"] == "test"

    def test_success_with_list_data(self):
        """测试列表 data"""
        response = ApiResponse.success(data=[{"id": "1"}, {"id": "2"}])

        content = json.loads(response.body.decode("utf-8"))
        assert isinstance(content["data"], list)
        assert len(content["data"]) == 2

    def test_success_with_extra_fields(self):
        """测试额外字段通过 kwargs 扩展"""
        response = ApiResponse.success(
            data={"message": "hello"},
            conversation_id="conv-123",
            has_more=True,
        )

        content = json.loads(response.body.decode("utf-8"))
        assert content["conversation_id"] == "conv-123"
        assert content["has_more"] is True

    def test_success_null_data(self):
        """测试 data 为 null"""
        response = ApiResponse.success(data=None)

        content = json.loads(response.body.decode("utf-8"))
        assert content["data"] is None


class TestPaginatedResponse:
    """分页响应测试"""

    def test_paginated_default_values(self):
        """测试 paginated 默认值"""
        response = ApiResponse.paginated()

        assert response.status_code == 200

        content = json.loads(response.body.decode("utf-8"))
        assert content["code"] == 200
        assert content["msg"] == "OK"
        assert content["data"] is None
        assert content["total"] == 0
        assert content["page"] == 1
        assert content["page_size"] == 20

    def test_paginated_fields(self):
        """测试分页字段"""
        response = ApiResponse.paginated(
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

    def test_paginated_custom_msg(self):
        """测试自定义 msg"""
        response = ApiResponse.paginated(
            data=[],
            total=0,
            msg="查询成功",
        )

        content = json.loads(response.body.decode("utf-8"))
        assert content["msg"] == "查询成功"

    def test_paginated_with_extra_fields(self):
        """测试额外字段"""
        response = ApiResponse.paginated(
            data=[],
            total=100,
            extra_field="extra_value",
        )

        content = json.loads(response.body.decode("utf-8"))
        assert content["extra_field"] == "extra_value"

    def test_paginated_empty_data_list(self):
        """测试空数据列表"""
        response = ApiResponse.paginated(data=[], total=0, page=1, page_size=20)

        content = json.loads(response.body.decode("utf-8"))
        assert content["data"] == []
        assert content["total"] == 0

    def test_paginated_large_dataset(self):
        """测试大数据集"""
        large_data = [{"id": str(i)} for i in range(1000)]
        response = ApiResponse.paginated(
            data=large_data,
            total=10000,
            page=1,
            page_size=1000,
        )

        content = json.loads(response.body.decode("utf-8"))
        assert len(content["data"]) == 1000
        assert content["total"] == 10000


class TestFailResponse:
    """失败响应测试"""

    def test_fail_default_values(self):
        """测试 fail 默认值"""
        response = ApiResponse.fail(msg="错误")

        assert response.status_code == 400

        content = json.loads(response.body.decode("utf-8"))
        assert content["code"] == 400
        assert content["msg"] == "错误"
        assert content["data"] is None

    def test_fail_custom_code(self):
        """测试自定义错误码"""
        response = ApiResponse.fail(msg="资源不存在", code=404)

        assert response.status_code == 404
        content = json.loads(response.body.decode("utf-8"))
        assert content["code"] == 404

    def test_fail_with_error_details(self):
        """测试带错误详情"""
        response = ApiResponse.fail(
            msg="验证失败",
            data={"errors": ["字段 A 必填", "字段 B 格式错误"]},
        )

        content = json.loads(response.body.decode("utf-8"))
        assert content["data"]["errors"] == ["字段 A 必填", "字段 B 格式错误"]

    def test_not_found(self):
        """测试 not_found 快捷方法"""
        response = ApiResponse.not_found("用户不存在")

        assert response.status_code == 404
        content = json.loads(response.body.decode("utf-8"))
        assert content["code"] == 404
        assert content["msg"] == "用户不存在"

    def test_unauthorized(self):
        """测试 unauthorized 快捷方法"""
        response = ApiResponse.unauthorized()

        assert response.status_code == 401
        content = json.loads(response.body.decode("utf-8"))
        assert content["code"] == 401

    def test_forbidden(self):
        """测试 forbidden 快捷方法"""
        response = ApiResponse.forbidden()

        assert response.status_code == 403
        content = json.loads(response.body.decode("utf-8"))
        assert content["code"] == 403

    def test_validation_error(self):
        """测试 validation_error 快捷方法"""
        response = ApiResponse.validation_error(data=[{"field": "name", "error": "required"}])

        assert response.status_code == 422
        content = json.loads(response.body.decode("utf-8"))
        assert content["code"] == 422

    def test_internal_error(self):
        """测试 internal_error 快捷方法"""
        response = ApiResponse.internal_error()

        assert response.status_code == 500
        content = json.loads(response.body.decode("utf-8"))
        assert content["code"] == 500


class TestResponseComparison:
    """响应对比测试"""

    def test_success_vs_paginated_msg_default(self):
        """验证 success 和 paginated 的 msg 默认值都是 OK"""
        success = ApiResponse.success()
        paginated = ApiResponse.paginated()

        success_content = json.loads(success.body.decode("utf-8"))
        paginated_content = json.loads(paginated.body.decode("utf-8"))

        # 两者默认 msg 都是 "OK"
        assert success_content["msg"] == "OK"
        assert paginated_content["msg"] == "OK"

    def test_success_vs_paginated_structure(self):
        """验证 success 和 paginated 的响应结构"""
        success = ApiResponse.success(data={"id": "1"})
        paginated = ApiResponse.paginated(data=[{"id": "1"}], total=1)

        success_content = json.loads(success.body.decode("utf-8"))
        paginated_content = json.loads(paginated.body.decode("utf-8"))

        # success 不包含分页字段
        assert "total" not in success_content
        assert "page" not in success_content
        assert "page_size" not in success_content

        # paginated 包含分页字段
        assert "total" in paginated_content
        assert "page" in paginated_content
        assert "page_size" in paginated_content


class TestResponseIntegration:
    """响应集成测试"""

    def test_response_in_fastapi_context(self):
        """测试 ApiResponse 在 FastAPI 上下文中的使用"""
        from starlette.responses import JSONResponse

        response = ApiResponse.success(data={"message": "hello"})

        # 验证继承关系
        assert isinstance(response, JSONResponse)

    def test_response_body_is_bytes(self):
        """验证响应体是字节类型"""
        success = ApiResponse.success()
        paginated = ApiResponse.paginated()
        fail = ApiResponse.fail(msg="error")

        assert isinstance(success.body, bytes)
        assert isinstance(paginated.body, bytes)
        assert isinstance(fail.body, bytes)
