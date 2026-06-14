# 权限页面边界问题修复

## 修复文件
`/workspace/kcloudy.ai-platform/web/vue/src/iam/pages/permissions/PermissionList.vue`

## 修复内容
将空状态判断中的 `searchKeyword` 改为 `searchKeyword.trim()`，使与搜索过滤逻辑一致：

```vue
<!-- 修复前 -->
{{ searchKeyword ? '未找到匹配的权限' : '暂无权限数据' }}

<!-- 修复后 -->
{{ searchKeyword.trim() ? '未找到匹配的权限' : '暂无权限数据' }}
```

## 背景
搜索过滤逻辑在 `filteredPermissions` 计算属性中已经使用了 `searchKeyword.value.trim()`，但空状态判断没有同步更新，导致当用户输入仅包含空格的搜索关键词时，过滤逻辑和空状态显示不一致。

## 验证
修复后，空状态判断与搜索过滤逻辑保持一致，能够正确处理空字符串和仅包含空格的搜索关键词。