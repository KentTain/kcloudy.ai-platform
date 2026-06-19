## ADDED Requirements

### Requirement: Pub/Sub 心跳消息处理器
系统 SHALL 提供 `HeartbeatHandler` 类，继承 `SingleTopicHandler`，监听 `demo:heartbeat` 主题，收到消息后记录消息内容到日志。

#### Scenario: 收到心跳消息
- **WHEN** `demo:heartbeat` 主题收到消息
- **THEN** 处理器记录包含消息 payload 的日志

#### Scenario: 消息 payload 为空
- **WHEN** 收到的消息 payload 为空字典
- **THEN** 处理器记录包含空 payload 的日志，不抛出异常

### Requirement: Queue 数据集通知处理器
系统 SHALL 提供 `DatasetNotifyHandler` 类，继承 `SingleQueueHandler`，消费 `demo:dataset:notify` 队列，收到消息后记录消息内容到日志。

#### Scenario: 收到数据集通知
- **WHEN** `demo:dataset:notify` 队列收到消息
- **THEN** 处理器记录包含消息 body 的日志

#### Scenario: 消息 body 缺失必要字段
- **WHEN** 收到的消息 body 不含 `dataset_id` 字段
- **THEN** 处理器记录警告日志，跳过处理，不抛出异常

### Requirement: Listeners 生命周期管理
系统 SHALL 提供 `setup_listeners()` 和 `cleanup_listeners()` 异步函数，管理所有消息处理器的注册和清理。

#### Scenario: 启动监听器
- **WHEN** 调用 `setup_listeners()`
- **THEN** 注册所有 Pub/Sub 和 Queue 处理器到消息基础设施

#### Scenario: 清理监听器
- **WHEN** 调用 `cleanup_listeners()`
- **THEN** 取消所有消息处理器订阅，释放资源

### Requirement: Listeners 主题和队列常量
系统 SHALL 在 `constants.py` 中定义所有 Pub/Sub 主题名和 Queue 队列名常量，禁止在处理器中硬编码字符串。

#### Scenario: 使用常量引用主题名
- **WHEN** 处理器需要引用主题名
- **THEN** 使用 `HEARTBEAT_TOPIC` 常量而非硬编码字符串

### Requirement: application_listener.py 入口
系统 SHALL 将 `application_listener.py` 从占位符替换为真实实现，通过 `manage.py runlistener` 命令启动监听器。

#### Scenario: 运行监听器命令
- **WHEN** 执行 `python manage.py runlistener`
- **THEN** 调用 `setup_listeners()` 启动消息监听，进程持续运行直到被终止
