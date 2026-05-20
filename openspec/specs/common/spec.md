## ADDED Requirements

### Requirement: 异常类层次结构
系统 SHALL 提供完整的异常类层次结构，包含 UnauthorizedError、ForbiddenError、NotFoundError、BadRequestError、ServiceUnavailableError 等。

#### Scenario: 抛出 BadRequestError
- **WHEN** 业务逻辑检测到无效请求参数
- **THEN** 抛出 `BadRequestError("无效参数")` 异常

#### Scenario: 异常消息获取
- **WHEN** 捕获异常 `e = BadRequestError("参数不能为空")`
- **THEN** `e.message` 返回 `"参数不能为空"`

### Requirement: 统一响应格式
系统 SHALL 提供统一的 API 响应格式，包含 code、message、data 字段。

#### Scenario: 成功响应
- **WHEN** 调用 `success_response(data={"id": 1})`
- **THEN** 返回 `{"code": 0, "message": "success", "data": {"id": 1}}`

#### Scenario: 错误响应
- **WHEN** 调用 `error_response(message="操作失败", code=1001)`
- **THEN** 返回 `{"code": 1001, "message": "操作失败", "data": null}`

### Requirement: 请求上下文
系统 SHALL 提供请求上下文管理，支持存储当前用户、租户等信息。

#### Scenario: 设置上下文
- **WHEN** 调用 `ctx.set_user(user_info)`
- **THEN** 后续可通过 `ctx.get_user()` 获取用户信息

#### Scenario: 清理上下文
- **WHEN** 请求结束后
- **THEN** 上下文自动清理，避免内存泄漏

### Requirement: 全局异常处理
系统 SHALL 提供全局异常处理器，将自定义异常转换为统一响应格式。

#### Scenario: 捕获 NotFoundError
- **WHEN** 业务逻辑抛出 `NotFoundError("数据不存在")`
- **THEN** API 返回 HTTP 404 和 `{"code": 404, "message": "数据不存在", "data": null}`

#### Scenario: 捕获未处理异常
- **WHEN** 发生未处理的异常
- **THEN** API 返回 HTTP 500 和 `{"code": 500, "message": "服务器内部错误", "data": null}`
