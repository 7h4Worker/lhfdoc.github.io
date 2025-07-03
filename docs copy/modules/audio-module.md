# 音频处理模块详细分析

## 模块概述

音频处理模块是OpenEarable 2.0的核心功能组件，负责完整的音频信号链处理，包括音频捕获、编解码、流控制、信号处理等功能。该模块基于nRF5340 Audio DK的成熟音频架构，支持LE Audio协议和高质量音频处理。

## 文件结构

```
src/audio/
├── streamctrl.h/.c           # 音频流控制核心
├── audio_datapath.h/.c       # 音频数据路径处理
├── audio_system.h/.c         # 音频子系统管理
├── le_audio_rx.h/.c          # LE Audio接收处理
├── pdm_mic.h/.c              # PDM麦克风驱动
├── sw_codec_select.h/.c      # 软件编解码器选择
├── Equalizer.h/.cpp          # 音频均衡器
├── sdlogger_wrapper.h/.cpp   # SD卡日志包装器
├── CMakeLists.txt            # 构建配置
├── Kconfig                   # 配置选项
└── Kconfig.defaults          # 默认配置
```

## 核心组件分析

### 1. StreamCtrl - 音频流控制器

StreamCtrl是音频流处理的核心控制组件，负责管理音频流的状态和数据传输。

#### 主要功能

- **流状态管理**: 控制播放/暂停状态
- **数据传输**: 处理音频数据的发送
- **同步控制**: 确保音频数据的同步传输

#### 接口定义

```cpp
// 流状态枚举
enum stream_state {
    STATE_STREAMING,    // 正在流传输
    STATE_PAUSED,       // 暂停状态
};

// 核心接口函数
uint8_t stream_state_get(void);                        // 获取当前流状态
void streamctrl_send(const void *data, size_t size, uint8_t num_ch); // 发送音频数据
int streamctrl_start();                                 // 启动流控制
```

#### 实现特点

- **状态机管理**: 使用状态机控制流传输状态
- **多声道支持**: 支持单声道和立体声音频
- **缓冲管理**: 智能的音频缓冲区管理

### 2. Audio Datapath - 音频数据路径

音频数据路径模块负责音频数据的完整处理流程，从输入到输出的所有处理环节。

#### 主要功能

- **音频同步**: 基于时间戳的音频同步
- **格式转换**: 音频格式和采样率转换
- **信号处理**: 音频增强和降噪处理
- **测试音生成**: 系统测试音频信号生成

#### 核心接口

```cpp
// 主要处理接口
void audio_datapath_stream_out(const uint8_t *buf, size_t size, 
                               uint32_t sdu_ref_us, bool bad_frame,
                               uint32_t recv_frame_ts_us);

// 系统控制接口
int audio_datapath_start(struct data_fifo *fifo_rx);   // 启动数据路径
int audio_datapath_stop(void);                         // 停止数据路径
int audio_datapath_init(void);                         // 初始化数据路径

// 音频增强功能
int audio_datapath_tone_play(uint16_t freq, uint16_t dur_ms, float amplitude);
void audio_datapath_tone_stop(void);                   // 停止测试音

// 延迟控制
int audio_datapath_pres_delay_us_set(uint32_t delay_us);
void audio_datapath_pres_delay_us_get(uint32_t *delay_us);
```

#### 数据流架构

```
[LE Audio RX] → [Decoder] → [Equalizer] → [I2S Output]
                    ↓
                [SD Logger] (可选)
                    ↓
                [Sensor Data] (可选)
```

#### 同步机制

```cpp
// 时间戳同步处理
void audio_datapath_stream_out(const uint8_t *buf, size_t size, 
                               uint32_t sdu_ref_us, bool bad_frame,
                               uint32_t recv_frame_ts_us) {
    // 1. 解码音频数据
    // 2. 计算播放时间戳
    // 3. 应用呈现延迟
    // 4. 同步到I2S输出
    // 5. 记录到SD卡(可选)
}
```

### 3. Audio System - 音频子系统

音频子系统提供高层次的音频管理接口，集成编解码器、音频处理和系统控制。

#### 主要功能

- **编解码管理**: LC3编解码器控制
- **系统配置**: 音频参数配置管理
- **测试功能**: 内置测试音生成
- **性能优化**: 音频处理性能优化

#### 核心接口

```cpp
// 系统控制
void audio_system_start(void);                         // 启动音频系统
void audio_system_stop(void);                          // 停止音频系统

// 编码器控制
void audio_system_encoder_start(void);                 // 启动编码器
void audio_system_encoder_stop(void);                  // 停止编码器

// 配置管理
int audio_system_config_set(uint32_t encoder_sample_rate_hz, 
                            uint32_t encoder_bitrate,
                            uint32_t decoder_sample_rate_hz);

// 解码处理
int audio_system_decode(const void *encoded_data, size_t encoded_data_size, 
                       bool bad_frame);

// 测试功能
int audio_system_encode_test_tone_set(uint32_t freq);
int audio_system_encode_test_tone_step(void);

// 缓冲管理
int audio_system_fifo_rx_block_drop(void);
```

#### 配置参数

```cpp
struct audio_config {
    uint32_t sample_rate_hz;    // 采样率
    uint32_t bitrate_bps;       // 比特率
    uint8_t channels;           // 声道数
    uint16_t frame_size_us;     // 帧长度(微秒)
};
```

### 4. PDM Microphone - PDM麦克风驱动

PDM麦克风模块负责板载麦克风的音频捕获功能。

#### 主要功能

- **PDM信号采集**: 脉冲密度调制信号采集
- **数字滤波**: PDM到PCM转换和滤波
- **缓冲管理**: 音频数据缓冲和队列管理

#### 接口定义

```cpp
// 麦克风控制
void pdm_mic_start(void);                              // 启动麦克风
void pdm_mic_stop(void);                               // 停止麦克风
int pdm_mic_init(void);                                // 初始化麦克风

// 数据路径
int pdm_datapath_start(struct data_fifo *fifo_rx);     // 启动PDM数据路径
```

#### PDM配置

```cpp
// PDM配置参数
struct pdm_config {
    uint32_t sample_rate;       // 采样率 (通常16kHz)
    uint8_t gain_l;             // 左声道增益
    uint8_t gain_r;             // 右声道增益
    uint8_t clock_freq;         // PDM时钟频率
};
```

### 5. Equalizer - 音频均衡器

音频均衡器提供实时音频增强和频率响应调整功能。

#### 主要功能

- **频率响应调整**: 多频段均衡处理
- **实时处理**: 低延迟音频处理
- **参数可调**: 支持动态参数调整

#### 接口定义

```cpp
#define EQ_ORDER 9              // 均衡器阶数

// 均衡器控制
void reset_eq();                // 重置均衡器
void equalize(int16_t *data, int length);  // 音频均衡处理
```

#### 均衡器结构

```cpp
// 9阶数字滤波器实现
struct eq_filter {
    float coeffs[EQ_ORDER];     // 滤波器系数
    float delays[EQ_ORDER];     // 延迟缓冲
    float gain;                 // 增益参数
};
```

### 6. LE Audio RX - LE Audio接收处理

LE Audio接收模块负责蓝牙LE Audio协议的音频数据接收和处理。

#### 主要功能

- **ISO数据接收**: 接收ISO音频数据包
- **错误处理**: 丢包检测和错误恢复
- **同步维护**: 音频流同步维护
- **质量监控**: 音频质量监控和统计

#### 数据包处理

```cpp
// LE Audio数据包结构
struct le_audio_packet {
    uint32_t timestamp;         // 时间戳
    uint16_t seq_num;           // 序列号
    uint8_t *payload;           // 音频负载
    size_t payload_len;         // 负载长度
    bool crc_ok;               // CRC校验状态
};
```

### 7. Software Codec Select - 软件编解码器选择

软件编解码器选择模块提供LC3等音频编解码器的集成接口。

#### 支持的编解码器

- **LC3**: LE Audio标准编解码器
- **SBC**: 经典蓝牙编解码器(兼容性)
- **Raw PCM**: 未压缩音频格式

#### 编解码器接口

```cpp
// 编解码器操作接口
struct codec_interface {
    int (*init)(void);
    int (*encode)(const int16_t *input, uint8_t *output, size_t *output_size);
    int (*decode)(const uint8_t *input, size_t input_size, int16_t *output);
    void (*deinit)(void);
};
```

## 音频处理流程

### 播放流程

```
[LE Audio RX] → [LC3 Decode] → [Equalizer] → [I2S DAC] → [扬声器]
                      ↓
                [SD Logger] (可选录制)
```

### 录音流程

```
[PDM Mic] → [Filter] → [LC3 Encode] → [LE Audio TX] → [蓝牙传输]
               ↓
          [SD Logger] (可选录制)
```

### 双向通信流程

```
接收: [LE Audio RX] → [Decode] → [Mix] → [I2S Output]
                                   ↑
发送: [PDM Mic] → [Encode] → [LE Audio TX]
```

## 同步和时序

### 音频同步机制

```cpp
// 时间戳同步处理
void audio_sync_process(uint32_t sdu_ref_us, uint32_t recv_ts_us) {
    // 1. 计算传输延迟
    uint32_t transport_delay = recv_ts_us - sdu_ref_us;
    
    // 2. 应用呈现延迟
    uint32_t presentation_delay = get_presentation_delay();
    
    // 3. 计算播放时间
    uint32_t play_time = sdu_ref_us + presentation_delay;
    
    // 4. 同步到I2S播放
    schedule_i2s_playback(play_time);
}
```

### 缓冲管理

```cpp
// 自适应缓冲管理
void adaptive_buffer_management() {
    // 监控缓冲区水位
    size_t buffer_level = get_buffer_level();
    
    if (buffer_level < LOW_THRESHOLD) {
        // 缓冲区过低，增加延迟
        increase_buffer_size();
    } else if (buffer_level > HIGH_THRESHOLD) {
        // 缓冲区过高，减少延迟
        decrease_buffer_size();
    }
}
```

## 音频质量优化

### 1. 降噪处理

```cpp
// 数字降噪算法
void noise_reduction(int16_t *audio_data, size_t length) {
    // 实现自适应滤波降噪
    for (size_t i = 0; i < length; i++) {
        audio_data[i] = apply_noise_filter(audio_data[i]);
    }
}
```

### 2. 动态范围控制

```cpp
// 自动增益控制
void agc_process(int16_t *audio_data, size_t length) {
    // 计算音频能量
    float energy = calculate_energy(audio_data, length);
    
    // 调整增益
    float gain = calculate_optimal_gain(energy);
    apply_gain(audio_data, length, gain);
}
```

### 3. 回声消除

```cpp
// 声学回声消除(AEC)
void echo_cancellation(int16_t *mic_data, int16_t *speaker_data, 
                      int16_t *output, size_t length) {
    // 实现自适应回声消除算法
    adaptive_filter_process(mic_data, speaker_data, output, length);
}
```

## 配置参数

### 音频配置选项

```kconfig
# 采样率配置
CONFIG_AUDIO_SAMPLE_RATE_48000=y
CONFIG_AUDIO_SAMPLE_RATE_16000=n

# 编解码器配置
CONFIG_AUDIO_CODEC_LC3=y
CONFIG_AUDIO_CODEC_SBC=n

# 音频增强
CONFIG_AUDIO_EQUALIZER=y
CONFIG_AUDIO_NOISE_REDUCTION=y
CONFIG_AUDIO_AGC=y

# 缓冲配置
CONFIG_AUDIO_BUFFER_SIZE=4096
CONFIG_AUDIO_BUFFER_COUNT=4
```

### 性能参数

```cpp
// 音频性能参数
#define AUDIO_FRAME_SIZE_US     10000   // 10ms帧长
#define AUDIO_SAMPLE_RATE_HZ    48000   // 48kHz采样率
#define AUDIO_CHANNELS          2       // 立体声
#define AUDIO_BITS_PER_SAMPLE   16      // 16位采样深度

// 延迟参数
#define PRESENTATION_DELAY_US   40000   // 40ms呈现延迟
#define PROCESSING_DELAY_US     5000    // 5ms处理延迟
```

## 错误处理和恢复

### 音频中断处理

```cpp
void audio_error_handler(audio_error_t error) {
    switch (error) {
        case AUDIO_UNDERRUN:
            // 缓冲区下溢处理
            refill_audio_buffer();
            break;
            
        case AUDIO_OVERRUN:
            // 缓冲区上溢处理
            drop_old_audio_frames();
            break;
            
        case AUDIO_SYNC_LOST:
            // 同步丢失处理
            reinitialize_sync();
            break;
            
        default:
            // 通用错误处理
            restart_audio_system();
            break;
    }
}
```

### 质量监控

```cpp
// 音频质量统计
struct audio_quality_stats {
    uint32_t packets_received;      // 接收包数
    uint32_t packets_lost;          // 丢包数
    uint32_t late_packets;          // 延迟包数
    float average_latency_ms;       // 平均延迟
    float jitter_ms;                // 抖动
};
```

## 功耗优化

### 动态功耗管理

```cpp
void audio_power_management() {
    if (audio_stream_active()) {
        // 流传输活跃时，保持高性能模式
        set_cpu_frequency(HIGH_FREQ);
        enable_audio_pll();
    } else {
        // 流传输空闲时，降低功耗
        set_cpu_frequency(LOW_FREQ);
        disable_audio_pll();
    }
}
```

## 总结

音频处理模块是OpenEarable 2.0的核心功能组件，具有以下特点：

1. **完整的音频链**: 从音频捕获到播放的完整处理链
2. **LE Audio支持**: 完整支持蓝牙LE Audio协议栈
3. **高质量处理**: 集成均衡器、降噪等音频增强功能
4. **低延迟设计**: 优化的缓冲和同步机制
5. **模块化架构**: 各功能模块独立，易于维护和扩展
6. **实时性能**: 满足实时音频处理要求
7. **功耗优化**: 智能的功耗管理策略

该模块为OpenEarable 2.0提供了专业级的音频处理能力，支持高质量的音乐播放、通话和音频采集功能。
