ALT-VoiceType_Ahee52 整合安装包 0.1.0
====================================

这个包是离线整合包：包含程序本体和 4 个档位共用的 5 个模型。

推荐系统
--------
Windows 10/11 64 位

安装后占用约 12.1 GB
下载文件合计约 9.43 GB
安装时建议预留至少 25 GB 空闲磁盘

文件说明
--------
必须把下面所有文件下载到同一个文件夹，不能只下载 exe：

ALT-VoiceType_Ahee52-Full-Setup-0.1.0.exe
ALT-VoiceType_Ahee52-Full-Setup-0.1.0-1.bin
ALT-VoiceType_Ahee52-Full-Setup-0.1.0-2.bin
ALT-VoiceType_Ahee52-Full-Setup-0.1.0-3.bin
ALT-VoiceType_Ahee52-Full-Setup-0.1.0-4.bin
ALT-VoiceType_Ahee52-Full-Setup-0.1.0-5.bin
ALT-VoiceType_Ahee52-Full-Setup-0.1.0-6.bin
SHA256SUMS.txt

每个 .bin 都小于 1.8 GB，可以分别上传到 GitHub Release。
不要重命名 exe 或 bin 文件；安装器会按原文件名查找分卷。

安装
----
1. 把上面的文件放在同一个文件夹。
2. 双击 ALT-VoiceType_Ahee52-Full-Setup-0.1.0.exe。
3. 安装器会自动读取同目录下的 -1.bin 到 -6.bin。
4. 安装完成后启动 ALT-VoiceType。

模型安装位置
------------
%LOCALAPPDATA%\AltVoice\models\

包含以下 5 个模型：
- qwen3_asr_0_6b
- qwen3_asr_1_7b_uncensored
- qwen3_1_7b_abliterated_q4
- index_translate_2b_q4
- qwen3_4b_abliterated_q4

四个档位
--------
safe
  0.6B ASR + 1.7B Abliterated 纠错 + 2B 翻译

balanced
  0.6B ASR + 1.7B Abliterated 纠错 + 4B Abliterated 翻译

12gb-max
  1.7B Uncensored ASR + 1.7B Abliterated 纠错 + 2B 翻译

16gb-quality
  1.7B Uncensored ASR + 1.7B Abliterated 纠错 + 4B Abliterated 翻译

快捷键
------
默认：左 Alt（lalt）

设置中可以改为：
lalt、ralt、lalt+q、ralt+space、alt+shift 等。
Alt 不会被独占，Alt+Tab 等系统组合仍可用。

校验
----
在文件所在目录运行：

certutil -hashfile ALT-VoiceType_Ahee52-Full-Setup-0.1.0.exe SHA256

其他文件的期望值见 SHA256SUMS.txt。

注意
----
- 安装包未签名，Windows SmartScreen 可能提示“未知发布者”。
- 安装时需要同时保留安装包和已安装文件，峰值占用约 22 GB。
- 如果只需要程序、不需要模型，请使用单独的 341 MB 精简安装包。
