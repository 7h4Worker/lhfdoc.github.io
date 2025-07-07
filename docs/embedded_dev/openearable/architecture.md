# OpenEarable 2.0 源码架构分析

## 项目结构概览

```
openearable-v2/
├── CMakeLists.txt              # 主构建配置文件
├── prj.conf                    # 项目配置文件
├── prj_release.conf           # 发布版本配置
├── prj_fota.conf              # FOTA版本配置
├── boards/                     # 板级支持包
│   └── teco/openearable_v2/   # OpenEarable v2硬件配置
├── src/                       # 源代码目录
│   ├── audio/                 # 音频处理模块
│   ├── Battery/               # 电源管理模块
│   ├── bluetooth/             # 蓝牙通信模块
│   ├── buttons/               # 按键处理模块
│   ├── drivers/               # 硬件驱动模块
│   ├── modules/               # 通用功能模块
│   ├── SensorManager/         # 传感器管理模块
│   ├── SD_Card/               # SD卡管理模块
│   ├── ParseInfo/             # 数据解析模块
│   ├── Wire/                  # I2C通信模块
│   └── utils/                 # 工具函数模块
├── unicast_server/            # 单播服务器应用
│   └── main.cpp               # 主入口文件
├── broadcast_sink/            # 广播接收器应用
├── include/                   # 公共头文件
└── tools/                     # 构建和烧录工具
```

## 应用架构分析

### 主应用入口 (unicast_server/main.cpp)

项目主要以单播服务器模式运行，主要初始化流程：

1. **系统初始化**
   - 电源管理器初始化
   - USB设备栈使能
   - 音频流控制启动

2. **状态管理**
   - SIRK (Set Identity Resolving Key) 检查
   - 配对状态设置
   - LED状态指示器初始化

3. **服务初始化**
   - 传感器管理器初始化
   - 蓝牙服务初始化（LED、电池、按键、传感器等）
   - 数据解析服务初始化

### 核心模块架构

#### 1. 电源管理模块 (src/Battery/)
- **PowerManager**: 电源状态管理
- **BQ27220**: 电池监测芯片驱动
- **BQ25120a**: 电池充电管理芯片驱动
- **BootState**: 启动状态管理

#### 2. 音频处理模块 (src/audio/)
- **audio_datapath**: 音频数据路径处理
- **audio_system**: 音频子系统管理
- **Equalizer**: 音频均衡器
- **streamctrl**: 音频流控制
- **pdm_mic**: PDM麦克风驱动

#### 3. 蓝牙通信模块 (src/bluetooth/)
- **bt_management**: 蓝牙连接管理
- **bt_stream**: 蓝牙音频流处理
- **gatt_services**: GATT服务实现
  - device_info: 设备信息服务
  - battery_service: 电池服务
  - sensor_service: 传感器服务
  - led_service: LED控制服务
  - button_service: 按键服务

#### 4. 传感器管理模块 (src/SensorManager/)
- **SensorManager**: 传感器统一管理接口
- **DefaultSensors**: 默认传感器配置
- **SensorScheme**: 传感器方案定义

#### 5. 硬件驱动模块 (src/drivers/)
- **ADAU1860**: 音频编解码器驱动
- **LED_Controller**: LED控制驱动

#### 6. 数据存储模块 (src/SD_Card/)
- **SDLogger**: SD卡数据记录
- **SD_Card_Manager**: SD卡管理
- **Benchmark**: 性能测试

#### 7. 通信模块 (src/Wire/)
- I2C通信协议实现
- 传感器通信接口

#### 8. 工具模块 (src/utils/)
- **StateIndicator**: 状态指示器
- **macros**: 通用宏定义
- **fw_info**: 固件信息管理

## 关键特性

### 多应用架构支持
- **单播服务器** (unicast_server): 主要应用模式，作为音频接收端
- **广播接收器** (broadcast_sink): 广播音频接收模式

### 模块化设计
- 每个功能模块都有独立的CMakeLists.txt
- 模块间通过定义良好的接口通信
- 支持模块的独立开发和测试

### 硬件抽象
- 通过设备树(DTS)文件进行硬件配置
- 驱动层与应用层分离
- 支持多种硬件平台

### 电源管理
- 完整的电池状态监控
- 充电状态管理
- 低功耗优化

### 传感器集成
- 统一的传感器管理接口
- 支持多种传感器类型
- 可配置的采样率和数据格式

## 构建系统

### CMake配置
- 使用Zephyr RTOS构建系统
- 支持条件编译配置
- 模块化的子目录构建

### 配置文件
- **prj.conf**: 基础配置
- **prj_release.conf**: 发布版本优化配置
- **prj_fota.conf**: 支持固件升级的配置

### 编译标志
- `HEADSET=1`: 耳机模式
- `GATEWAY=2`: 网关模式
- 支持不同的音频配置和功能

## 模块间通信机制

### ZBus 消息总线
- 基于Zephyr ZBus的发布-订阅模式
- 模块间解耦的异步通信
- 支持多订阅者的事件分发

### 关键消息类型
- **button_msg**: 按键事件消息
- **sensor_msg**: 传感器数据消息
- **battery_msg**: 电池状态消息
- **audio_msg**: 音频状态消息

### 工作队列和线程
- 各模块使用独立的工作队列
- 优先级配置的多线程架构
- 中断安全的消息传递

## 数据流分析

### 音频数据流
```
PDM麦克风 → 音频数据路径 → 均衡器处理 → 蓝牙LE Audio → 远程设备
```

### 传感器数据流
```
物理传感器 → 传感器管理器 → 数据融合 → 蓝牙GATT → 客户端应用
                                    ↓
                                SD卡存储
```

### 控制流
```
物理按键 → 按键管理器 → ZBus消息 → 各功能模块 → 状态更新 → LED指示
```

## 功耗优化策略

### 动态频率调节
- 根据工作负载调整CPU频率
- 传感器按需采样
- 音频流自适应比特率

### 外设管理
- 未使用外设的自动关闭
- I2C/SPI接口的低功耗模式
- GPIO引脚的合理配置

### 睡眠机制
- 系统空闲时进入低功耗模式
- 中断唤醒机制
- 电池电量监控和保护

## 完整模块文档

以下是各核心模块的详细分析文档：

### 核心功能模块
1. **[电源管理模块](../modules/battery-module.md)** - 电池监控、充电管理、功耗优化
2. **[音频处理模块](../modules/audio-module.md)** - 音频采集、处理、流控制
3. **[传感器管理模块](../modules/sensor-module.md)** - 多传感器融合、数据处理
4. **[蓝牙通信模块](../modules/bluetooth-module.md)** - LE Audio、GATT服务、连接管理
5. **[数据存储模块](../modules/storage-module.md)** - SD卡管理、数据记录
6. **[硬件驱动模块](../modules/drivers-module.md)** - 音频编解码器、LED控制器

### 辅助功能模块
7. **[按键处理模块](../modules/buttons-module.md)** - 物理按键、防抖处理、事件分发
8. **[数据解析模块](../modules/parseinfo-module.md)** - 传感器数据格式、蓝牙配置信息
9. **[I2C通信模块](../modules/wire-module.md)** - Arduino兼容I2C接口、设备通信
10. **[系统工具模块](../modules/utils-module.md)** - 状态指示、版本管理、错误处理

## 开发指南

### 添加新传感器
1. 在 `src/drivers/` 下创建驱动文件
2. 在 `src/SensorManager/` 中注册传感器
3. 在 `src/ParseInfo/` 中定义数据格式
4. 在 `src/bluetooth/gatt_services/` 中添加GATT特性

### 添加新功能模块
1. 创建模块目录和CMakeLists.txt
2. 定义模块接口和数据结构
3. 实现ZBus消息处理
4. 在主应用中集成模块

### 调试和测试
- 使用Zephyr日志系统
- 通过UART或RTT输出调试信息
- 单元测试和集成测试框架

## 总结

OpenEarable 2.0采用了现代化的嵌入式系统架构设计，具有以下特点：

1. **模块化设计**: 功能模块高度解耦，便于开发和维护
2. **消息驱动**: 基于ZBus的异步消息通信机制
3. **多应用支持**: 支持不同的应用场景和配置
4. **硬件抽象**: 良好的硬件抽象层，支持多平台移植
5. **功耗优化**: 全面的功耗管理和优化策略
6. **可扩展性**: 易于添加新功能和传感器
7. **可调试性**: 完善的日志和调试机制

该架构为智能可穿戴设备的开发提供了完整的解决方案，是一个值得学习和借鉴的优秀开源项目。

---

*本文档基于OpenEarable 2.0源码深度分析生成，各模块的详细技术文档请参考相关链接。*
