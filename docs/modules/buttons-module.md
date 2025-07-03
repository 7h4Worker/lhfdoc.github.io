# OpenEarable 2.0 - 按键模块 (Buttons Module)

## 概述

按键模块负责处理OpenEarable设备上的物理按键输入，包括按键事件检测、防抖处理、状态管理和事件分发。该模块为用户提供交互接口，支持播放/暂停、音量控制等功能。

## 核心组件

### 1. Button 类 (`Button.h/cpp`)

主要的按键抽象类，处理单个按键的完整生命周期：

#### 核心接口
```cpp
class Button {
public:
    Button(gpio_dt_spec spec);
    void begin();                    // 初始化按键
    void end();                      // 清理按键资源
    button_action getState() const;  // 获取当前状态

private:
    k_work_delayable button_work;    // 延时工作队列
    const struct gpio_dt_spec button; // GPIO规格
    static struct gpio_callback button_cb_data; // 中断回调数据
    button_action _buttonState;      // 当前状态
    button_action _temp_buttonState; // 临时状态
    
    static void button_isr(const struct device *dev, struct gpio_callback *cb, uint32_t pins);
    int update_state();
    static void button_work_handler(struct k_work * work);
};
```

#### 状态管理
- **BUTTON_RELEASED**: 按键释放状态
- **BUTTON_PRESS**: 按键按下状态
- 使用防抖机制避免误触发

#### 防抖机制
```cpp
#define BUTTON_DEBOUNCE K_MSEC(10)  // 10ms防抖延时
```

- 中断触发时启动延时工作
- 延时结束后确认状态变化
- 状态未变化时取消延时工作

### 2. 按键管理器 (`button_manager.h/c`)

负责按键事件的消息队列管理和事件分发：

#### 消息队列
```c
K_MSGQ_DEFINE(button_queue, sizeof(struct button_msg), 1, 4);
```

#### ZBus 通道
```c
ZBUS_CHAN_DEFINE(button_chan, struct button_msg, NULL, NULL, ZBUS_OBSERVERS_EMPTY,
                 ZBUS_MSG_INIT(0));
```

#### 发布线程
```c
void button_pub_task() {
    int ret;
    struct button_msg msg;
    
    while (1) {
        k_msgq_get(&button_queue, &msg, K_FOREVER);
        ret = zbus_chan_pub(&button_chan, &msg, K_FOREVER);
        if (ret) {
            LOG_ERR("Failed to publish button msg, ret: %d", ret);
        }
    }
}

K_THREAD_DEFINE(button_publish, CONFIG_BUTTON_PUBLISH_STACK_SIZE, button_pub_task, 
                NULL, NULL, NULL, K_PRIO_PREEMPT(CONFIG_BUTTON_PUBLISH_THREAD_PRIO), 0, 0);
```

### 3. 按键分配 (`button_assignments.h`)

定义按键映射和枚举：

```cpp
enum button_pin_names {
    BUTTON_EARABLE = DT_GPIO_PIN(DT_ALIAS(sw0), gpios),
    BUTTON_VOLUME_UP,       // 预留
    BUTTON_VOLUME_DOWN,     // 预留
    BUTTON_4,               // 预留
    BUTTON_5,               // 预留
};

#define BUTTON_PLAY_PAUSE BUTTON_EARABLE  // 别名定义
```

### 4. 按键状态查询 (`button_pressed.cpp`)

提供按键状态查询接口：

```cpp
int button_pressed(enum button_pin_names pin, bool * pressed) {
    switch (pin) {
        case BUTTON_EARABLE:
            *pressed = (earable_btn.getState() == BUTTON_PRESS);
            return 0;
        default:
            *pressed = false;
            return 0;
    }
}
```

## 工作流程

### 1. 初始化流程
```
Button构造 → GPIO配置 → 中断配置 → 回调注册 → 初始状态读取
```

### 2. 按键事件处理流程
```
GPIO中断触发 → button_isr() → 启动延时工作 → button_work_handler() → 
update_state() → 消息入队 → button_pub_task() → ZBus发布
```

### 3. 防抖处理
```
中断触发 → 读取临时状态 → 
如果状态相同 → 取消延时工作
如果状态不同 → 重新调度延时工作 → 延时后确认状态变化
```

## 硬件接口

### GPIO 配置
- 使用设备树别名 `sw0` 定义主按键
- 配置为输入模式 (`GPIO_INPUT`)
- 启用双边沿中断 (`GPIO_INT_EDGE_BOTH`)

### 中断处理
- 共享中断回调函数 `button_isr`
- 支持多按键扩展（当前仅实现主按键）
- 中断安全的状态更新

## 配置选项

### Kconfig 配置
```
CONFIG_BUTTON_PUBLISH_STACK_SIZE    # 发布线程栈大小
CONFIG_BUTTON_PUBLISH_THREAD_PRIO   # 发布线程优先级
CONFIG_MODULE_BUTTON_HANDLER_LOG_LEVEL  # 日志级别
```

### 设备树配置
```dts
aliases {
    sw0 = &button0;  // 主按键别名
};
```

## 扩展性设计

### 多按键支持
- 代码中预留了多个按键的实现框架
- 可通过取消注释轻松添加音量按键等
- 支持不同按键的独立处理

### 按键功能映射
- 通过 `button_assignments.h` 集中管理按键功能
- 支持别名定义，便于功能重映射
- 可扩展复杂按键组合功能

## 集成接口

### ZBus 消息
```cpp
struct button_msg {
    uint32_t button_pin;        // 按键引脚
    button_action button_action; // 按键动作
};
```

### 订阅者接口
其他模块可通过ZBus订阅按键事件：
```c
ZBUS_SUBSCRIBER_DEFINE(button_sub, 1);
ZBUS_CHAN_ADD_OBS(button_chan, button_sub, 0);
```

## 日志和调试

### 日志模块
```c
LOG_MODULE_REGISTER(button, CONFIG_MODULE_BUTTON_HANDLER_LOG_LEVEL);
```

### 关键日志点
- 按键状态变化记录
- 消息队列满警告
- GPIO配置错误
- 中断配置失败

## 功耗优化

### 中断驱动
- 使用GPIO中断而非轮询
- 按键空闲时零功耗
- 中断唤醒系统

### 工作队列优化
- 使用延时工作队列进行防抖
- 避免持续CPU占用
- 适当的线程优先级配置

## 错误处理

### GPIO 错误
- 设备就绪检查
- 引脚配置失败处理
- 中断配置错误处理

### 消息队列错误
- 队列满时的警告日志
- 发布失败的错误处理
- 资源竞争保护

## 典型使用场景

### 1. 播放/暂停控制
```cpp
// 在音频模块中订阅按键事件
void audio_button_handler(const struct zbus_channel *chan) {
    struct button_msg msg;
    zbus_chan_read(chan, &msg, K_FOREVER);
    
    if (msg.button_pin == BUTTON_EARABLE && msg.button_action == BUTTON_PRESS) {
        // 执行播放/暂停逻辑
        toggle_playback();
    }
}
```

### 2. 系统状态切换
```cpp
// 在状态管理模块中处理按键
void state_button_handler(const struct zbus_channel *chan) {
    struct button_msg msg;
    zbus_chan_read(chan, &msg, K_FOREVER);
    
    if (msg.button_pin == BUTTON_EARABLE && msg.button_action == BUTTON_PRESS) {
        // 状态切换或功能激活
        switch_system_state();
    }
}
```

## 总结

按键模块提供了完整的物理按键交互支持，具有以下特点：

1. **可靠性**: 硬件防抖和软件状态确认
2. **扩展性**: 支持多按键和复杂功能映射
3. **高效性**: 中断驱动和事件发布机制
4. **集成性**: 通过ZBus与其他模块无缝集成
5. **低功耗**: 中断唤醒和适当的线程调度

该模块为OpenEarable设备的用户交互提供了稳定可靠的基础设施。
