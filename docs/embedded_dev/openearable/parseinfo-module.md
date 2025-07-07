# OpenEarable 2.0 - 数据解析模块 (ParseInfo Module)

## 概述

数据解析模块负责定义和管理传感器数据的解析方案，为蓝牙通信提供传感器配置信息和数据格式描述。该模块通过标准化的数据结构定义，使客户端能够正确解析和处理来自OpenEarable设备的传感器数据。

## 核心组件

### 1. 传感器方案 (`SensorScheme.h/cpp`)

定义传感器的完整配置和解析方案：

#### 核心数据结构
```cpp
struct SensorScheme {
    const char* name;                       // 传感器名称
    uint8_t id;                            // 传感器ID
    uint8_t groupCount;                    // 组件组数量
    struct SensorComponentGroup* groups;   // 组件组数组
    struct SensorConfigOptions configOptions;  // 配置选项
};

struct ParseInfoScheme {
    uint8_t sensorCount;        // 传感器数量
    uint8_t* sensorIds;         // 传感器ID数组
};
```

#### 配置选项
```cpp
enum SensorConfigOptionsMasks {
    DATA_STREAMING = 0x01,      // 支持数据流传输
    DATA_STORAGE = 0x02,        // 支持数据存储
    FREQUENCIES_DEFINED = 0x10, // 定义了频率选项
};

struct FrequencyOptions {
    uint8_t frequencyCount;         // 频率选项数量
    uint8_t defaultFrequencyIndex;  // 默认频率索引
    uint8_t maxBleFrequencyIndex;   // 最大蓝牙频率索引
    const float* frequencies;       // 频率数组
};

struct SensorConfigOptions {
    uint8_t availableOptions;              // 可用选项掩码
    struct FrequencyOptions frequencyOptions;  // 频率选项
};
```

#### 核心接口
```cpp
int initParseInfoService(struct ParseInfoScheme* scheme, struct SensorScheme* sensorSchemes);
struct SensorScheme* getSensorSchemeForId(uint8_t id);
struct ParseInfoScheme* getParseInfoScheme();
float getSampleRateForSensorId(uint8_t id, uint8_t frequencyIndex);
float getSampleRateForSensor(struct SensorScheme* sensorScheme, uint8_t frequencyIndex);
```

### 2. 传感器组件 (`SensorComponent.h/cpp`)

定义传感器数据的组件结构：

#### 基本组件
```cpp
struct SensorComponent {
    const char* name;           // 组件名称 (如 "x", "y", "z")
    const char* unit;           // 单位 (如 "m/s²", "°/s")
    enum ParseType parseType;   // 数据类型
};
```

#### 组件组
```cpp
struct SensorComponentGroup {
    const char* name;                      // 组名称 (如 "Accelerometer")
    size_t componentCount;                 // 组件数量
    struct SensorComponent* components;    // 组件数组
};
```

#### 序列化接口
```cpp
size_t getSensorComponentGroupSize(struct SensorComponentGroup* group);
ssize_t serializeSensorComponentGroup(struct SensorComponentGroup* group, 
                                    char* buffer, size_t bufferSize);
```

### 3. 数据类型定义 (`ParseType.h`)

定义支持的数据解析类型：

```cpp
enum ParseType {
    PARSE_TYPE_INT8,     // 8位有符号整数
    PARSE_TYPE_UINT8,    // 8位无符号整数
    PARSE_TYPE_INT16,    // 16位有符号整数
    PARSE_TYPE_UINT16,   // 16位无符号整数
    PARSE_TYPE_INT32,    // 32位有符号整数
    PARSE_TYPE_UINT32,   // 32位无符号整数
    PARSE_TYPE_FLOAT,    // 32位浮点数
    PARSE_TYPE_DOUBLE,   // 64位双精度浮点数
};

const int parseTypeSizes[] = {
    1,  // INT8/UINT8
    1,
    2,  // INT16/UINT16
    2,
    4,  // INT32/UINT32
    4,
    4,  // FLOAT
    8,  // DOUBLE
};
```

### 4. 默认传感器定义 (`DefaultSensors.h`)

预定义常用传感器的配置方案（具体实现可能在相应的.cpp文件中）。

## 蓝牙服务集成

### GATT 服务定义
```cpp
#define BT_UUID_PARSE_INFO_SERVICE_VAL \
    BT_UUID_128_ENCODE(0xcaa25cb7, 0x7e1b, 0x44f2, 0xadc9, 0xe8c06c9ced43)

#define BT_UUID_PARSE_INFO_CHARAC_VAL \
    BT_UUID_128_ENCODE(0xcaa25cb9, 0x7e1b, 0x44f2, 0xadc9, 0xe8c06c9ced43)

#define BT_UUID_PARSE_INFO_REQUEST_CHARAC_VAL \
    BT_UUID_128_ENCODE(0xcaa25cba, 0x7e1b, 0x44f2, 0xadc9, 0xe8c06c9ced43)

#define BT_UUID_PARSE_INFO_RESPONSE_CHARAC_VAL \
    BT_UUID_128_ENCODE(0xcaa25cbb, 0x7e1b, 0x44f2, 0xadc9, 0xe8c06c9ced43)
```

### 特性功能
- **Parse Info Service**: 主服务
- **Parse Info Characteristic**: 基本解析信息
- **Request Characteristic**: 客户端请求特定传感器信息
- **Response Characteristic**: 服务器响应传感器配置

## 典型传感器配置示例

### IMU 传感器方案
```cpp
// 加速度计组件
struct SensorComponent accel_components[] = {
    {"x", "m/s²", PARSE_TYPE_FLOAT},
    {"y", "m/s²", PARSE_TYPE_FLOAT},
    {"z", "m/s²", PARSE_TYPE_FLOAT}
};

struct SensorComponentGroup accel_group = {
    "Accelerometer",
    3,
    accel_components
};

// 陀螺仪组件
struct SensorComponent gyro_components[] = {
    {"x", "°/s", PARSE_TYPE_FLOAT},
    {"y", "°/s", PARSE_TYPE_FLOAT},
    {"z", "°/s", PARSE_TYPE_FLOAT}
};

struct SensorComponentGroup gyro_group = {
    "Gyroscope",
    3,
    gyro_components
};

// 频率选项
const float imu_frequencies[] = {1.0f, 10.0f, 25.0f, 50.0f, 100.0f};
struct FrequencyOptions imu_freq_options = {
    5,      // 5个频率选项
    2,      // 默认25Hz (索引2)
    3,      // 蓝牙最大50Hz (索引3)
    imu_frequencies
};

// IMU传感器方案
struct SensorComponentGroup imu_groups[] = {accel_group, gyro_group};
struct SensorScheme imu_scheme = {
    "IMU",
    SENSOR_ID_IMU,
    2,      // 2个组件组
    imu_groups,
    {
        DATA_STREAMING | DATA_STORAGE | FREQUENCIES_DEFINED,
        imu_freq_options
    }
};
```

### PPG 传感器方案
```cpp
struct SensorComponent ppg_components[] = {
    {"raw", "counts", PARSE_TYPE_UINT32},
    {"heart_rate", "bpm", PARSE_TYPE_FLOAT}
};

struct SensorComponentGroup ppg_group = {
    "PPG",
    2,
    ppg_components
};

const float ppg_frequencies[] = {25.0f, 50.0f, 100.0f};
struct FrequencyOptions ppg_freq_options = {
    3, 1, 2,  // 3个选项，默认50Hz，蓝牙最大100Hz
    ppg_frequencies
};

struct SensorScheme ppg_scheme = {
    "PPG",
    SENSOR_ID_PPG,
    1,
    &ppg_group,
    {
        DATA_STREAMING | DATA_STORAGE | FREQUENCIES_DEFINED,
        ppg_freq_options
    }
};
```

## 数据序列化

### 组件组大小计算
```cpp
size_t getSensorComponentGroupSize(struct SensorComponentGroup* group) {
    size_t size = 0;
    
    // 组名长度 + 组件数量
    size += strlen(group->name) + 1 + sizeof(group->componentCount);
    
    // 每个组件的信息
    for (size_t i = 0; i < group->componentCount; i++) {
        size += strlen(group->components[i].name) + 1;
        size += strlen(group->components[i].unit) + 1;
        size += sizeof(group->components[i].parseType);
    }
    
    return size;
}
```

### 序列化格式
```
[Group Name][Component Count]
  [Component 1 Name][Component 1 Unit][Component 1 Type]
  [Component 2 Name][Component 2 Unit][Component 2 Type]
  ...
```

## 初始化流程

### 1. 服务初始化
```cpp
int initParseInfoService(struct ParseInfoScheme* scheme, 
                        struct SensorScheme* sensorSchemes) {
    // 1. 存储传感器方案引用
    // 2. 初始化蓝牙GATT服务
    // 3. 注册特性回调函数
    // 4. 准备默认响应数据
    return 0;
}
```

### 2. 方案查询
```cpp
struct SensorScheme* getSensorSchemeForId(uint8_t id) {
    // 遍历已注册的传感器方案
    // 根据ID匹配并返回对应方案
    return matching_scheme;
}
```

## 客户端交互协议

### 1. 获取传感器列表
```
Client Request:  [REQUEST_SENSOR_LIST]
Server Response: [SENSOR_COUNT][SENSOR_ID_1][SENSOR_ID_2]...
```

### 2. 获取传感器配置
```
Client Request:  [REQUEST_SENSOR_CONFIG][SENSOR_ID]
Server Response: [SENSOR_NAME][GROUP_COUNT][GROUP_DATA...]
```

### 3. 获取频率选项
```
Client Request:  [REQUEST_FREQUENCIES][SENSOR_ID]
Server Response: [FREQ_COUNT][DEFAULT_INDEX][MAX_BLE_INDEX][FREQ_1][FREQ_2]...
```

## 内存管理

### 静态配置
- 传感器方案使用静态分配
- 组件定义存储在常量区域
- 避免运行时内存分配

### 缓冲区管理
- 序列化使用预分配缓冲区
- 防止缓冲区溢出检查
- 适当的错误处理

## 扩展性设计

### 新传感器添加
1. 定义传感器组件结构
2. 创建传感器方案
3. 在默认方案中注册
4. 更新传感器ID枚举

### 新数据类型支持
1. 扩展 `ParseType` 枚举
2. 更新 `parseTypeSizes` 数组
3. 修改序列化/反序列化逻辑

## 调试和验证

### 配置验证
- 检查组件数量一致性
- 验证频率选项有效性
- 确认数据类型支持

### 序列化测试
- 缓冲区大小验证
- 数据完整性检查
- 跨平台兼容性测试

## 总结

数据解析模块提供了完整的传感器数据格式定义和管理框架，具有以下特点：

1. **标准化**: 统一的数据格式定义和解析方案
2. **灵活性**: 支持多种数据类型和传感器配置
3. **可扩展**: 易于添加新传感器和数据类型
4. **高效性**: 静态配置和优化的序列化机制
5. **兼容性**: 蓝牙GATT服务集成和跨平台支持

该模块为OpenEarable设备的数据通信提供了可靠的格式化基础设施，确保客户端能够正确解析和处理传感器数据。
