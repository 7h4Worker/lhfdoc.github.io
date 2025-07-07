# OpenEarable 2.0 - I2C通信模块 (Wire Module)

## 概述

I2C通信模块为OpenEarable设备提供了Arduino风格的I2C通信接口，基于Zephyr RTOS的I2C驱动实现。该模块封装了底层的I2C硬件操作，为上层驱动和应用提供了简洁易用的通信接口。

## 核心组件

### 1. Arduino风格I2C接口 (`Wire.h/cpp`)

提供与Arduino Wire库兼容的I2C接口：

#### 核心类定义
```cpp
class MbedI2C {
public:
    MbedI2C(const struct device * master);
    
    // 基本操作
    virtual void begin(uint32_t speed = I2C_SPEED_FAST);
    virtual void end();
    virtual void setClock(uint32_t freq);
    
    // 传输操作
    virtual void beginTransmission(uint8_t address);
    virtual uint8_t endTransmission(bool stopBit = true);
    virtual size_t requestFrom(uint8_t address, size_t len, bool stopBit = true);
    
    // 数据操作
    virtual size_t write(uint8_t data);
    virtual size_t write(const uint8_t* data, int len);
    virtual int read();
    virtual int peek();
    virtual void flush();
    virtual int available();
    
    // 回调设置
    virtual void onReceive(void(*)(int));
    virtual void onRequest(void(*)(void));
    
    // 资源管理
    void aquire();
    void release();

private:
    const struct device * master;
    struct k_mutex mutex;
    
    // 缓冲区
    char buf[BUFFER_RX_SIZE];
    RingBufferN<BUFFER_RX_SIZE> rxBuffer;
    uint8_t txBuffer[BUFFER_TX_SIZE];
    uint32_t usedTxBuffer;
    
    // 底层操作
    int master_read(int address, const char * buf, const uint32_t len, bool no_stop);
    int master_write(int address, const char * buf, const uint32_t len, bool no_stop);
    int i2c_message(uint8_t read_write, int address, const char * buf, 
                   const uint32_t len, bool no_stop);
};
```

#### 配置参数
```cpp
#define BUFFER_TX_SIZE 256    // 发送缓冲区大小
#define BUFFER_RX_SIZE 512    // 接收缓冲区大小
```

### 2. 基础I2C管理 (`TWIM.h/cpp`)

提供更底层的I2C管理接口：

```cpp
class TWIM {
public:
    TWIM(const struct device * master);
    virtual void begin();
    virtual void end();
    virtual void setClock(uint32_t speed = I2C_SPEED_FAST);
    
    void aquire();
    void release();
    
    const struct device * master;
    
private:
    struct k_mutex mutex;
};
```

### 3. 环形缓冲区 (`RingBuffer.h`)

用于I2C数据缓冲的环形缓冲区实现：

```cpp
template<int N>
class RingBufferN {
private:
    uint8_t _buffer[N];
    volatile int _head;
    volatile int _tail;
    
public:
    void store_char(uint8_t c);
    int read_char();
    int available();
    int peek();
    void clear();
    bool isFull();
};
```

## 工作机制

### 1. 初始化流程
```cpp
void MbedI2C::begin(uint32_t speed) {
    // 1. 检查设备就绪状态
    if (!device_is_ready(master)) {
        LOG_ERR("I2C device not ready");
        return;
    }
    
    // 2. 配置I2C时钟速度
    setClock(speed);
    
    // 3. 初始化缓冲区
    rxBuffer.clear();
    usedTxBuffer = 0;
    
    // 4. 初始化互斥锁
    k_mutex_init(&mutex);
}
```

### 2. 数据传输流程

#### 主机写操作
```cpp
void beginTransmission(uint8_t address) {
    _address = address;
    usedTxBuffer = 0;  // 清空发送缓冲区
}

size_t write(uint8_t data) {
    if (usedTxBuffer < BUFFER_TX_SIZE) {
        txBuffer[usedTxBuffer++] = data;
        return 1;
    }
    return 0;
}

uint8_t endTransmission(bool stopBit) {
    int ret = master_write(_address, (const char*)txBuffer, usedTxBuffer, !stopBit);
    usedTxBuffer = 0;
    return (ret == 0) ? 0 : 4;  // 0=成功, 4=其他错误
}
```

#### 主机读操作
```cpp
size_t requestFrom(uint8_t address, size_t len, bool stopBit) {
    char buffer[len];
    int ret = master_read(address, buffer, len, !stopBit);
    
    if (ret == 0) {
        // 将数据存入环形缓冲区
        for (size_t i = 0; i < len; i++) {
            rxBuffer.store_char(buffer[i]);
        }
        return len;
    }
    return 0;
}

int read() {
    return rxBuffer.read_char();
}
```

### 3. 底层I2C操作
```cpp
int i2c_message(uint8_t read_write, int address, const char * buf, 
               const uint32_t len, bool no_stop) {
    struct i2c_msg msg;
    
    msg.buf = (uint8_t*)buf;
    msg.len = len;
    msg.flags = read_write;
    if (no_stop) {
        msg.flags |= I2C_MSG_STOP;
    }
    
    return i2c_transfer(master, &msg, 1, address);
}
```

## 线程安全

### 互斥锁保护
```cpp
void aquire() {
    k_mutex_lock(&mutex, K_FOREVER);
}

void release() {
    k_mutex_unlock(&mutex);
}
```

### 典型使用模式
```cpp
wire.aquire();
wire.beginTransmission(device_address);
wire.write(register_address);
wire.write(data);
wire.endTransmission();
wire.release();
```

## 缓冲区管理

### 发送缓冲区
- 固定大小256字节
- 在 `beginTransmission` 时清空
- 在 `endTransmission` 时发送

### 接收缓冲区
- 使用环形缓冲区，大小512字节
- 支持流式数据接收
- 提供 `available()` 查询可读数据量

### 环形缓冲区操作
```cpp
template<int N>
void RingBufferN<N>::store_char(uint8_t c) {
    int next_head = (_head + 1) % N;
    if (next_head != _tail) {
        _buffer[_head] = c;
        _head = next_head;
    }
}

template<int N>
int RingBufferN<N>::read_char() {
    if (_head == _tail) {
        return -1;  // 缓冲区空
    }
    
    uint8_t c = _buffer[_tail];
    _tail = (_tail + 1) % N;
    return c;
}
```

## 错误处理

### 设备状态检查
```cpp
if (!device_is_ready(master)) {
    LOG_ERR("I2C master device %s not ready", master->name);
    return -ENODEV;
}
```

### 传输错误处理
```cpp
int ret = i2c_transfer(master, msgs, num_msgs, addr);
if (ret != 0) {
    LOG_ERR("I2C transfer failed: %d", ret);
    return ret;
}
```

### 缓冲区溢出保护
```cpp
size_t write(const uint8_t* data, int len) {
    size_t written = 0;
    for (int i = 0; i < len && usedTxBuffer < BUFFER_TX_SIZE; i++) {
        txBuffer[usedTxBuffer++] = data[i];
        written++;
    }
    return written;
}
```

## 设备集成

### 设备树配置
```dts
&i2c0 {
    status = "okay";
    clock-frequency = <I2C_BITRATE_FAST>;
    
    sensor@48 {
        compatible = "example,sensor";
        reg = <0x48>;
    };
};
```

### 驱动实例化
```cpp
// 获取I2C设备
const struct device *i2c_dev = DEVICE_DT_GET(DT_NODELABEL(i2c0));

// 创建Wire实例
MbedI2C wire(i2c_dev);

// 初始化
wire.begin(I2C_SPEED_FAST);
```

## 典型应用场景

### 1. 传感器数据读取
```cpp
// 读取传感器寄存器
uint8_t readSensorRegister(uint8_t addr, uint8_t reg) {
    wire.aquire();
    
    wire.beginTransmission(addr);
    wire.write(reg);
    wire.endTransmission(false);  // 重复启动
    
    wire.requestFrom(addr, 1);
    uint8_t data = wire.read();
    
    wire.release();
    return data;
}
```

### 2. 传感器配置写入
```cpp
// 写入传感器寄存器
void writeSensorRegister(uint8_t addr, uint8_t reg, uint8_t value) {
    wire.aquire();
    
    wire.beginTransmission(addr);
    wire.write(reg);
    wire.write(value);
    wire.endTransmission();
    
    wire.release();
}
```

### 3. 批量数据传输
```cpp
// 读取多个连续寄存器
void readMultipleRegisters(uint8_t addr, uint8_t startReg, 
                          uint8_t* buffer, size_t len) {
    wire.aquire();
    
    wire.beginTransmission(addr);
    wire.write(startReg);
    wire.endTransmission(false);
    
    wire.requestFrom(addr, len);
    for (size_t i = 0; i < len; i++) {
        buffer[i] = wire.read();
    }
    
    wire.release();
}
```

## 性能优化

### 时钟配置
```cpp
void setClock(uint32_t freq) {
    struct i2c_config config;
    config.frequency = freq;
    config.flags = I2C_MODE_MASTER;
    
    i2c_configure(master, &config);
}
```

### 支持的时钟速度
- **I2C_SPEED_STANDARD**: 100 kHz
- **I2C_SPEED_FAST**: 400 kHz
- **I2C_SPEED_FAST_PLUS**: 1 MHz

### 缓冲区优化
- 合理的缓冲区大小配置
- 避免频繁的小数据传输
- 批量操作提高效率

## 调试支持

### 日志记录
```cpp
#include <zephyr/logging/log.h>
LOG_MODULE_REGISTER(wire, CONFIG_WIRE_LOG_LEVEL);

LOG_DBG("I2C write to 0x%02x: %d bytes", address, len);
LOG_ERR("I2C transfer failed: %d", ret);
```

### 状态监控
- 传输成功/失败统计
- 缓冲区使用情况监控
- 设备响应时间测量

## 总结

I2C通信模块提供了完整的I2C通信支持，具有以下特点：

1. **兼容性**: Arduino Wire库兼容接口
2. **可靠性**: 完整的错误处理和状态检查
3. **高效性**: 优化的缓冲区管理和批量传输
4. **线程安全**: 互斥锁保护的并发访问
5. **灵活性**: 支持多种时钟速度和传输模式

该模块为OpenEarable设备的传感器和外设通信提供了稳定可靠的I2C通信基础设施。
