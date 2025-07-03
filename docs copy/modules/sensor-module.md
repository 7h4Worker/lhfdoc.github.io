# 传感器管理模块详细分析

## 模块概述

传感器管理模块是OpenEarable 2.0的核心创新组件，负责管理集成的多种高精度传感器，包括IMU、PPG、温度、气压、麦克风等传感器。该模块提供统一的传感器接口、数据采集、处理和传输功能，是OpenEarable区别于普通音频设备的关键特性。

## 文件结构

```
src/SensorManager/
├── SensorManager.h/.cpp      # 传感器管理器核心
├── EdgeMLSensor.h/.cpp       # 传感器基类定义
├── IMU.h/.cpp               # 惯性测量单元传感器
├── PPG.h/.cpp               # 光电容积脉搏波传感器
├── Baro.h/.cpp              # 气压传感器
├── Temp.h/.cpp              # 温度传感器
├── BoneConduction.h/.cpp    # 骨传导传感器
├── Microphone.h/.cpp        # 麦克风传感器
├── BMX160/                  # BMX160 IMU驱动
├── MAXM86161/              # MAXM86161 PPG驱动
├── BMP388/                 # BMP388 气压计驱动
├── MLX90632/               # MLX90632 红外温度计驱动
├── BMA580/                 # BMA580 加速度计驱动
├── CMakeLists.txt          # 构建配置
└── Kconfig                 # 配置选项
```

## 核心架构

### 1. SensorManager - 传感器管理器

SensorManager是整个传感器系统的核心控制组件，负责传感器的生命周期管理、数据流控制和系统协调。

#### 主要功能

- **传感器生命周期管理**: 初始化、启动、停止传感器
- **数据流管理**: 传感器数据的采集、缓冲和分发
- **配置管理**: 动态配置传感器参数
- **消息总线集成**: 通过ZBus与其他模块通信
- **存储管理**: 控制数据的本地存储和蓝牙传输

#### 核心接口

```cpp
// 传感器管理器状态
enum sensor_manager_state {
    INIT,           // 初始化状态
    RUNNING,        // 运行状态
    SUSPENDED,      // 挂起状态
};

// 主要控制接口
void init_sensor_manager();                        // 初始化传感器管理器
void start_sensor_manager();                       // 启动传感器管理器
void stop_sensor_manager();                        // 停止传感器管理器
void config_sensor(struct sensor_config *config);  // 配置传感器
enum sensor_manager_state get_state();             // 获取管理器状态
```

#### 工作队列架构

```cpp
// 传感器专用工作队列
extern struct k_work_q sensor_work_q;

// 消息队列定义
K_MSGQ_DEFINE(sensor_queue, sizeof(struct sensor_msg), 256, 4);
K_MSGQ_DEFINE(config_queue, sizeof(struct sensor_config), 16, 4);

// ZBus通道定义
ZBUS_CHAN_DEFINE(sensor_chan, struct sensor_msg, NULL, NULL, 
                 ZBUS_OBSERVERS_EMPTY, ZBUS_MSG_INIT(0));
```

### 2. EdgeMLSensor - 传感器基类

EdgeMLSensor是所有传感器类的抽象基类，定义了统一的传感器接口和行为模式。

#### 设计特点

- **纯虚函数接口**: 强制子类实现核心功能
- **统一的生命周期**: 标准化的初始化、启动、停止流程
- **配置化采样率**: 支持多档位采样率配置
- **双重数据流**: 支持SD卡存储和蓝牙传输

#### 核心接口

```cpp
template <size_t N>
struct SampleRateSetting {
    uint8_t reg_vals[N];        // 寄存器配置值
    float sample_rates[N];      // 标称采样率
    float true_sample_rates[N]; // 实际采样率
};

class EdgeMlSensor {
public:
    // 纯虚函数接口
    virtual bool init(struct k_msgq *queue) = 0;   // 初始化传感器
    virtual void start(int sample_rate_idx) = 0;   // 启动传感器
    virtual void stop() = 0;                       // 停止传感器

    // 状态查询和控制
    bool is_running();                             // 检查运行状态
    void sd_logging(bool enable);                  // 控制SD卡记录
    void ble_stream(bool enable);                  // 控制蓝牙流传输

protected:
    k_work sensor_work;         // 传感器工作项
    k_timer sensor_timer;       // 传感器定时器
    static k_msgq *sensor_queue; // 传感器消息队列

    bool _sd_logging = false;   // SD卡记录标志
    bool _ble_stream = true;    // 蓝牙传输标志
    bool _running = false;      // 运行状态标志
};
```

## 传感器实现详解

### 1. IMU 传感器 (BMX160)

IMU传感器基于Bosch BMX160九轴传感器，提供加速度计、陀螺仪和磁力计数据。

#### 技术规格

- **加速度计**: ±2g/±4g/±8g/±16g量程，14位分辨率
- **陀螺仪**: ±125°/s到±2000°/s量程，16位分辨率
- **磁力计**: ±1300μT量程，高精度磁场测量

#### 采样率配置

```cpp
class IMU : public EdgeMlSensor {
public:
    const static SampleRateSetting<6> sample_rates;
    
private:
    static DFRobot_BMX160 imu;  // BMX160驱动实例
};

// 支持的采样率设置
const SampleRateSetting<6> IMU::sample_rates = {
    .reg_vals = {0x07, 0x08, 0x09, 0x0A, 0x0B, 0x0C},
    .sample_rates = {25.0, 50.0, 100.0, 200.0, 400.0, 800.0},
    .true_sample_rates = {25.32, 50.64, 101.28, 202.56, 405.12, 810.24}
};
```

#### 数据结构

```cpp
struct imu_data {
    float accel_x, accel_y, accel_z;    // 加速度 (m/s²)
    float gyro_x, gyro_y, gyro_z;       // 角速度 (rad/s)
    float mag_x, mag_y, mag_z;          // 磁场强度 (μT)
    uint64_t timestamp;                 // 时间戳 (μs)
} __attribute__((packed));
```

### 2. PPG 传感器 (MAXM86161)

PPG传感器基于Maxim MAXM86161光学传感器，用于心率监测、血氧测量和生理信号分析。

#### 技术规格

- **光源**: 红光、红外光、绿光LED
- **光电二极管**: 高灵敏度光电检测器
- **采样率**: 最高3200Hz
- **分辨率**: 19位ADC

#### LED配置

```cpp
enum led_order {
    red,        // 红光LED (660nm)
    green,      // 绿光LED (537nm) 
    ir,         // 红外LED (880nm)
    ambient     // 环境光检测
};

class PPG : public EdgeMlSensor {
public:
    const static SampleRateSetting<16> sample_rates;
    
private:
    static MAXM86161 ppg;           // MAXM86161驱动实例
    ppg_sample data_buffer[64];     // 数据缓冲区
};
```

#### 数据结构

```cpp
struct ppg_sample {
    uint32_t red;           // 红光通道数据
    uint32_t ir;            // 红外通道数据
    uint32_t green;         // 绿光通道数据
    uint32_t ambient;       // 环境光数据
    uint64_t timestamp;     // 时间戳
} __attribute__((packed));
```

### 3. 温度传感器 (MLX90632)

温度传感器基于Melexis MLX90632非接触式红外温度计，可测量物体温度和环境温度。

#### 技术规格

- **测量范围**: -20°C到85°C (环境), -20°C到200°C (物体)
- **精度**: ±0.2°C (典型值)
- **响应时间**: <1秒
- **接口**: I2C

#### 数据结构

```cpp
struct temp_data {
    float ambient_temp;     // 环境温度 (°C)
    float object_temp;      // 物体温度 (°C)
    uint64_t timestamp;     // 时间戳
} __attribute__((packed));
```

### 4. 气压传感器 (BMP388)

气压传感器基于Bosch BMP388高精度气压计，用于高度测量和环境监测。

#### 技术规格

- **压力范围**: 300-1250 hPa
- **精度**: ±0.08 hPa (典型值)
- **高度分辨率**: ±8 cm
- **温度补偿**: 集成温度传感器

#### 数据结构

```cpp
struct baro_data {
    float pressure;         // 大气压力 (hPa)
    float temperature;      // 温度 (°C)
    float altitude;         // 海拔高度 (m)
    uint64_t timestamp;     // 时间戳
} __attribute__((packed));
```

### 5. 骨传导传感器

骨传导传感器通过检测颅骨振动来感知语音和咀嚼等生理活动。

#### 实现原理

- **振动检测**: 高灵敏度加速度计检测骨传导振动
- **信号处理**: 数字滤波和特征提取
- **模式识别**: 语音活动检测(VAD)

#### 数据结构

```cpp
struct bone_conduction_data {
    float vibration_x, vibration_y, vibration_z;   // 三轴振动数据
    float rms_amplitude;                           // RMS振幅
    bool voice_activity;                           // 语音活动标志
    uint64_t timestamp;                            // 时间戳
} __attribute__((packed));
```

## 数据流架构

### 传感器数据流

```
[传感器硬件] → [驱动层] → [EdgeMLSensor] → [SensorManager] → [数据分发]
                                                                    ↓
                                                              [SD卡存储]
                                                                    ↓
                                                              [蓝牙传输]
```

### 消息队列系统

```cpp
// 传感器消息结构
struct sensor_msg {
    bool sd;                    // SD卡存储标志
    bool stream;                // 蓝牙传输标志
    struct sensor_data data;    // 传感器数据
};

// 传感器数据结构
struct sensor_data {
    uint8_t id;                 // 传感器ID
    uint8_t size;               // 数据大小
    uint64_t time;              // 时间戳
    uint8_t data[36];           // 数据载荷
} __attribute__((packed));
```

### 配置系统

```cpp
// 传感器配置结构
struct sensor_config {
    uint8_t sensorId;           // 传感器ID
    uint8_t sampleRateIndex;    // 采样率索引
    uint8_t storageOptions;     // 存储选项
} __attribute__((packed));

// 传感器ID枚举
enum sensor_id {
    ID_IMU = 0,                 // 惯性测量单元
    ID_TEMP_BARO = 1,           // 温度气压传感器
    ID_MICRO = 2,               // 麦克风
    ID_PPG = 4,                 // 光电容积脉搏波
    ID_PULSOX = 5,              // 脉搏血氧
    ID_OPTTEMP = 6,             // 光学温度计
    ID_BONE_CONDUCTION = 7,     // 骨传导传感器
};
```

## 定时器和中断系统

### 定时器驱动的数据采集

```cpp
class IMU : public EdgeMlSensor {
private:
    // 定时器中断处理函数
    static void sensor_timer_handler(struct k_timer *dummy) {
        k_work_submit_to_queue(&sensor_work_q, &sensor.sensor_work);
    }
    
    // 传感器数据更新工作项
    static void update_sensor(struct k_work *work) {
        // 1. 读取传感器数据
        bmx160_data_t raw_data;
        imu.read_sensor_data(&raw_data);
        
        // 2. 数据格式转换
        struct sensor_data sensor_data;
        format_imu_data(&raw_data, &sensor_data);
        
        // 3. 发送到消息队列
        struct sensor_msg msg = {
            .sd = sensor._sd_logging,
            .stream = sensor._ble_stream,
            .data = sensor_data
        };
        k_msgq_put(&sensor_queue, &msg, K_NO_WAIT);
    }
};
```

### 中断驱动的事件检测

```cpp
// PPG传感器的FIFO中断处理
void ppg_fifo_interrupt_handler() {
    // 1. 读取FIFO数据
    uint8_t fifo_samples = ppg.get_fifo_samples();
    
    for (int i = 0; i < fifo_samples; i++) {
        // 2. 处理每个样本
        ppg_sample sample;
        ppg.read_fifo_sample(&sample);
        
        // 3. 质量检查和处理
        if (is_valid_ppg_sample(&sample)) {
            process_ppg_data(&sample);
        }
    }
}
```

## 功耗管理

### 动态功耗控制

```cpp
void sensor_power_management() {
    // 根据活跃传感器数量调整功耗
    if (active_sensors == 0) {
        // 无活跃传感器，进入低功耗模式
        set_sensor_power_mode(POWER_MODE_SLEEP);
    } else if (active_sensors <= 2) {
        // 少量传感器，中等功耗模式
        set_sensor_power_mode(POWER_MODE_NORMAL);
    } else {
        // 多传感器，高性能模式
        set_sensor_power_mode(POWER_MODE_HIGH_PERFORMANCE);
    }
}
```

### 采样率自适应

```cpp
void adaptive_sampling_rate() {
    // 根据电池电量和数据需求调整采样率
    uint8_t battery_level = get_battery_level();
    
    if (battery_level < 20) {
        // 低电量时降低采样率
        reduce_sensor_sampling_rates();
    } else if (battery_level > 80) {
        // 电量充足时恢复正常采样率
        restore_sensor_sampling_rates();
    }
}
```

## 数据处理和分析

### 实时信号处理

```cpp
// IMU数据的运动检测
bool detect_motion(imu_data *data) {
    // 计算加速度向量的幅值
    float accel_magnitude = sqrt(data->accel_x * data->accel_x +
                                data->accel_y * data->accel_y +
                                data->accel_z * data->accel_z);
    
    // 判断是否有显著运动
    return (accel_magnitude > MOTION_THRESHOLD);
}

// PPG数据的心率检测
float calculate_heart_rate(ppg_sample *samples, int count) {
    // 1. 信号预处理
    filter_ppg_signal(samples, count);
    
    // 2. 峰值检测
    int peak_count = detect_peaks(samples, count);
    
    // 3. 心率计算
    float sampling_period = 1.0f / PPG_SAMPLE_RATE;
    float heart_rate = (peak_count * 60.0f) / (count * sampling_period);
    
    return heart_rate;
}
```

### 传感器融合

```cpp
// 多传感器融合的姿态估计
void sensor_fusion_update(imu_data *imu, mag_data *mag) {
    // 1. 加速度计姿态估计
    float accel_roll = atan2(imu->accel_y, imu->accel_z);
    float accel_pitch = atan2(-imu->accel_x, 
                             sqrt(imu->accel_y * imu->accel_y + 
                                  imu->accel_z * imu->accel_z));
    
    // 2. 陀螺仪姿态积分
    integrate_gyroscope_data(imu);
    
    // 3. 磁力计偏航角计算
    float mag_yaw = atan2(mag->mag_y, mag->mag_x);
    
    // 4. 互补滤波器融合
    complementary_filter_update(accel_roll, accel_pitch, mag_yaw);
}
```

## 校准和补偿

### 传感器校准

```cpp
// IMU零偏校准
void calibrate_imu_bias() {
    const int calibration_samples = 1000;
    float accel_bias[3] = {0, 0, 0};
    float gyro_bias[3] = {0, 0, 0};
    
    // 收集校准数据
    for (int i = 0; i < calibration_samples; i++) {
        imu_data data;
        read_imu_data(&data);
        
        accel_bias[0] += data.accel_x;
        accel_bias[1] += data.accel_y;
        accel_bias[2] += data.accel_z - 9.81f; // 重力补偿
        
        gyro_bias[0] += data.gyro_x;
        gyro_bias[1] += data.gyro_y;
        gyro_bias[2] += data.gyro_z;
        
        k_sleep(K_MSEC(1));
    }
    
    // 计算平均偏差
    for (int i = 0; i < 3; i++) {
        accel_bias[i] /= calibration_samples;
        gyro_bias[i] /= calibration_samples;
    }
    
    // 存储校准参数
    store_calibration_data(accel_bias, gyro_bias);
}
```

### 温度补偿

```cpp
// PPG温度补偿
void temperature_compensation_ppg(ppg_sample *sample, float temperature) {
    // 基于温度的增益补偿
    float temp_coeff = 1.0f + (temperature - 25.0f) * 0.001f;
    
    sample->red = (uint32_t)(sample->red * temp_coeff);
    sample->ir = (uint32_t)(sample->ir * temp_coeff);
    sample->green = (uint32_t)(sample->green * temp_coeff);
}
```

## 配置选项

### Kconfig配置

```kconfig
# 传感器管理器配置
CONFIG_SENSOR_WORK_QUEUE_STACK_SIZE=2048
CONFIG_SENSOR_WORK_QUEUE_PRIO=5
CONFIG_SENSOR_PUB_STACK_SIZE=1024
CONFIG_SENSOR_PUB_THREAD_PRIO=6

# 传感器使能
CONFIG_SENSOR_IMU=y
CONFIG_SENSOR_PPG=y
CONFIG_SENSOR_TEMPERATURE=y
CONFIG_SENSOR_BAROMETER=y
CONFIG_SENSOR_BONE_CONDUCTION=y

# 采样率配置
CONFIG_IMU_DEFAULT_SAMPLE_RATE=100
CONFIG_PPG_DEFAULT_SAMPLE_RATE=400
CONFIG_TEMP_DEFAULT_SAMPLE_RATE=10

# 数据缓冲配置
CONFIG_SENSOR_QUEUE_SIZE=256
CONFIG_SENSOR_BUFFER_SIZE=64
```

## 错误处理和诊断

### 传感器健康监控

```cpp
void sensor_health_check() {
    // 检查各传感器状态
    for (int id = 0; id < NUM_SENSORS; id++) {
        EdgeMlSensor *sensor = get_sensor((sensor_id)id);
        
        if (sensor && sensor->is_running()) {
            // 检查数据更新频率
            if (sensor_data_rate[id] < expected_rate[id] * 0.8f) {
                LOG_WRN("Sensor %d data rate low: %.1f Hz", 
                       id, sensor_data_rate[id]);
                
                // 尝试重启传感器
                sensor->stop();
                k_sleep(K_MSEC(100));
                sensor->start(sensor_config[id].sample_rate_idx);
            }
        }
    }
}
```

### 数据质量检查

```cpp
bool validate_sensor_data(struct sensor_data *data) {
    switch (data->id) {
        case ID_IMU:
            return validate_imu_data((imu_data*)data->data);
        case ID_PPG:
            return validate_ppg_data((ppg_sample*)data->data);
        case ID_TEMP_BARO:
            return validate_temp_baro_data((temp_baro_data*)data->data);
        default:
            return true;
    }
}
```

## 总结

传感器管理模块是OpenEarable 2.0的核心创新特性，具有以下关键优势：

1. **多传感器集成**: 支持IMU、PPG、温度、气压等多种传感器
2. **统一管理接口**: 通过EdgeMLSensor基类提供统一的传感器接口
3. **高效数据流**: 基于消息队列和ZBus的高效数据传输
4. **灵活配置**: 支持动态配置采样率和存储选项
5. **实时处理**: 低延迟的数据采集和处理能力
6. **功耗优化**: 智能的功耗管理和自适应采样
7. **数据质量**: 完善的校准、补偿和质量检查机制
8. **模块化设计**: 易于扩展新的传感器类型

该模块为OpenEarable 2.0提供了强大的传感器数据采集和处理能力，支持各种生理监测、运动追踪和环境感知应用，是实现智能耳戴式设备功能的核心基础。
