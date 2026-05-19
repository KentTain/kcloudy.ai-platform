# 配置目录

本目录配置文件已迁移至共享配置目录 `server/config/`。

## 配置文件位置

实际配置文件位于：

```
server/config/
├── application.yml              # 基础配置
├── application-local.yml.example # 本地配置示例
└── application-local.yml        # 本地配置（不提交）
```

## 本地开发

1. 复制配置示例：

```bash
cp server/config/application-local.yml.example server/config/application-local.yml
```

2. 修改 `application-local.yml` 中的配置

## 说明

配置路径在启动时通过 `--config` 参数指定，默认为 `../config/application.yml`。

所有技术栈共享同一份配置，便于统一管理。
