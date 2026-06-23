# 使用playwright进行e2e测试的需求

## 使用playwright对本项目进行e2e测试，测试内容（tenant模块、iam模块），具体内容包括

### 1.服务器使用headless方式进行测试，需要实现自动登录后进行测试

### 2.tenant模块的测试内容

### 2.1.登录测试地址：/admin/login，后端登录接口：<http://localhost:5173/api/iam/console/v1/auth/login，返回格式如下>

``` json
{
    "code": 200,
    "msg": "OK",
    "data": {
        "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIj",
        "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoiNzRmZjBiNGQtMmFmNy00M2Y0L",
        "expires_in": 7200,
        "token_type": "Bearer",
        "need_complete_profile": false,
        "tenant_id": "00000000-0000-0000-0000-000000000000"
    }
}
```

### 2.2.登录后获取登录用户的数据接口：<http://localhost:5173/api/tenant/admin/v1/admin/me，返回格式如下>

``` json
{
    "code": 200,
    "msg": "OK",
    "data": {
        "id": "74ff0b4d-2af7-43f4-bd6c-7090f9c982e0",
        "tenant_id": "00000000-0000-0000-0000-000000000000",
        "username": "admin",
        "email": "admin@example.com",
        "phone": null,
        "nickname": "系统管理员",
        "avatar": null,
        "status": "active",
        "profile_completed": true,
        "is_email_verified": true,
        "is_phone_verified": false,
        "last_login_at": "2026-06-23T02:25:09.079868+00:00",
        "created_at": "2026-06-22T11:21:37.867319+00:00",
        "roles": [
            "sysAdmin"
        ],
        "permissions": [
            "tenant:module:delete",
            "tenant:module:read",
            "tenant:module:write",
            "tenant:resource:delete",
            "tenant:resource:read",
            "tenant:resource:write",
            "tenant:tenant:delete",
            "tenant:tenant:read",
            "tenant:tenant:write"
        ],
        "tenants": [
            {
                "id": "00000000-0000-0000-0000-000000000000",
                "name": "默认租户",
                "code": "default",
                "is_default": true
            }
        ],
        "menus": [
            {
                "id": "module_iam",
                "code": "iam.module",
                "name": "系统管理",
                "icon": "Shield",
                "path": null,
                "sort_order": 0,
                "is_visible": true,
                "children": [
                    {
                        "id": "f47f270f-ae81-48fa-baac-980b412faae8",
                        "code": "iam.roles.create",
                        "name": "创建角色",
                        "icon": null,
                        "path": "/iam/roles/create",
                        "sort_order": 1,
                        "is_visible": false,
                        "children": []
                    },
                    {
                        "id": "263dd005-ba20-4f41-ad29-d3ac41bd4f9d",
                        "code": "iam.menus.create",
                        "name": "创建菜单",
                        "icon": null,
                        "path": "/iam/menus/create",
                        "sort_order": 1,
                        "is_visible": false,
                        "children": []
                    }
                ]
            },
            {
                "id": "module_ai",
                "code": "ai.module",
                "name": "AI 能力",
                "icon": "Robot",
                "path": null,
                "sort_order": 1,
                "is_visible": true,
                "children": [
                    {
                        "id": "9736b9c8-69bd-41aa-aee0-9c01238c4d57",
                        "code": "ai.plugins",
                        "name": "插件管理",
                        "icon": "Puzzle",
                        "path": "/ai/plugins",
                        "sort_order": 1,
                        "is_visible": true,
                        "children": []
                    }
                ]
            }
        ]
    }
}
```

### 2.3.根据登录用户的菜单数据，对tenant模块的整个功能进行冒烟测试，测试顺序如下

``` text
1.资源配置，包括以下功能：
1.1.数据库tab页签，新增配置、编辑配置、删除配置；
1.2.存储tab页签，新增配置、编辑配置、删除配置；
1.3.其他资源配置（缓存、队列、发布订阅）的创建、编辑及删除；
1.4.实际操作过程中，所有资源列表的显示数据总数是否正确；
1.5.实际操作过程中，统计功能是否准确，包括：配置总数、已被引用、未被使用；
1.6.只测试功能，不测试“测试”功能；

2.模块管理，包括以下功能：
2.1.模块基本功能，新增、编辑、查看详情、删除；
2.2.实际操作过程中，所有模块列表的显示数据总数是否正确；
2.3.根据模块名称或编码、模块状态查询，所有模块列表的显示数据是否正确；
2.4.实际操作过程中，统计功能是否准确，包括：模块总数、启用模块、必须模块、已分配次数；

3.租户管理，包括以下功能：
3.1.租户基本功能，新增、编辑、查看详情、停用、删除；
3.2.实际操作过程中，所有租户列表的显示数据总数是否正确；
3.3.根据租户名称或编码、租户状态查询，所有租户列表的显示数据是否正确；
3.4.实际操作过程中，统计功能是否准确，包括：租户总数、未激活数、过期数；
```

### 3.iam模块的测试内容

### 3.1.登录测试：/login，登录接口：<http://localhost:5173/api/iam/console/v1/auth/login，返回格式同tenant接口后端登录接口>>

### 3.2.登录后获取登录用户的数据接口：<http://localhost:5173/api/iam/console/v1/users/me，返回格式同tenant接口后端获取登录用户信息接口>>

### 3.3.根据登录用户的菜单数据，对iam模块的整个功能进行冒烟测试

``` text

```

### 4.测试完成后，将测试报告写入：docs\tests，按 模块 + 日期时间 进行命名，例如：tenant-2026-06-12.md

## 本项目的测试环境如下

### 1. 已经安装：playwright（1.60.0）及其cli（0.1.13），配置文件：web\vue\playwright.config.ts

### 2. 已有的测试账号，tenant模块：tenant_admin/admin123，iam模块：admin/admin123

### 3. 本地docker已经启动且基础设施完善，可通过配置进行连接：server\config\application-local.yml

### 4. 后端项目地址：server\python，构建及启动命令

``` bash
# 同步所有依赖组
uv sync --all-groups

# 启动 Web 服务（加载所有模块）
uv run python manage.py runserver --host 0.0.0.0 --port 8080
```

默认启动地址：<http://127.0.0.1:8080/>

### 5. 前端项目地址：web\vue，构建及启动命令

``` bash
# 安装依赖
pnpm install

# 启动开发服务器
pnpm dev，
```

默认启动地址：<http://127.0.0.1:5173/>
