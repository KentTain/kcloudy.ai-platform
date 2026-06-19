## ADDED Requirements

### 需求:模块元数据声明数据结构

系统必须提供模块元数据声明的数据结构，支持声明菜单、权限和默认角色。

#### 场景:定义菜单数据结构
- **当** 模块声明 MenuDef 数据类
- **那么** 必须包含 code、name、path 字段，可选 icon、parent_code、sort_order、is_visible 字段

#### 场景:定义权限数据结构
- **当** 模块声明 PermissionDef 数据类
- **那么** 必须包含 code、name、resource、action 字段，可选 description 字段

#### 场景:定义角色数据结构
- **当** 模块声明 RoleDef 数据类
- **那么** 必须包含 code、name 字段，可选 description、permission_codes、is_system 字段

#### 场景:定义模块完整定义数据结构
- **当** 模块声明 ModuleDefinition 数据类
- **那么** 必须包含 code、name 字段，可选 description、icon、version、menus、permissions、default_roles 字段

### 需求:ModuleDescriptor 协议扩展

系统必须扩展 ModuleDescriptor 协议，新增 get_module_definition() 方法。

#### 场景:模块实现声明方法
- **当** 模块类实现 get_module_definition() 方法
- **那么** 返回 ModuleDefinition 实例或 None（未实现）

#### 场景:模块未实现声明方法
- **当** 模块类未实现 get_module_definition() 方法
- **那么** 调用该方法返回 None，同步服务跳过该模块

### 需求:菜单 code 格式规范

系统必须规范菜单 code 的命名格式。

#### 场景:菜单 code 格式正确
- **当** 菜单 code 格式为 `<module>.<name>`（如 `iam.users`）
- **那么** 系统接受该菜单定义

#### 场景:菜单 code 重复
- **当** 两个模块定义相同 code 的菜单
- **那么** 同步服务抛出错误，应用启动失败

### 需求:权限 code 格式规范

系统必须规范权限 code 的命名格式。

#### 场景:权限 code 格式正确
- **当** 权限 code 格式为 `<module>:<resource>:<action>`（如 `iam:user:read`）
- **那么** 系统接受该权限定义

#### 场景:权限 code 重复
- **当** 两个模块定义相同 code 的权限
- **那么** 同步服务抛出错误，应用启动失败
