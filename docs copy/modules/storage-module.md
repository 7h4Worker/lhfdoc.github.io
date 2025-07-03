# 数据存储模块详细分析

## 模块概述

数据存储模块负责OpenEarable 2.0的本地数据存储功能，主要通过SD卡实现传感器数据和音频数据的本地记录。该模块提供高效的数据缓冲、文件管理和存储优化功能。

## 文件结构

```
src/SD_Card/
├── SDLogger/               # SD卡数据记录器
│   ├── SDLogger.h/.cpp        # 主要日志记录类
│   └── CMakeLists.txt         # 构建配置
├── SD_Card_Manager/        # SD卡管理器
│   ├── SD_Card_Manager.h/.cpp # SD卡管理接口
│   └── CMakeLists.txt         # 构建配置
├── Benchmark/              # 性能测试
│   ├── Benchmark.h/.cpp       # 存储性能测试
│   └── CMakeLists.txt         # 构建配置
└── CMakeLists.txt          # 模块构建配置
```

## 核心组件

### 1. SDLogger - SD卡日志记录器

SDLogger是数据存储的核心组件，提供高效的传感器数据记录功能。

#### 主要特性

- **缓冲写入**: 使用环形缓冲区优化写入性能
- **块对齐**: 4KB块对齐确保最佳存储性能
- **文件格式**: 自定义二进制格式(.oe)优化存储效率
- **版本管理**: 文件头包含版本和时间戳信息

#### 缓冲架构

```cpp
class SDLogger {
private:
    static constexpr size_t SD_BLOCK_SIZE = 4096;      // SD卡块大小
    static constexpr size_t BUFFER_BLOCK_COUNT = 8;    // 缓冲区块数
    static constexpr size_t BUFFER_SIZE = SD_BLOCK_SIZE * BUFFER_BLOCK_COUNT; // 32KB缓冲区
    
    // 文件头结构
    struct __attribute__((packed)) FileHeader {
        uint16_t version;       // 文件格式版本
        uint64_t timestamp;     // 创建时间戳
    };
};
```

### 2. SD_Card_Manager - SD卡管理器

SD卡管理器提供SD卡的底层操作接口，包括挂载、卸载、文件系统管理等。

#### 主要功能

- **SD卡检测**: 自动检测SD卡插入和移除
- **文件系统管理**: FAT32文件系统支持
- **错误处理**: SD卡错误检测和恢复
- **性能监控**: 读写性能统计

### 3. 数据格式

#### 传感器数据格式

```cpp
// 传感器数据记录格式
struct sensor_log_entry {
    uint64_t timestamp;     // 时间戳 (微秒)
    uint8_t sensor_id;      // 传感器ID
    uint8_t data_size;      // 数据大小
    uint8_t data[];         // 传感器数据
} __attribute__((packed));
```

#### 文件格式结构

```
.oe文件格式:
+------------------+
| 文件头 (10字节)   |
| - 版本 (2字节)    |
| - 时间戳 (8字节)  |
+------------------+
| 传感器数据记录1   |
+------------------+
| 传感器数据记录2   |
+------------------+
| ...              |
+------------------+
```

## 性能优化

### 缓冲写入策略

```cpp
void SDLogger::write_sensor_data(const sensor_data* data) {
    // 1. 数据写入环形缓冲区
    ring_buffer_put(&sd_buffer, (uint8_t*)data, sizeof(sensor_data));
    
    // 2. 检查是否达到写入阈值
    if (ring_buffer_size_get(&sd_buffer) >= WRITE_THRESHOLD) {
        // 触发批量写入
        schedule_bulk_write();
    }
}
```

### 块对齐优化

```cpp
// 确保写入数据块对齐
static_assert(BUFFER_SIZE % SD_BLOCK_SIZE == 0, 
              "BUFFER_SIZE must be a multiple of SD_BLOCK_SIZE");
```

## 总结

数据存储模块为OpenEarable 2.0提供了高效可靠的本地数据存储功能，支持:

1. **高性能写入**: 缓冲和块对齐优化
2. **可靠存储**: 错误检测和恢复机制  
3. **标准格式**: 自定义二进制格式优化存储效率
4. **易于解析**: Python工具支持数据解析和分析

该模块确保了传感器数据的可靠本地存储，为离线数据分析和研究提供了重要支持。
