"""
This Python program is used to convert audio recordings in Wav format into spectrograms. 
It was originally designed for processing satellite radio downlink telemetry recordings.

Code version: 1.0   Date: January 15, 2024

Developer & Acknowledgments:
    Code prototypes/Functional references: BI4KZZ.
    Developers & Improver: BY7030SWL
    Suggested for: Kaguya810
    Huge contributor: ChatGPT-3.5

License: GNU General Public License v3.0
"""

import os
import re
from datetime import datetime, timedelta
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.ticker import MaxNLocator
from scipy.io.wavfile import read
from scipy import signal

#检测有效频率范围
def detect_valid_frequency_range(freqs_array, Pxx):
    try:
        # 设置判定阈值
        threshold_db=20

        # 计算每个频率的最大分贝
        max_db_per_freq = 10 * np.log10(np.max(Pxx, axis=1) + 1e-10)

        # 找到最小分贝超过阈值的频率a
        min_freq_index = np.argmax(max_db_per_freq > threshold_db)
        min_freq = freqs_array[min_freq_index]

        # 找到最大分贝超过阈值的频率b
        max_freq_index = len(freqs_array) - np.argmax(max_db_per_freq[::-1] > threshold_db) - 1
        max_freq = freqs_array[max_freq_index]
        valid_freq_range = (min_freq, max_freq)

        print("音频有效范围: ", valid_freq_range, "Hz")
        return min_freq, max_freq

    except Exception as e:
        print("检测有效频率范围时出现错误:", e)
        return None


# 获取采样率/音频信号一维 NumPy 数组
def data_acquisition(filename):
    try:
        # 获取采样率/音频信号一维 NumPy 数组
        sample_rate, linear_array = read(filename)

        # 处理一维数组，仅保留一个音频通道的数据
        if linear_array.ndim > 1:
            linear_array = linear_array[:, 0]
            print("检测到音频为双声道，仅保留一个音频通道的数据")

        # 数值返回
        return sample_rate, linear_array

    # 异常处理
    except IOError as e:
        print(f"Error reading {filename}: {e}")
        return None, None
    except Exception as e:
        print("Error:", e)
        return -1


# 绘图函数
def plot_fft_freq_chart(NFFT, noverlap, sample_rate, linear_array, utc_time, base_freq_mhz):
    try:
        # 获取频谱数据
        freqs_array, time_array, Pxx = signal.spectrogram(linear_array, sample_rate, nperseg=NFFT, noverlap=noverlap)
        print(f"linear_array占用内存: {linear_array.nbytes / (1024 * 1024):.2f} MB")
        print(f"Pxx占用内存: {Pxx.nbytes / (1024 * 1024):.2f} MB")
        print(f"freqs_array占用内存: {freqs_array.nbytes / (1024 * 1024):.2f} MB")
        print(f"time_array占用内存: {time_array.nbytes / (1024 * 1024):.2f} MB")

        
        # 获取有效频率范围
        min_freq, max_freq = detect_valid_frequency_range(freqs_array, Pxx)

        # 处理显示范围
        display_mask = (freqs_array >= min_freq) & (freqs_array <= max_freq)
        freqs_array_display = freqs_array[display_mask]
        Pxx_display = Pxx[display_mask]
        del freqs_array, Pxx  # 释放无用大型数组

        # 设置字体，解决中文负号显示问题
        plt.rcParams['font.sans-serif'] = ['SimHei']
        plt.rcParams['axes.unicode_minus'] = False

        # 处理时间数据，修改横坐标轴为UTC时间刻度
        start_time = utc_time + timedelta(seconds=time_array.min())  # 计算数据起始时间
        time_array = np.array([start_time + timedelta(seconds=sec) for sec in time_array])  # 将 time_array 中的秒数与起始时间相加，生成新的时间数组
        time_array = np.insert(time_array, 0, start_time)  # 在时间数组前加一个额外的时间点，确保长度匹配
        plt.gca().xaxis.set_major_formatter(mdates.DateFormatter("%H:%M:%S"))  # 设置横坐标轴格式为小时:分钟:秒
        plt.gca().xaxis.set_major_locator(MaxNLocator(nbins=6))  # 设置横坐标轴刻度的数量

        # 处理频率数据，修改纵坐标轴为绝对频率刻度
        base_freq_hz  = float(freq_str[:-2])  # 处理为Hz为单位的基础频率
        freqs_array_display = (base_freq_hz + freqs_array_display) / 1e6  # 将 freq 数组中的频率与基础频率相加，生成新的绝对频率数组
        plt.gca().yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f'{x:.5f} MHz'))  # 设置纵坐标轴单位为MHz
        plt.gca().yaxis.set_major_locator(MaxNLocator(nbins=5))  # 设置纵坐标轴刻度的数量

        # 处理振幅数据，通过对数变换计算分贝
        log_spec = 10 * np.log10(Pxx_display)

        # 确定图表参数
        plt.imshow(log_spec, cmap='binary', aspect='auto', origin='lower', interpolation='spline16', vmin=30, vmax=40, extent=[time_array.min(), time_array.max(), freqs_array_display.min(), freqs_array_display.max()])
        
        #处理数据，确定各标题
        plt.title(name + " Signal Rceived By Haikou Station")  # 处理信号源名称,确定图表总标题
        plt.xlabel(f'Start Time: {start_time.strftime("%Y/%m/%d - %H:%M:%S")} UTC')  # 计算横坐标轴起始时间,确定横坐标轴标题
        plt.ylabel(f'Base Frequency: {base_freq_mhz} MHz')  # 计算纵坐标轴基础频率,确定纵坐标轴标题
        plt.colorbar(label='Amplitude (dB)')  # 处理上色参数条标题
        
        # 绘制
        plt.show()

    # 异常处理
    except IOError as e:
        print("IOError:", e)
        return -1
    except ValueError as e:
        print("ValueError:", e)
        return -1


# 文件选择部分

# 获取脚本目录下的所有.wav文件
wav_files = [f for f in os.listdir() if f.endswith(".wav")]

# 显示文件编号和文件名
for i, file in enumerate(wav_files, 1):
    print(f"{i}: {file}")

# 获取用户选择的文件编号
while True:
    choosefile = input("请输入你选择的文件的编号：")
    try:
        file_index = int(choosefile) - 1
        if 0 <= file_index < len(wav_files):
            filename = wav_files[file_index]
            break
        else:
            print("选择无效，请重新输入。")
    except ValueError:
        print("输入不是有效的数字，请重新输入。")

# 尝试自动解析文件名
def name_resolution(filename):
    match = re.match(r'(?P<name>[^_]+)_(?P<time>\d{8}_\d{6}Z)_(?P<freq>\d+Hz)_AF\.wav', filename)
    if match:
        name = match.group('name')
        time_str = match.group('time')
        freq_str = match.group('freq')
        utc_time = datetime.strptime(time_str, "%Y%m%d_%H%M%SZ")
        base_freq_mhz = float(freq_str[:-2]) / 1e6
        print("自动解析结果:")
        print("数据源:", name)
        print("时间:", utc_time)
        print("基础频率:", base_freq_mhz, "MHz")
        print("正在处理，请稍候~")
    else:
        while True:
            try:
                print(f"文件名 {filename} 不符合自动解析的格式，请手动输入。")
                name = input("请指定数据来源：")
                time_string = input("请输入时间 (如20240101_235959Z): ")
                freq_string = input("请输入基础频率（*******Hz): ")
                # 构建新的文件名
                filename = f"{name}_{time_string}_{freq_string}_AF.wav"
                # 尝试再次解析
                return name_resolution(filename)
            except ValueError:
                print("输入的格式不正确，请重新输入。")
    return name, time_str, freq_str, utc_time, base_freq_mhz

name_resolution(filename)

# 获取用户选择的预设编号
print("\n预设0：自行输入\n")
print("预设1：\n 傅里叶变换数据点数：32786\n 重叠样本数：30000\n")
print("预设2：\n 傅里叶变换数据点数：16384\n 重叠样本数：15000\n")
print("预设3：\n 傅里叶变换数据点数：16384\n 重叠样本数：12000\n")

while True:
    choose = input("请输入你选择的预设的编号：")
    if choose == "0":
        while True:
            try:
                NFFT = int(float(input("请输入傅里叶变换数据点数：")))
                noverlap = int(float(input("请输入重叠样本数：")))
                if NFFT >= noverlap:
                    break
                else:
                    print("重叠样本数不能大于等于傅里叶变换数据点数，请重新输入。")
            except ValueError:
                print("输入不是有效的整数，请重新输入。")
        break
    elif choose == "1":
        NFFT = 32786
        noverlap = 30000
        break
    elif choose == "2":
        NFFT = 16384
        noverlap = 15000
        break
    elif choose == "3":
        NFFT = 16384
        noverlap = 12000
        break
    else:
        print("选择无效，请重新输入。")

# 获取 name, utc_time 等信息
name, time_str, freq_str, utc_time, base_freq_mhz = name_resolution(filename)

# 调用data_acquisition函数，获取采样率/音频信号一维 NumPy 数组/绘图最大频率值
sample_rate, linear_array = data_acquisition(filename)

# 用获得的数据绘制图表
plot_fft_freq_chart(NFFT, noverlap, sample_rate, linear_array, utc_time, base_freq_mhz)