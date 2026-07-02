# Controller 测试规范

## 测试目标

Controller 层单元测试的核心目标：
1. **Mock Service 层返回对象**
2. **测试 Controller 的最终返回对象是否正确、是否出错**

## 测试关注点

### ✅ 应该测试

| 场景 | 说明 |
|------|------|
| 正常返回 | Service 返回数据后，Controller 正确封装响应 |
| 错误处理 | Service 抛出异常或返回 None 时，Controller 正确处理错误 |
| 参数传递 | Controller 将请求参数正确传递给 Service（通过 mock 验证） |
| 响应格式 | 返回的 JSON 结构、字段名称、状态码是否正确 |

### ❌ 不应该测试

| 场景 | 说明 |
|------|------|
| Service 调用细节 | 不验证 Service 方法被调用几次、调用参数是什么 |
| Service 内部逻辑 | Service 层如何查询数据、如何处理业务逻辑 |
| 副作用验证 | 不验证是否调用了某个上下文设置方法（除非影响返回结果） |
| ORM 模型字段完整性 | Mock 对象只需设置 Controller 真正用到的字段 |

## 测试示例

### ✅ 正确示例 1：测试成功返回

```python
async def test_get_tenant_success(self, mock_session):
    """成功获取租户"""
    from tenant.controllers.inner.tenant_controller import get_tenant
    
    # 准备 mock 数据 - 只设置 Controller 真正用到的字段
    mock_tenant = MagicMock()
    mock_tenant.id = "tenant-1"
    mock_tenant.name = "测试租户"
    mock_tenant.code = "TEST001"
    mock_tenant.status = "active"
    
    # Mock Service 层
    with patch("tenant.controllers.inner.tenant_controller.TenantService.get_by_id") as mock_get:
        mock_get.return_value = mock_tenant
        
        # 执行测试
        result = await get_tenant(tenant_id="tenant-1", session=mock_session)
        
        # 验证返回对象
        assert result.status_code == 200
        data = json.loads(result.body.decode())
        assert data["code"] == 200
        assert data["data"]["id"] == "tenant-1"
        assert data["data"]["name"] == "测试租户"
```

### ✅ 正确示例 2：测试错误处理

```python
async def test_get_tenant_not_found(self, mock_session):
    """租户不存在时抛出 404"""
    from tenant.controllers.inner.tenant_controller import get_tenant
    
    # Mock Service 返回 None
    with patch("tenant.controllers.inner.tenant_controller.TenantService.get_by_id") as mock_get:
        mock_get.return_value = None
        
        # 执行测试并验证异常
        with pytest.raises(HTTPException) as exc_info:
            await get_tenant(tenant_id="nonexistent", session=mock_session)
        
        # 验证异常信息
        assert exc_info.value.status_code == 404
        assert "不存在" in exc_info.value.detail
```

### ❌ 错误示例：过度验证 Service 调用

```python
async def test_get_tenant_success(self, mock_session):
    """错误：验证了 Service 调用细节"""
    mock_tenant = MagicMock()
    # ... 设置几十个字段
    
    with patch("...Service.get_by_id") as mock_get:
        mock_get.return_value = mock_tenant
        
        result = await get_tenant(tenant_id="tenant-1", session=mock_session)
        
        # ❌ 错误：验证 Service 调用参数
        mock_get.assert_called_once_with(mock_session, "tenant-1", use_cache=True)
        
        # ❌ 错误：验证其他副作用
        mock_context.assert_called_once()
```

## Mock 对象设置原则

### 只设置 Controller 用到的字段

```python
# ✅ 正确：Controller 只用到 id、name、code
mock_tenant = MagicMock()
mock_tenant.id = "tenant-1"
mock_tenant.name = "测试租户"
mock_tenant.code = "TEST001"

# ❌ 错误：设置了一堆用不到的字段
mock_tenant.contact_name = "联系人"
mock_tenant.contact_email = "test@example.com"
mock_tenant.contact_phone = "13800138000"
mock_tenant.expired_at = None
# ... 更多无关字段
```

## 多 Service 调用的测试

当 Controller 调用多个 Service 时：

```python
async def test_list_user_tenants_success(self, mock_session):
    """测试多 Service 调用"""
    # Mock 第一个 Service
    mock_user_tenant = MagicMock()
    mock_user_tenant.tenant_id = "tenant-1"
    mock_user_tenant.role = "owner"
    mock_user_tenant.is_default = True
    
    # Mock 第二个 Service
    mock_tenant = MagicMock()
    mock_tenant.id = "tenant-1"
    mock_tenant.name = "测试租户"
    mock_tenant.code = "TEST001"
    mock_tenant.status = "active"
    
    with patch("framework.clients.iam_client.get_iam_client") as mock_iam:
        mock_iam_client = MagicMock()
        mock_iam_client.get_user_tenants = AsyncMock(return_value=[mock_user_tenant])
        mock_iam.return_value = mock_iam_client
        
        with patch("...TenantService.get_tenants_batch") as mock_batch:
            mock_batch.return_value = [mock_tenant]
            
            result = await list_user_tenants(user_id="user-1", session=mock_session)
            
            # ✅ 只验证最终返回
            assert result.status_code == 200
            data = json.loads(result.body.decode())
            assert len(data["data"]) == 1
            assert data["data"][0]["id"] == "tenant-1"
```

## 总结

Controller 层测试的核心原则：
1. **关注输入输出**：Service 返回什么 → Controller 返回什么
2. **简化 Mock 数据**：只设置 Controller 真正用到的字段
3. **不验证调用细节**：不关心 Service 被调用几次、参数是什么
4. **测试错误处理**：确保 Controller 正确处理 Service 的异常情况
