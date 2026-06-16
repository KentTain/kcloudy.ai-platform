## 新增需求

### 需求:前端类型必须使用标准后缀命名
前端所有 API 通信对象的类型定义必须遵循 `{Entity}{Action}` 格式，禁止使用 `Params`/`QueryParams` 后缀。

#### 场景:替换 Create 后缀
- **当** 前端类型原名为 `Create{Entity}Params`
- **那么** 重命名为 `{Entity}Create`

#### 场景:替换 Update 后缀
- **当** 前端类型原名为 `Update{Entity}Params`
- **那么** 重命名为 `{Entity}Update`

#### 场景:替换 Query 后缀
- **当** 前端类型原名为 `{Entity}QueryParams`
- **那么** 重命名为 `{Entity}Query`

### 需求:后端 Schema 必须使用标准后缀命名
后端 Pydantic Schema 的请求/响应类命名必须在各模块间保持一致。

#### 场景:响应类统一使用 Response 后缀
- **当** 后端 Schema 原名为 `{Entity}Vo`
- **那么** 重命名为 `{Entity}Response`

#### 场景:列表响应使用 ListResponse 后缀
- **当** 后端 Schema 原名为 `{Entity}ListVo`
- **那么** 重命名为 `{Entity}ListResponse`

#### 场景:树响应使用 TreeResponse 后缀
- **当** 后端 Schema 代表树结构
- **那么** 后缀使用 `TreeResponse`

#### 场景:属性配置响应使用 PropertyResponse 后缀
- **当** 后端 Schema 代表资源配置或属性
- **那么** 后缀使用 `PropertyResponse`

#### 场景:请求 Schema 去掉 Request 后缀
- **当** 后端 Schema 原名为 `{Entity}CreateRequest`/`{Entity}UpdateRequest`
- **那么** 去掉 `Request` 后缀，改为 `{Entity}Create`/`{Entity}Update`

### 需求:所有引用旧名的位置必须同步更新
重命名类型后，所有引用该类型的模块必须同步更新，确保编译和类型检查通过。

#### 场景:后端 API 控制器引用更新
- **当** Controller 中引用了旧 Schema 类名
- **那么** 更新 `import` 语句和使用处的类名

#### 场景:前端 API 函数引用更新
- **当** API 函数中使用了旧类型
- **那么** 更新 `import` 语句和类型标注

#### 场景:前端 Store 引用更新
- **当** Pinia Store 中引用了旧类型
- **那么** 更新类型引用

#### 场景:前端页面组件引用更新
- **当** Vue 页面组件中引用了旧类型
- **那么** 更新类型引用
