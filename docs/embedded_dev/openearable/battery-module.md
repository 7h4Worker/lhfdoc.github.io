# 电源管理模块详细分析

## 模块概述

电源管理模块是OpenEarable 2.0的核心组件之一，负责整个系统的电源状态管理、电池监控、充电控制等功能。该模块采用了双芯片架构，通过BQ27220燃料计量芯片和BQ25120a充电管理芯片实现完整的电源解决方案。

## 文件结构

```
src/Battery/
├── PowerManager.h/.cpp    # 电源管理器主类
├── BQ27220.h/.cpp        # 燃料计量芯片驱动
├── BQ25120a.h/.cpp       # 充电管理芯片驱动
├── BootState.h/.c        # 启动状态管理
├── CMakeLists.txt        # 构建配置
└── Kconfig              # 配置选项
```

## 核心类分析

### 1. PowerManager 类

PowerManager是电源管理的核心类，负责协调各个电源组件的工作。

#### 主要功能

- **系统电源控制**: 开关机、重启等
- **充电状态监控**: 实时监控充电状态变化
- **电池状态管理**: 电量、健康状态、温度等
- **电源异常处理**: 低电量保护、充电故障处理
- **LED状态指示**: 通过LED显示电源状态

#### 关键方法

```cpp
class PowerManager {
public:
    int begin();                    // 初始化电源管理器
    int power_down(bool fault);     // 系统关机
    void reboot();                  // 系统重启
    
    // 状态查询接口
    void get_battery_status(battery_level_status &status);
    void get_energy_status(battery_energy_status &status);
    void get_health_status(battery_health_status &status);
    
    void set_error_led(int val);    // 错误LED控制
};
```

#### 工作队列架构

PowerManager使用Zephyr的工作队列系统实现异步任务处理：

```cpp
// 延迟工作队列定义
K_WORK_DELAYABLE_DEFINE(PowerManager::charge_ctrl_delayable, charge_ctrl_work_handler);
K_WORK_DELAYABLE_DEFINE(PowerManager::power_down_work, power_down_work_handler);

// 即时工作队列定义
K_WORK_DEFINE(PowerManager::fuel_gauge_work, fuel_gauge_work_handler);
K_WORK_DEFINE(PowerManager::battery_controller_work, battery_controller_work_handler);
```

#### 中断处理机制

```cpp
// 燃料计量芯片中断处理
void fuel_gauge_callback(const struct device *dev, struct gpio_callback *cb, uint32_t pins);

// 充电控制芯片中断处理
void battery_controller_callback(const struct device *dev, struct gpio_callback *cb, uint32_t pins);

// 电源连接状态中断处理
void power_good_callback(const struct device *dev, struct gpio_callback *cb, uint32_t pins);
```

### 2. BQ27220 燃料计量芯片驱动

BQ27220是德州仪器(TI)的单节锂离子电池燃料计量芯片，提供精确的电池状态信息。

#### 主要功能

- **电池状态监控**: 电压、电流、温度、电量百分比
- **电池健康评估**: 循环次数、健康状态、剩余容量
- **安全保护**: 过压、欠压、过温保护
- **校准功能**: 支持电池容量校准

#### 寄存器定义

```cpp
enum registers : uint8_t {
    CTRL = 0x00,        // 控制寄存器
    TEMP = 0x06,        // 温度寄存器
    VOLT = 0x08,        // 电压寄存器
    AI = 0x14,          // 平均电流寄存器
    FLAGS = 0x0A,       // 状态标志寄存器
    NAC = 0x0C,         // 标称可用容量
    FCC = 0x12,         // 满充容量
    SOC = 0x2C,         // 电量百分比
    SOH = 0x2E,         // 健康状态
};
```

#### 电池状态结构

```cpp
struct bat_status {
    bool DSG;           // 放电状态
    bool SYSDWN;        // 系统关机电压
    bool TDA;           // 温度数据可用
    bool BATTPRES;      // 电池存在
    bool AUTH_GD;       // 认证良好
    bool OCVGD;         // 开路电压良好
    bool TCA;           // 温度补偿可用
    bool CHGINH;        // 充电禁止
    bool FC;            // 充电完成
    bool OTD;           // 放电过温
    bool OTC;           // 充电过温
    bool SLEEP;         // 睡眠模式
    bool OCVFAIL;       // 开路电压失败
    bool OCVCOMP;       // 开路电压补偿
    bool FD;            // 完全放电
};
```

#### 关键方法

```cpp
class BQ27220 {
public:
    int begin();                          // 初始化芯片
    float voltage();                      // 读取电压
    float current();                      // 读取电流
    float temperature();                  // 读取温度
    float state_of_charge();              // 读取电量百分比
    float state_of_health();              // 读取健康状态
    
    bat_status battery_status();          // 读取电池状态
    gauge_status gauging_state();         // 读取计量状态
    
    int calibration_enter();              // 进入校准模式
    int calibration_exit();               // 退出校准模式
    int config_update_enter();            // 进入配置更新模式
    int config_update_exit();             // 退出配置更新模式
};
```

### 3. BQ25120a 充电管理芯片驱动

BQ25120a是TI的低功耗线性充电管理芯片，专为便携式设备设计。

#### 主要功能

- **充电控制**: 恒流/恒压充电，充电电流可调
- **电源路径管理**: 支持边充边用
- **按键检测**: 集成按键检测功能
- **负载开关**: 集成LDO和负载开关
- **安全保护**: 过压、过流、过温保护

#### 寄存器定义

```cpp
enum registers : uint8_t {
    CTRL = 0x00,            // 控制寄存器
    FAULT = 0x01,           // 故障状态寄存器
    TS_FAULT = 0x02,        // 温度传感器故障寄存器
    CHARGE_CTRL = 0x03,     // 充电控制寄存器
    TERM_CTRL = 0x04,       // 终止控制寄存器
    BAT_VOL_CTRL = 0x05,    // 电池电压控制寄存器
    LS_LDO_CTRL = 0x07,     // 负载开关/LDO控制寄存器
    BTN_CTRL = 0x08,        // 按键控制寄存器
    ILIM_UVLO = 0x09        // 输入限流/欠压锁定寄存器
};
```

#### 充电状态结构

```cpp
struct chrg_state {
    float mAh;              // 充电电流(mA)
    bool enabled;           // 充电使能
    bool high_impedance;    // 高阻抗模式
};

struct button_state {
    bool wake_1;            // 唤醒按键1状态
    bool wake_2;            // 唤醒按键2状态
};
```

#### 关键方法

```cpp
class BQ25120a {
public:
    int begin();                              // 初始化芯片
    
    // 电源控制
    bool power_connected();                   // 检测电源连接
    void enter_high_impedance();             // 进入高阻抗模式
    void exit_high_impedance();              // 退出高阻抗模式
    
    // 充电控制
    void disable_charge();                    // 禁用充电
    void enable_charge();                     // 使能充电
    uint8_t read_charging_state();            // 读取充电状态
    
    // 故障检测
    uint8_t read_fault();                     // 读取故障状态
    uint8_t read_ts_fault();                  // 读取温度传感器故障
    
    // 按键检测
    button_state read_button_state();         // 读取按键状态
    
    // 回调设置
    int set_power_connect_callback(gpio_callback_handler_t handler);
    int set_int_callback(gpio_callback_handler_t handler);
};
```

## 电源管理状态机

### 充电状态定义

```cpp
enum charging_state {
    DISCHARGING,        // 放电状态
    POWER_CONNECTED,    // 电源已连接
    PRECHARGING,        // 预充电状态
    CHARGING,           // 正在充电
    TRICKLE_CHARGING,   // 涓流充电
    FULLY_CHARGED,      // 充电完成
    BATTERY_LOW,        // 电池低电量
    BATTERY_CRITICAL,   // 电池严重低电量
    FAULT               // 故障状态
};
```

### 状态转换逻辑

```cpp
void PowerManager::charge_task() {
    // 读取充电状态
    uint16_t charging_state = battery_controller.read_charging_state() >> 6;
    
    switch (charging_state) {
        case 0: // 放电状态
            msg.charging_state = DISCHARGING;
            
            // 检查低电量状态
            gauge_status gs = fuel_gauge.gauging_state();
            if (gs.edv2) msg.charging_state = BATTERY_LOW;
            if (gs.edv1) msg.charging_state = BATTERY_CRITICAL;
            break;
            
        case 1: // 充电状态
            // 检查系统关机电压
            if (bat.SYSDWN) {
                msg.charging_state = PRECHARGING;
                break;
            }
            
            // 分析充电参数
            float current = fuel_gauge.current();
            float target_current = fuel_gauge.charge_current();
            float voltage = fuel_gauge.voltage();
            
            // 判断具体充电阶段
            if (current > 0.8 * target_current - 2 * i_term) {
                msg.charging_state = CHARGING;
            } else if (voltage > u_term - 0.02) {
                msg.charging_state = TRICKLE_CHARGING;
            }
            break;
            
        case 2: // 充电完成
            msg.charging_state = FULLY_CHARGED;
            break;
            
        case 3: // 故障状态
            msg.charging_state = FAULT;
            break;
    }
}
```

## LED状态指示

### 充电状态LED

| LED状态 | 描述 |
|---------|------|
| 🟥 红色常亮 | 电池故障或深度放电 |
| 🔴 红色脉冲 | 预充电阶段 |
| 🟧 橙色常亮 | 电源连接，充电电流未达到目标 |
| 🟠 橙色脉冲 | 充电电流达到目标的80% |
| 🟢 绿色脉冲 | 涓流充电 |
| 🟩 绿色常亮 | 充电完成 |

### 放电状态LED

| LED状态 | 描述 |
|---------|------|
| 🟠 橙色闪烁 | 电池低电量(7%剩余) |
| 🔴 红色闪烁 | 电池严重低电量(3%剩余) |

## 配置参数

### 电池参数配置

```cpp
struct battery_settings {
    uint16_t capacity_mAh;      // 电池容量(mAh)
    uint16_t nominal_voltage_mV; // 标称电压(mV)
    uint16_t max_voltage_mV;    // 最大电压(mV)
    uint16_t charge_current_mA; // 充电电流(mA)
    uint16_t taper_current_mA;  // 涓流充电电流(mA)
    float u_term;               // 终止电压(V)
    float i_term;               // 终止电流(mA)
};
```

### Kconfig配置选项

```kconfig
CONFIG_BATTERY_CHARGE_CONTROLLER_NORMAL_INTERVAL_SECONDS=5
CONFIG_BATTERY_ENABLE_LOW_STATE=y
CONFIG_BATTERY_ENABLE_TRICKLE_CHARGE=y
```

## 消息总线集成

电源管理模块使用Zephyr的ZBus消息总线与其他模块通信：

```cpp
// 定义电池数据通道
ZBUS_CHAN_DEFINE(battery_chan, struct battery_data, NULL, NULL, 
                 ZBUS_OBSERVERS_EMPTY, ZBUS_MSG_INIT(0));

// 电池数据结构
struct battery_data {
    float battery_level;        // 电量百分比
    enum charging_state charging_state; // 充电状态
};
```

## 错误处理机制

### 故障检测

```cpp
void PowerManager::handle_fault(uint8_t fault_code) {
    // 设置错误LED
    set_error_led(1);
    
    // 记录故障信息
    LOG_ERR("Battery fault detected: 0x%02X", fault_code);
    
    // 根据故障类型采取措施
    switch (fault_code) {
        case OVER_TEMP_FAULT:
            disable_charging();
            break;
        case OVER_VOLTAGE_FAULT:
            emergency_shutdown();
            break;
        // ... 其他故障处理
    }
}
```

### 低电量保护

```cpp
void PowerManager::check_low_battery() {
    if (power_on && battery_status.SYSDWN) {
        LOG_WRN("Battery reached system down voltage.");
        k_work_reschedule(&power_down_work, K_NO_WAIT);
    }
}
```

## 性能优化

### 功耗优化
- 使用高阻抗模式减少待机功耗
- 动态调整监控间隔
- 智能电源路径管理

### 精度优化
- 电池参数校准
- 温度补偿
- 老化补偿算法

## 总结

电源管理模块通过双芯片架构实现了完整的电源解决方案，具有以下特点：

1. **完整的电源状态监控**: 电量、电压、电流、温度等参数实时监控
2. **智能充电管理**: 支持多阶段充电和各种保护功能
3. **用户友好的状态指示**: 通过LED直观显示电源状态
4. **系统集成友好**: 通过消息总线与其他模块通信
5. **安全可靠**: 多重保护机制确保系统安全

该模块为OpenEarable 2.0提供了稳定可靠的电源基础，支持长时间运行和安全的充电体验。
