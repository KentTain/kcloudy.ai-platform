## 新增需求

### 需求:子域名路由配置

系统必须配置 nginx 支持子域名路由。

nginx 配置必须：
- 匹配任意子域名 (*.example.com)
- 将子域名映射到对应模块
- 处理 SPA 路由回退

#### 场景:匹配 demo 子域名
- **当** 请求 demo.example.com
- **那么** nginx 提供 demo 模块的静态文件

#### 场景:匹配 platform 子域名
- **当** 请求 platform.example.com
- **那么** nginx 提供平台版（全模块）的静态文件

#### 场景:SPA 路由回退
- **当** 请求 demo.example.com/some-page（非静态文件）
- **那么** nginx 返回 index.html，由前端路由处理

### 需求:API 反向代理

系统必须配置 nginx 将 API 请求代理到后端服务。

API 代理配置必须：
- 匹配 `/api/` 路径前缀
- 代理到后端服务地址
- 传递原始请求头（Host、X-Real-IP 等）

#### 场景:代理 API 请求
- **当** 请求 demo.example.com/api/v1/menus/user
- **那么** nginx 代理到 backend:8000/api/v1/menus/user

#### 场景:传递客户端 IP
- **当** 代理 API 请求
- **那么** 后端收到 X-Real-IP 头包含真实客户端 IP

### 需求:Cookie 共享配置

系统必须配置 nginx 支持 Cookie 跨子域名共享。

Cookie 配置必须：
- 设置响应头 `Set-Cookie` 的 Domain 属性为 `.example.com`
- 确保 SameSite 属性兼容跨子域名

#### 场景:登录后 Cookie 共享
- **当** 用户在 platform.example.com 登录
- **那么** Cookie 对 demo.example.com、iam.example.com 等子域名可见

### 需求:静态资源缓存

系统必须配置 nginx 静态资源缓存策略。

缓存配置必须：
- JS/CSS 文件设置长期缓存（1 年）
- HTML 文件禁用缓存
- 使用文件内容 hash 作为缓存 key

#### 场景:缓存 JS 文件
- **当** 请求 assets/index.abc123.js
- **那么** nginx 设置 Cache-Control: max-age=31536000

#### 场景:不缓存 HTML 文件
- **当** 请求 index.html
- **那么** nginx 设置 Cache-Control: no-cache

### 需求:Gzip 压缩

系统必须配置 nginx 启用 Gzip 压缩。

Gzip 配置必须：
- 压缩 text/html、text/css、application/javascript 类型
- 设置最小压缩大小（1KB）
- 设置压缩级别（6）

#### 场景:压缩响应
- **当** 请求大于 1KB 的 JS 文件
- **那么** nginx 返回 gzip 压缩的响应

## 修改需求

无。

## 移除需求

无。
