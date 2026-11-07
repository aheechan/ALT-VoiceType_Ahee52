ALT-VoiceType 整合安装包 0.1.0
================================

这个包是离线整合包：包含程序本体和固定的 3 个模型。

内置 CUDA llama.cpp 运行库
固定模型
--------
Qwen3-ASR-0.6B
Qwen3-1.7B-Abliterated Q4
Index-Translate-2B Q4

模型合计约 4.00 GB。

三个档位
--------
eco
  20 秒输入上限
  CPU 运行全部模型

standard
  45 秒输入上限
  全 GPU 运行

extended
  120 秒输入上限
  全 GPU 运行

安装后占用约 5.4 GB。
下载文件合计约 3.93 GB。
安装时建议预留至少 12 GB 空闲磁盘。

文件说明
--------
必须把下面所有文件下载到同一个文件夹，不能只下载 exe：

ALT-VoiceType-Setup-0.1.0.exe
ALT-VoiceType-Setup-0.1.0-1.bin
ALT-VoiceType-Setup-0.1.0-2.bin
ALT-VoiceType-Setup-0.1.0-3.bin
SHA256SUMS.txt

每个 .bin 都小于 1.8 GB，可以分别上传到 GitHub Release。
不要重命名 exe 或 bin 文件；安装器会按原文件名查找分卷。

安装
----
1. 把上面的文件放在同一个文件夹。
2. 双击 ALT-VoiceType-Setup-0.1.0.exe。
3. 安装器会自动读取同目录下的 -1.bin 到 -3.bin。
4. 安装完成后启动 ALT-VoiceType。

模型安装位置
------------
模型会安装到安装目录下的 models 文件夹，例如：

D:\ALT-VoiceType\models

卸载软件时，安装目录中的模型会一并删除。

配置和日志
----------
%APPDATA%\ALT-VoiceType\config.json
%APPDATA%\ALT-VoiceType\logs\app.log

快捷键
------
默认：左 Alt（lalt）

设置中可以改为：
lalt、ralt、lalt+q、ralt+space、alt+shift 等。
Alt 不会被独占。

校验
----
certutil -hashfile ALT-VoiceType-Setup-0.1.0.exe SHA256

其他文件的期望值见 SHA256SUMS.txt。

注意
----
- 安装包未签名，Windows SmartScreen 可能提示“未知发布者”。
- 安装时需要同时保留安装包和已安装文件。
- 输入结束后的收尾录音为 0.39 秒。
- 识别结果中的数字统一使用阿拉伯数字。
