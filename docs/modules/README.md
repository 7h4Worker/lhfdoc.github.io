# OpenEarable 2.0 模块文档索引

## 概述

本目录包含了OpenEarable 2.0项目各个功能模块的详细技术文档。每个模块文档深入分析了源码实现、架构设计、接口定义、使用方法等内容。

## 核心功能模块

### [电源管理模块 (Battery-Module.md)](./Battery-Module.md)
- **PowerManager**: 电源状态统一管理
- **BQ27220**: 电池监测芯片（容量、电压、温度）
- **BQ25120a**: 电池充电管理芯片
- **BootState**: 启动状态检测和管理
- **功能**: 电池监控、充电控制、功耗优化、LED状态指示

### [音频处理模块 (Audio-Module.md)](./Audio-Module.md)
- **streamctrl**: 音频流控制和状态管理
- **audio_datapath**: 音频数据路径处理
- **audio_system**: 音频子系统初始化
- **Equalizer**: 音频均衡器处理
- **pdm_mic**: PDM麦克风驱动
- **功能**: 音频采集、处理、流控制、质量优化

### [传感器管理模块 (Sensor-Module.md)](./Sensor-Module.md)
- **SensorManager**: 传感器统一管理接口
- **EdgeMLSensor**: 边缘机器学习传感器
- **IMU传感器**: 加速度计、陀螺仪、磁力计
- **PPG传感器**: 心率和血氧检测
- **功能**: 多传感器融合、数据处理、AI推理、功耗管理

### [蓝牙通信模块 (Bluetooth-Module.md)](./Bluetooth-Module.md)
- **GATT服务**: 传感器、电池、LED、按键服务
- **LE Audio**: 低功耗音频流传输
- **连接管理**: 配对、连接状态管理
- **安全机制**: 加密、认证、密钥管理
- **功能**: 数据传输、音频流、设备控制、状态同步

### [数据存储模块 (Storage-Module.md)](./Storage-Module.md)
- **SDLogger**: 高效数据记录器
- **SD_Card_Manager**: SD卡生命周期管理
- **缓冲机制**: 环形缓冲区和批量写入
- **文件系统**: FAT文件系统支持
- **功能**: 数据持久化、性能优化、错误恢复

### [硬件驱动模块 (Drivers-Module.md)](./Drivers-Module.md)
- **ADAU1860**: 音频编解码器驱动
- **KTD2026**: RGB LED控制器驱动
- **GPIO控制**: 通用输入输出管理
- **功能**: 硬件抽象、设备控制、状态管理

## 辅助功能模块

### [按键处理模块 (Buttons-Module.md)](./Buttons-Module.md)
- **Button类**: 单个按键的完整生命周期管理
- **button_manager**: 按键事件消息队列管理
- **防抖机制**: 硬件防抖和软件状态确认
- **事件分发**: 基于ZBus的事件发布
- **功能**: 用户交互、事件处理、系统控制

### [数据解析模块 (ParseInfo-Module.md)](./ParseInfo-Module.md)
- **SensorScheme**: 传感器配置和解析方案
- **SensorComponent**: 传感器数据组件定义
- **数据类型**: 多种数据类型支持和序列化
- **蓝牙服务**: GATT服务集成和客户端交互
- **功能**: 数据格式化、协议定义、客户端支持

### [I2C通信模块 (Wire-Module.md)](./Wire-Module.md)
- **MbedI2C**: Arduino兼容的I2C接口
- **TWIM**: 底层I2C管理
- **环形缓冲区**: 高效的数据缓冲机制
- **线程安全**: 互斥锁保护的并发访问
- **功能**: 传感器通信、设备控制、数据传输

### [系统工具模块 (Utils-Module.md)](./Utils-Module.md)
- **StateIndicator**: LED状态指示器
- **版本管理**: 硬件版本检测和管理
- **错误处理**: 系统错误处理和恢复机制
- **UICR管理**: 用户信息配置寄存器
- **功能**: 状态指示、系统监控、错误恢复、调试支持

## 模块关系图

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   按键处理模块   │    │   系统工具模块   │    │   I2C通信模块   │
│   (Buttons)     │    │    (Utils)      │    │    (Wire)       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │              ┌─────────────────┐              │
         └──────────────→│   ZBus消息总线   │←─────────────┘
                        │  (Message Bus)  │
         ┌──────────────→└─────────────────┘←─────────────┐
         │                       │                       │
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   音频处理模块   │    │   蓝牙通信模块   │    │   传感器管理     │
│    (Audio)      │    │  (Bluetooth)    │    │   (Sensor)      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │              ┌─────────────────┐              │
         └──────────────→│   数据解析模块   │←─────────────┘
                        │  (ParseInfo)    │
                        └─────────────────┘
                                 │
                        ┌─────────────────┐
                        │   数据存储模块   │
                        │   (Storage)     │
                        └─────────────────┘
                                 │
                        ┌─────────────────┐
                        │   硬件驱动模块   │
                        │   (Drivers)     │
                        └─────────────────┘
                                 │
                        ┌─────────────────┐
                        │   电源管理模块   │
                        │   (Battery)     │
                        └─────────────────┘
```

## 核心设计原则

### 1. 模块化设计
- 每个模块独立开发和测试
- 清晰的模块边界和接口定义
- 松耦合的模块间通信

### 2. 消息驱动架构
- 基于ZBus的发布-订阅模式
- 异步消息处理机制
- 事件驱动的系统响应

### 3. 硬件抽象
- 统一的硬件接口层
- 设备驱动与应用分离
- 跨平台移植支持

### 4. 功耗优化
- 智能功耗管理策略
- 动态频率和功耗调节
- 低功耗模式支持

### 5. 可扩展性
- 易于添加新功能模块
- 灵活的配置和定制机制
- 开放的接口设计

## 开发和调试

### 日志系统
- 分模块的日志级别控制
- 实时日志输出和分析
- 调试信息的结构化记录

### 配置管理
- Kconfig配置系统
- 设备树硬件描述
- 编译时和运行时配置

### 测试支持
- 单元测试框架
- 集成测试用例
- 性能测试和分析

## 使用指南

### 新手入门
1. 从[顶层架构文档](../OpenEarable-源码架构分析.md)开始了解整体架构
2. 阅读感兴趣的模块详细文档
3. 参考典型使用场景和代码示例
4. 进行实际的开发和调试

### 进阶开发
1. 深入理解模块间的交互机制
2. 学习硬件抽象层的实现
3. 掌握功耗优化的策略和技巧
4. 参与开源项目的贡献和改进

## 文档维护

### 更新原则
- 与源码同步更新
- 保持文档的准确性和完整性
- 及时反映架构和接口变更

### 贡献指南
- 遵循文档格式和风格
- 提供清晰的代码示例
- 包含充分的使用说明

---

*本索引文档提供了OpenEarable 2.0项目完整的模块文档导航，帮助开发者快速定位和理解各个功能模块。*
