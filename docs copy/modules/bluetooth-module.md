# 蓝牙通信模块详细分析

## 模块概述

蓝牙通信模块是OpenEarable 2.0与外部设备通信的核心组件，基于Bluetooth LE Audio协议栈构建，提供音频流传输、GATT服务、设备管理等功能。该模块不仅支持高质量音频传输，还提供了丰富的传感器数据传输和设备控制接口。

## 文件结构

```
src/bluetooth/
├── bt_management/           # 蓝牙连接管理
├── bt_stream/              # 蓝牙音频流处理
├── bt_content_control/     # 内容控制
├── bt_rendering_and_capture/ # 音频渲染和捕获
├── gatt_services/          # GATT服务实现
│   ├── device_info.h/.c        # 设备信息服务
│   ├── battery_service.h/.cpp   # 电池服务
│   ├── sensor_service.h/.c      # 传感器服务  
│   ├── led_service.h/.cpp       # LED控制服务
│   ├── button_service.h/.c      # 按键服务
│   └── audio_config_service.h/.c # 音频配置服务
├── CMakeLists.txt          # 构建配置
├── Kconfig                 # 配置选项
└── Kconfig.defaults        # 默认配置
```

## 核心架构

### 1. GATT服务架构

OpenEarable 2.0实现了多个自定义GATT服务，为客户端提供完整的设备控制和数据访问接口。

#### 服务概览

| 服务名称 | 功能描述 | 主要特征 |
|---------|----------|----------|
| Device Info | 设备信息查询 | 制造商、型号、固件版本等 |
| Battery Service | 电池状态监控 | 电量、充电状态、健康状态 |
| Sensor Service | 传感器数据传输 | 配置、数据流、录制控制 |
| LED Service | LED状态控制 | 颜色、模式、亮度控制 |
| Button Service | 按键事件通知 | 按键状态、事件通知 |
| Audio Config | 音频参数配置 | 采样率、编解码器设置 |

### 2. 传感器服务详解

传感器服务是OpenEarable的核心创新服务，提供完整的传感器数据访问和控制接口。

#### UUID定义

```cpp
// 传感器服务UUID
#define BT_UUID_SENSOR_VAL \
    BT_UUID_128_ENCODE(0x34c2e3bb, 0x34aa, 0x11eb, 0xadc1, 0x0242ac120002)

// 传感器配置特征UUID
#define BT_UUID_SENSOR_CONFIG_VAL \
    BT_UUID_128_ENCODE(0x34c2e3be, 0x34aa, 0x11eb, 0xadc1, 0x0242ac120002)

// 传感器数据特征UUID
#define BT_UUID_SENSOR_DATA_VAL \
    BT_UUID_128_ENCODE(0x34c2e3bc, 0x34aa, 0x11eb, 0xadc1, 0x0242ac120002)

// 配置状态特征UUID
#define BT_UUID_SENSOR_CONFIG_STATUS_VAL \
    BT_UUID_128_ENCODE(0x34c2e3bf, 0x34aa, 0x11eb, 0xadc1, 0x0242ac120002)

// 录制名称特征UUID
#define BT_UUID_SENSOR_RECORDING_NAME_VAL \
    BT_UUID_128_ENCODE(0x34c2e3c0, 0x34aa, 0x11eb, 0xadc1, 0x0242ac120002)
```

#### 服务接口

```cpp
// 传感器服务初始化
int init_sensor_service();

// 传感器配置状态设置
int set_sensor_config_status(struct sensor_config config);

// 获取录制名称
const char *get_sensor_recording_name();
```

#### 传感器配置协议

```cpp
// 传感器配置结构
struct sensor_config {
    uint8_t sensorId;           // 传感器ID
    uint8_t sampleRateIndex;    // 采样率索引
    uint8_t storageOptions;     // 存储选项位图
} __attribute__((packed));

// 存储选项位图定义
#define STORAGE_SD_CARD    (1 << 0)    // SD卡存储
#define STORAGE_BLE_STREAM (1 << 1)    // 蓝牙流传输
#define STORAGE_FLASH      (1 << 2)    // 内部Flash存储
```

### 3. 电池服务详解

电池服务提供完整的电源状态信息，支持标准GATT电池服务扩展。

#### 电池状态结构

```cpp
// 电池电量状态
struct battery_level_status {
    uint8_t flags;              // 状态标志
    uint16_t power_state;       // 电源状态
} __attribute__((packed));

// 电池能量状态
struct battery_energy_status {
    uint8_t flags;              // 状态标志
    struct sfloat voltage;      // 电压(V)
    struct sfloat available_capacity; // 可用容量(mAh)
    struct sfloat charge_rate;  // 充电速率(mA)
} __attribute__((packed));

// 电池健康状态
struct battery_health_status {
    uint8_t flags;              // 状态标志
    uint8_t battery_health_summary; // 健康状态摘要
    uint16_t cycle_count;       // 循环次数
    int8_t current_temperature; // 当前温度(°C)
} __attribute__((packed));
```

#### 服务接口

```cpp
// 电池服务初始化
int init_battery_service();

// 发送电池电量数据
int bt_send_battery_level(struct battery_data *data);
```

### 4. LED服务详解

LED服务提供LED状态的完整控制接口，支持颜色、亮度、模式控制。

#### LED控制结构

```cpp
// RGB颜色定义
typedef uint8_t RGBColor[3];

// LED模式枚举
enum led_mode {
    STATE_INDICATION,   // 状态指示模式
    CUSTOM,            // 自定义模式
};

// LED配置结构
struct led_config {
    enum led_mode mode;     // LED模式
    RGBColor color;         // RGB颜色
    uint8_t brightness;     // 亮度(0-255)
    uint16_t pattern;       // 闪烁模式
} __attribute__((packed));
```

### 5. 按键服务详解

按键服务提供按键事件的实时通知功能。

#### 按键事件结构

```cpp
// 按键状态结构
struct button_event {
    uint8_t button_id;      // 按键ID
    uint8_t event_type;     // 事件类型
    uint32_t timestamp;     // 时间戳
} __attribute__((packed));

// 事件类型定义
enum button_event_type {
    BUTTON_PRESS,           // 按键按下
    BUTTON_RELEASE,         // 按键释放
    BUTTON_LONG_PRESS,      // 长按
    BUTTON_DOUBLE_CLICK,    // 双击
};
```

## LE Audio 音频流处理

### 音频流架构

OpenEarable基于Nordic的nRF5340 Audio应用，支持完整的LE Audio协议栈。

#### 音频流类型

```cpp
// 音频流类型
enum audio_stream_type {
    STREAM_TYPE_CIS,        // Connected Isochronous Stream (单播)
    STREAM_TYPE_BIS,        // Broadcast Isochronous Stream (广播)
};

// 音频配置参数
struct audio_config {
    uint32_t sample_rate_hz;    // 采样率
    uint8_t channels;           // 声道数
    uint16_t frame_duration_us; // 帧长度
    uint8_t codec_type;         // 编解码器类型
    uint32_t bitrate_bps;       // 比特率
};
```

#### 编解码器支持

```cpp
// 支持的编解码器
enum audio_codec {
    CODEC_LC3,              // LC3 (LE Audio标准)
    CODEC_SBC,              // SBC (经典蓝牙)
    CODEC_PCM,              // 未压缩PCM
};

// LC3编解码器配置
struct lc3_config {
    uint32_t sample_rate;       // 采样率 (8000, 16000, 24000, 32000, 48000)
    uint16_t frame_duration;    // 帧长度 (7.5ms, 10ms)
    uint8_t channels;           // 声道数 (1, 2)
    uint32_t bitrate;           // 比特率 (16000-320000 bps)
};
```

## 连接管理

### 配对和绑定

```cpp
// 配对状态管理
enum pairing_state {
    SET_PAIRING,        // 设置配对模式
    BONDING,           // 正在绑定
    PAIRED,            // 已配对
    CONNECTED,         // 已连接
};

// 连接参数
struct connection_params {
    uint16_t interval_min;      // 最小连接间隔
    uint16_t interval_max;      // 最大连接间隔
    uint16_t latency;          // 从设备延迟
    uint16_t timeout;          // 超时时间
};
```

### 安全管理

```cpp
// 安全参数
struct security_params {
    uint8_t auth_req;           // 认证要求
    uint8_t oob_flag;          // OOB数据标志
    uint8_t min_key_size;      // 最小密钥长度
    uint8_t max_key_size;      // 最大密钥长度
    uint8_t init_key_dist;     // 初始密钥分发
    uint8_t resp_key_dist;     // 响应密钥分发
};

// SIRK (Set Identity Resolving Key) 管理
uint32_t uicr_sirk_get(void);          // 获取SIRK
int uicr_sirk_set(uint32_t sirk);      // 设置SIRK
```

## 数据传输优化

### 数据分包传输

```cpp
// 大数据包分包传输
struct data_packet {
    uint8_t packet_id;          // 包ID
    uint8_t total_packets;      // 总包数
    uint8_t sequence;           // 序列号
    uint16_t data_size;         // 数据大小
    uint8_t data[];             // 数据载荷
} __attribute__((packed));

// 分包传输控制
int send_large_data(const uint8_t *data, size_t size, 
                   uint16_t mtu_size);
```

### 流量控制

```cpp
// 流量控制参数
struct flow_control {
    uint16_t window_size;       // 窗口大小
    uint16_t credit_count;      // 信用计数
    bool flow_enabled;          // 流控使能
};

// 自适应流控
void adaptive_flow_control(uint16_t buffer_level) {
    if (buffer_level > HIGH_THRESHOLD) {
        // 缓冲区满，减少发送速率
        reduce_transmission_rate();
    } else if (buffer_level < LOW_THRESHOLD) {
        // 缓冲区空，增加发送速率
        increase_transmission_rate();
    }
}
```

## 功耗优化

### 连接间隔优化

```cpp
// 动态连接间隔调整
void optimize_connection_interval() {
    if (high_data_rate_required()) {
        // 高数据传输需求，使用短连接间隔
        set_connection_interval(7.5); // 7.5ms
    } else {
        // 低功耗需求，使用长连接间隔
        set_connection_interval(100);  // 100ms
    }
}
```

### 广告功耗管理

```cpp
// 广告参数优化
struct adv_params {
    uint16_t interval_min;      // 最小广告间隔
    uint16_t interval_max;      // 最大广告间隔
    uint8_t type;              // 广告类型
    uint8_t tx_power;          // 发射功率
};

// 自适应广告
void adaptive_advertising() {
    if (battery_low()) {
        // 低电量时减少广告频率
        set_adv_interval(1000);  // 1秒
        set_tx_power(-20);       // 降低发射功率
    } else {
        // 正常电量时正常广告
        set_adv_interval(100);   // 100ms
        set_tx_power(0);         // 标准发射功率
    }
}
```

## 错误处理和恢复

### 连接错误处理

```cpp
// 连接错误类型
enum connection_error {
    CONN_ERR_TIMEOUT,           // 连接超时
    CONN_ERR_AUTH_FAILED,       // 认证失败
    CONN_ERR_PARAM_INVALID,     // 参数无效
    CONN_ERR_RESOURCES,         // 资源不足
};

// 错误恢复策略
void handle_connection_error(enum connection_error error) {
    switch (error) {
        case CONN_ERR_TIMEOUT:
            // 超时错误，重新尝试连接
            restart_connection();
            break;
            
        case CONN_ERR_AUTH_FAILED:
            // 认证失败，清除配对信息
            clear_bonding_info();
            start_pairing_mode();
            break;
            
        case CONN_ERR_PARAM_INVALID:
            // 参数错误，使用默认参数
            reset_to_default_params();
            break;
            
        default:
            // 通用错误，重启蓝牙栈
            restart_bluetooth_stack();
            break;
    }
}
```

### 音频流错误处理

```cpp
// 音频流错误处理
void handle_audio_stream_error(int error_code) {
    if (error_code == AUDIO_UNDERRUN) {
        // 音频缓冲区下溢
        increase_buffer_size();
        adjust_presentation_delay();
    } else if (error_code == AUDIO_SYNC_LOST) {
        // 音频同步丢失
        reinitialize_audio_sync();
    }
}
```

## 配置选项

### Kconfig配置

```kconfig
# 蓝牙基础配置
CONFIG_BT=y
CONFIG_BT_PERIPHERAL=y
CONFIG_BT_CENTRAL=y
CONFIG_BT_GATT_CLIENT=y

# LE Audio配置
CONFIG_BT_AUDIO=y
CONFIG_BT_BAP_UNICAST_SERVER=y
CONFIG_BT_BAP_BROADCAST_SINK=y
CONFIG_LC3_CODEC=y

# GATT服务配置
CONFIG_BT_GATT_DYNAMIC_DB=y
CONFIG_BT_GATT_SERVICE_CHANGED=y

# 安全配置
CONFIG_BT_SMP=y
CONFIG_BT_PRIVACY=y
CONFIG_BT_RPA=y

# 音频配置
CONFIG_AUDIO_SAMPLE_RATE_48000=y
CONFIG_AUDIO_FRAME_DURATION_10MS=y
CONFIG_LC3_BITRATE_96000=y
```

### 服务配置

```cpp
// GATT服务配置
#define MAX_SENSOR_DATA_SIZE    256
#define MAX_RECORDING_NAME_LEN  32
#define BATTERY_UPDATE_INTERVAL K_SECONDS(30)
#define SENSOR_DATA_INTERVAL    K_MSEC(100)

// 连接配置
#define MIN_CONN_INTERVAL       6    // 7.5ms
#define MAX_CONN_INTERVAL       80   // 100ms
#define SLAVE_LATENCY          0
#define CONN_SUP_TIMEOUT       400   // 4s
```

## 性能监控

### 连接质量监控

```cpp
// 连接质量统计
struct connection_stats {
    uint32_t packets_sent;          // 发送包数
    uint32_t packets_received;      // 接收包数
    uint32_t packets_lost;          // 丢包数
    float rssi_average;             // 平均RSSI
    uint16_t connection_interval;   // 连接间隔
    uint16_t slave_latency;         // 从设备延迟
};

// 质量监控
void monitor_connection_quality() {
    struct connection_stats stats;
    get_connection_stats(&stats);
    
    // 计算丢包率
    float packet_loss_rate = (float)stats.packets_lost / 
                            (stats.packets_sent + stats.packets_lost);
    
    // 信号质量评估
    if (stats.rssi_average < -80 || packet_loss_rate > 0.05) {
        LOG_WRN("Poor connection quality detected");
        optimize_connection_params();
    }
}
```

## 总结

蓝牙通信模块是OpenEarable 2.0的重要组成部分，具有以下特点：

1. **完整的LE Audio支持**: 基于最新的LE Audio标准，支持高质量音频传输
2. **丰富的GATT服务**: 提供传感器、电池、LED、按键等完整的设备控制接口
3. **高效数据传输**: 优化的数据分包和流量控制机制
4. **智能功耗管理**: 自适应的连接参数和广告策略
5. **可靠的错误处理**: 完善的错误检测和恢复机制
6. **安全通信**: 支持配对、绑定和加密通信
7. **性能监控**: 实时的连接质量监控和优化

该模块为OpenEarable 2.0提供了稳定可靠的无线通信能力，支持高质量音频播放、丰富的传感器数据传输和完整的设备控制功能。
