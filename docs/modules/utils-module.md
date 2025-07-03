# OpenEarable 2.0 - 系统工具模块 (Utils Module)

## 概述

系统工具模块提供了OpenEarable设备的各种辅助功能和系统级工具，包括状态指示、板级支持、版本管理、错误处理等核心系统功能。该模块为整个系统提供了基础的支撑服务。

## 核心组件

### 1. 状态指示器 (`StateIndicator.h/cpp`)

负责通过LED显示设备的各种状态：

#### 核心类定义
```cpp
class StateIndicator {
public:
    void init(struct earable_state state);
    void set_state(struct earable_state state);
    void set_charging_state(enum charging_state state);
    void set_pairing_state(enum pairing_state state);
    void set_indication_mode(enum led_mode state);
    void set_custom_color(const RGBColor &color);

private:
    earable_state _state;
    RGBColor color;
};

extern StateIndicator state_indicator;
```

#### 预定义颜色
```cpp
static const RGBColor LED_OFF = {0, 0, 0};
static const RGBColor LED_RED = {32, 0, 0};
static const RGBColor LED_GREEN = {0, 32, 0};
static const RGBColor LED_BLUE = {0, 0, 32};
static const RGBColor LED_YELLOW = {16, 16, 0};
static const RGBColor LED_ORANGE = {24, 8, 0};
static const RGBColor LED_CYAN = {0, 16, 16};
static const RGBColor LED_MAGENTA = {16, 0, 16};
```

#### 状态映射
- **充电状态**: 红色（充电中）、绿色（充电完成）
- **配对状态**: 蓝色（配对模式）、青色（已连接）
- **系统状态**: 不同颜色组合表示各种工作模式
- **自定义模式**: 支持用户定义颜色

### 2. 板级支持

#### nRF5340开发板支持 (`nrf5340_audio_dk.h/c`)
```cpp
// 板级初始化
int board_init(void);

// 硬件配置
void configure_board_peripherals(void);

// 电源管理
void board_power_management_init(void);
```

#### OpenEarable板级支持 (`openearable.h/c`)
```cpp
// OpenEarable特定初始化
int openearable_board_init(void);

// 硬件抽象层
void openearable_configure_peripherals(void);

// 板级电源控制
void openearable_power_control(void);
```

### 3. 版本管理 (`board_version.h/c`)

提供硬件版本检测和管理：

```cpp
// 版本检测
enum board_version {
    BOARD_VERSION_UNKNOWN,
    BOARD_VERSION_1_0,
    BOARD_VERSION_2_0,
    BOARD_VERSION_2_1
};

// 核心接口
enum board_version get_board_version(void);
const char* get_board_version_string(void);
bool is_board_version_supported(enum board_version version);
```

#### 版本检测机制
- 通过GPIO引脚状态检测硬件版本
- 支持多种版本的兼容性处理
- 版本信息用于功能适配

### 4. 通道分配 (`channel_assignment.h/c`)

管理音频通道和数据流的分配：

```cpp
// 通道分配结构
struct channel_assignment {
    uint8_t left_channel;
    uint8_t right_channel;
    uint8_t stream_id;
};

// 核心接口
int channel_assignment_init(void);
int assign_audio_channel(uint8_t stream_id, uint8_t* left, uint8_t* right);
int release_audio_channel(uint8_t stream_id);
```

### 5. 固件信息 (`fw_info_app.h`)

提供固件版本和构建信息：

```cpp
// 固件信息结构
struct fw_info {
    uint32_t version_major;
    uint32_t version_minor;
    uint32_t version_patch;
    char build_date[16];
    char build_time[16];
    char git_commit[8];
};

// 接口函数
const struct fw_info* get_fw_info(void);
void print_fw_info(void);
```

### 6. 错误处理 (`error_handler.c`)

系统错误处理和恢复机制：

```cpp
// 错误类型定义
enum error_type {
    ERROR_HARDWARE,
    ERROR_MEMORY,
    ERROR_COMMUNICATION,
    ERROR_CONFIGURATION,
    ERROR_TIMEOUT
};

// 错误处理函数
void handle_error(enum error_type type, int error_code);
void register_error_callback(void (*callback)(enum error_type, int));
void system_recovery(void);
```

### 7. UICR管理 (`uicr.h/c`)

用户信息配置寄存器(UICR)管理：

```cpp
// UICR配置
struct uicr_config {
    uint32_t device_id;
    uint32_t hw_version;
    uint32_t production_date;
    uint8_t calibration_data[32];
};

// 接口函数
int uicr_init(void);
int uicr_read_config(struct uicr_config* config);
int uicr_write_config(const struct uicr_config* config);
bool uicr_is_programmed(void);
```

## 宏定义工具 (`macros/`)

### 通用宏定义
```cpp
// 位操作宏
#define BIT_SET(val, bit)    ((val) |= (1U << (bit)))
#define BIT_CLEAR(val, bit)  ((val) &= ~(1U << (bit)))
#define BIT_CHECK(val, bit)  (((val) >> (bit)) & 1U)

// 数组操作宏
#define ARRAY_SIZE(arr)      (sizeof(arr) / sizeof((arr)[0]))

// 数学宏
#define MIN(a, b)           (((a) < (b)) ? (a) : (b))
#define MAX(a, b)           (((a) > (b)) ? (a) : (b))
#define CLAMP(val, min, max) MIN(MAX(val, min), max)
```

### 调试宏
```cpp
#ifdef CONFIG_DEBUG
#define DEBUG_PRINT(fmt, ...) printk(fmt, ##__VA_ARGS__)
#define ASSERT(expr) do { \
    if (!(expr)) { \
        printk("ASSERT failed: %s:%d\n", __FILE__, __LINE__); \
        k_panic(); \
    } \
} while(0)
#else
#define DEBUG_PRINT(fmt, ...)
#define ASSERT(expr)
#endif
```

## 状态指示逻辑

### 1. 启动状态指示
```cpp
void indicate_boot_status(void) {
    // 白色闪烁 - 系统启动
    state_indicator.set_custom_color({16, 16, 16});
    k_sleep(K_MSEC(500));
    state_indicator.set_custom_color(LED_OFF);
}
```

### 2. 电池状态指示
```cpp
void indicate_battery_status(uint8_t level) {
    if (level > 80) {
        state_indicator.set_custom_color(LED_GREEN);    // 电量充足
    } else if (level > 30) {
        state_indicator.set_custom_color(LED_YELLOW);   // 电量中等
    } else if (level > 10) {
        state_indicator.set_custom_color(LED_ORANGE);   // 电量较低
    } else {
        state_indicator.set_custom_color(LED_RED);      // 电量极低
    }
}
```

### 3. 连接状态指示
```cpp
void indicate_connection_status(bool connected) {
    if (connected) {
        state_indicator.set_custom_color(LED_CYAN);     // 已连接
    } else {
        state_indicator.set_custom_color(LED_BLUE);     // 等待连接
    }
}
```

## 系统初始化流程

### 1. 板级初始化
```cpp
int system_init(void) {
    int ret;
    
    // 1. 基础板级初始化
    ret = board_init();
    if (ret) return ret;
    
    // 2. 版本检测
    enum board_version version = get_board_version();
    LOG_INF("Board version: %s", get_board_version_string());
    
    // 3. UICR初始化
    ret = uicr_init();
    if (ret) return ret;
    
    // 4. 通道分配初始化
    ret = channel_assignment_init();
    if (ret) return ret;
    
    // 5. 状态指示器初始化
    struct earable_state initial_state = {0};
    state_indicator.init(initial_state);
    
    return 0;
}
```

### 2. 外设配置
```cpp
void configure_peripherals(void) {
    // GPIO配置
    configure_gpio_pins();
    
    // I2C配置
    configure_i2c_interfaces();
    
    // SPI配置
    configure_spi_interfaces();
    
    // 电源域配置
    configure_power_domains();
}
```

## 错误处理策略

### 1. 错误分类处理
```cpp
void handle_error(enum error_type type, int error_code) {
    switch (type) {
        case ERROR_HARDWARE:
            // 硬件错误 - 记录并尝试重启硬件
            LOG_ERR("Hardware error: %d", error_code);
            reset_hardware_peripherals();
            break;
            
        case ERROR_MEMORY:
            // 内存错误 - 清理内存并重启
            LOG_ERR("Memory error: %d", error_code);
            cleanup_memory();
            system_restart();
            break;
            
        case ERROR_COMMUNICATION:
            // 通信错误 - 重置通信接口
            LOG_ERR("Communication error: %d", error_code);
            reset_communication_interfaces();
            break;
            
        default:
            LOG_ERR("Unknown error type: %d, code: %d", type, error_code);
            break;
    }
}
```

### 2. 系统恢复机制
```cpp
void system_recovery(void) {
    // 1. 保存关键状态
    save_critical_state();
    
    // 2. 重置外设
    reset_all_peripherals();
    
    // 3. 重新初始化
    system_init();
    
    // 4. 恢复关键状态
    restore_critical_state();
    
    // 5. 状态指示
    indicate_recovery_complete();
}
```

## 配置管理

### Kconfig 选项
```kconfig
# 调试选项
config UTILS_DEBUG
    bool "Enable utils module debug"
    default n

# 状态指示选项
config STATE_INDICATOR_BRIGHTNESS
    int "LED brightness level (0-255)"
    range 0 255
    default 32

# 版本检测选项
config BOARD_VERSION_DETECTION
    bool "Enable board version detection"
    default y

# 错误恢复选项
config ERROR_RECOVERY_ENABLED
    bool "Enable automatic error recovery"
    default y
```

### 设备树配置
```dts
/ {
    board_config {
        compatible = "openearable,board-config";
        version-gpio = <&gpio0 28 GPIO_ACTIVE_HIGH>;
        status-led = <&led_rgb>;
    };
};
```

## 性能监控

### 系统资源监控
```cpp
struct system_stats {
    uint32_t cpu_usage;
    uint32_t memory_usage;
    uint32_t stack_usage;
    uint32_t heap_free;
};

void get_system_stats(struct system_stats* stats) {
    // CPU使用率
    stats->cpu_usage = get_cpu_usage_percent();
    
    // 内存使用情况
    stats->memory_usage = get_memory_usage_bytes();
    stats->heap_free = get_heap_free_bytes();
    
    // 栈使用情况
    stats->stack_usage = get_stack_usage_bytes();
}
```

### 运行时统计
```cpp
void print_runtime_stats(void) {
    struct system_stats stats;
    get_system_stats(&stats);
    
    LOG_INF("System Stats:");
    LOG_INF("  CPU Usage: %u%%", stats.cpu_usage);
    LOG_INF("  Memory Usage: %u bytes", stats.memory_usage);
    LOG_INF("  Heap Free: %u bytes", stats.heap_free);
    LOG_INF("  Stack Usage: %u bytes", stats.stack_usage);
}
```

## 调试和诊断

### 诊断信息收集
```cpp
void collect_diagnostic_info(void) {
    // 固件信息
    const struct fw_info* fw = get_fw_info();
    LOG_INF("Firmware: v%u.%u.%u", fw->version_major, 
            fw->version_minor, fw->version_patch);
    
    // 硬件信息
    LOG_INF("Board: %s", get_board_version_string());
    
    // 系统状态
    print_runtime_stats();
    
    // UICR信息
    struct uicr_config uicr;
    if (uicr_read_config(&uicr) == 0) {
        LOG_INF("Device ID: 0x%08x", uicr.device_id);
        LOG_INF("HW Version: 0x%08x", uicr.hw_version);
    }
}
```

## 总结

系统工具模块提供了完整的系统支撑功能，具有以下特点：

1. **全面性**: 涵盖状态指示、版本管理、错误处理等各个方面
2. **可靠性**: 完善的错误处理和系统恢复机制
3. **可维护性**: 清晰的版本管理和诊断信息
4. **可配置性**: 丰富的配置选项和板级适配
5. **可观测性**: 完整的状态指示和运行时监控

该模块为OpenEarable设备提供了稳定可靠的系统基础设施，确保设备的正常运行和可维护性。
