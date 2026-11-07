# ALT-VoiceType_Ahee52

[English](README.en.md) | **中文**

![ALT-VoiceType](altvoice/assets/logo.png)

**完全离线的 Windows 语音输入工具：中文语音识别、上下文纠错、自然多语言翻译。**

按一下快捷键开始说话，再按一下结束；识别、纠错和翻译全部在本机完成，结果直接输入到当前光标位置，不经过云端。

> 作者：**Ahee52**  
> 状态：0.1.0 预览版  
> 当前发布包：**CPU ASR + 内置 CUDA llama.cpp**  
> 数据目录：`%APPDATA%\ALT-VoiceType`  
> 模型目录：安装目录下的 `models`

---

## 为什么当前是 CPU + Torch 版本

作者已经尝试过更快的 CUDA + PyTorch 方案，但最终没有把它放进当前发布包，原因是客观的：

1. **打包体积**  
   CUDA 版 PyTorch 会额外增加约 2.5–3.5GB 安装体积，安装包增加约 1.5–2.5GB。

2. **显卡和驱动差异**  
   20/30/40/50 系对 CUDA 版本的要求不同。50 系 Blackwell 需要 CUDA 12.8+，旧驱动用户需要先更新驱动。

3. **不同机器环境差异**  
   CUDA Toolkit、驱动、DLL 冲突、PATH 设置都会影响运行；CPU 版更稳定，解压即用。

所以当前发布的是：

```text
CPU + Torch
```

这不是“只能这样”，而是一个**优先保证可运行、可复现、体积可控**的取舍。

**鼓励社区实现 CUDA + PyTorch 加速版。**  
代码中的 ASR 适配器、模型服务和设备配置已经为 CUDA 扩展留出入口；详见下文 [CUDA 扩展](#cuda-扩展)。

---

## 功能

- **完全离线**：ASR、纠错、翻译都在本机运行，默认不发送网络请求。
- **默认固定中文输入**：当前 ASR 输入语言固定为中文，适合中文听写和中文口语翻译。
- **多语言输出**：可输出英语、日语、韩语、西班牙语、法语、德语、俄语、葡萄牙语、意大利语、阿拉伯语、越南语、泰语、印尼语、土耳其语等。
- **上下文纠错**：Qwen3-1.7B-Abliterated 负责同音字、断句、术语和数字规范化。
- **直接输入**：结果自动粘贴到上一个光标位置。
- **双栏主界面**：识别文字 / 转译文字，各自带复制按钮和“已复制”反馈。
- **可拖拽、可缩放**：当前尺寸为最小尺寸，四个角和四条边都可以拖拽缩放。
- **实时音量表**：录音时显示波形；结束后示波器变灰。
- **0.39 秒收尾**：第二次按快捷键后继续采集 0.39 秒，避免截断尾音。
- **ESC 取消录音**：录音中按 ESC 立即丢弃本次录音，不识别、不插入、不写历史。
- **可配置快捷键**：左 Alt、右 Alt、左/右 Alt + 任意按键；不独占 Alt。
- **模型预热**：主界面显示加载/预热/就绪状态。
- **数字规范化**：中文数字自动转阿拉伯数字，例如“二零二五年”→“2025年”，“三千五百块”→“3500块”，“百分之三十”→“30%”。

---

## 输入语言说明

当前版本的输入语言固定为中文：

```text
音频 → 中文 ASR → 中文纠错 → 目标语言翻译
```

这是有意的默认设置，不是限制。

如果希望支持**英文输入**，可以自行调整：

1. 修改 `altvoice/pipeline.py` 中 ASR 调用的语言参数；
2. 修改 `altvoice/config.py` 的 `ASRConfig.language`；
3. 选择支持英语的 ASR 模型或为 Qwen3-ASR 提供英文提示；
4. 在纠错提示词中调整输入语言说明。

也欢迎参与者增加更多小语种输入、纠错和翻译支持。

---

## 三个资源档位

当前固定只使用三个模型，三个档位只是资源策略和输入时长不同：

| 档位 | 输入上限 | 资源模式 | 说明 |
|---|---:|---|---|
| **eco** | 20 秒 | CPU | 最低资源，适合无独显或轻量使用 |
| **standard** | 45 秒 | GPU（目标） | 纠错/翻译使用 GPU；当前 CPU 包中 ASR 仍为 CPU |
| **extended** | 120 秒 | GPU（目标） | 更长输入，适合长句/连续听写 |

### 固定三个模型

| 角色 | 模型 | 大小 |
|---|---|---:|
| ASR | Qwen3-ASR-0.6B | 1.75 GB |
| 纠错 | Qwen3-1.7B-Abliterated Q4 | 1.03 GB |
| 翻译 | Index-Translate-2B Q4 | 1.22 GB |
| **合计** | | **4.00 GB** |

模型文件安装到：

```text
<安装目录>\models
```

例如：

```text
D:\ALT-VoiceType\models
```

默认完整安装后约：

```text
6.0 GB
```

---

## 运行机制

```text
全局键盘钩子
   │  lalt / ralt / lalt+q ...
   ▼
录音线程
   │  sounddevice，20 ms 帧
   ▼
VAD / 静音裁剪
   │
   ▼
ASR（Qwen3-ASR-0.6B，CPU）
   │  中文语音 → 原始文本
   ▼
纠错（Qwen3-1.7B-Abliterated）
   │  同音字、标点、术语、上下文
   ▼
数字规范化
   │  中文数字 → 阿拉伯数字
   ▼
翻译（Index-Translate-2B）
   │  中文 → 目标语言；目标中文时跳过
   ▼
Windows 文本注入
   │  恢复光标，自动粘贴
   ▼
主界面双栏显示
```

- 录音、ASR、纠错、翻译都在后台线程执行。
- 主界面自动出现时不会抢当前输入框焦点。
- 只有触发录音的主按键会被拦截，Alt 本身不被吞掉。
- 录音结束后有 0.39 秒收尾。
- 录音中按 ESC 会取消本次输入。
- 所有模型通过本地 `qwen-asr` / `llama.cpp` 加载。

---

## 安装完整离线版

### 文件

发布页需要下载：

```text
ALT-VoiceType-Setup-0.1.0.exe
ALT-VoiceType-Setup-0.1.0-1.bin
ALT-VoiceType-Setup-0.1.0-2.bin
ALT-VoiceType-Setup-0.1.0-3.bin
SHA256SUMS.txt
README-GitHub.txt
```

每个 `.bin` 都小于 1.8GB，是为了适配 GitHub Release 单文件 2GB 限制。

### 步骤

1. 将 exe 和全部 3 个 bin 下载到同一个文件夹；
2. 不要重命名，不要只下载 exe；
3. 双击 `ALT-VoiceType-Setup-0.1.0.exe`；
4. 安装器会自动查找同目录分卷；
5. 安装完成后启动 `ALT-VoiceType`；
6. 等主界面显示“加载完毕，可以开始输入”；
7. 第一次使用建议先点击 **预热模型**。

### 实测大小

作者本地测试的整合包：

```text
下载文件合计：约 4.42 GB
安装后占用：约 6.0 GB
安装峰值磁盘：约 14 GB
```

模型部分：

```text
4.00 GB
```

程序本体：

```text
约 1.37 GB
```

---

## 缓存与自动清理

这个项目对用户输入信息的处理原则是：

> 音频尽量不落地，文本历史有限保留，缓存可自动清理。

| 数据 | 位置 | 生命周期 |
|---|---|---|
| 录音内存 | 进程内存 | 识别或取消后立即释放 |
| 临时 WAV | `%TEMP%\altvoice_*.wav` | 处理完立即删除；启动时清理 1 小时前的残留 |
| 历史文本 | `%APPDATA%\ALT-VoiceType\history.db` | 默认保留 7 天，最多 500 条，自动清理 |
| 会话上下文 | 进程内存 | 程序退出即消失 |
| 日志 | `%APPDATA%\ALT-VoiceType\logs` | 只记录状态/错误，不保存完整识别文本 |
| 模型文件 | 安装目录 `models` | 不自动删除；卸载程序时随安装目录删除 |

历史记录可以在历史窗口中清空；也可以直接在程序退出后删除：

```text
%APPDATA%\ALT-VoiceType\history.db
```

---

## CUDA 扩展

当前发布包是 **CPU + Torch**，不包含 CUDA 版 PyTorch。

如果社区希望实现更快的 ASR，推荐方向：

```text
PyTorch 2.8 + cu128
CUDA 12.8
NVIDIA 驱动 570+
```

一个 cu128 包可以覆盖：

```text
20 系  sm_75
30 系  sm_86
40 系  sm_89
50 系  sm_120
```

前提：

- 显卡驱动足够新；
- PyTorch wheel 包含对应算力；
- 50 系必须使用 CUDA 12.8 或更新版本。

体积预估：

```text
安装体积增加：约 2.5–3.5 GB
安装包增加：约 1.5–2.5 GB
```

CUDA 版应作为**单独安装包**发布，例如：

```text
ALT-VoiceType-CUDA-Setup-0.1.0.exe
```

不要和 CPU 包混在一起，以免没有 CUDA 环境的用户无法启动。

---

## 从源码运行

要求：

```text
Windows 10/11 64 位
Python 3.11/3.12
麦克风
```

```powershell
git clone https://github.com/aheechan/ALT-VoiceType_Ahee52.git
cd ALT-VoiceType_Ahee52

py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1

pip install -e ".[ui,audio,asr-qwen,download]"
altvoice run
```

环境检查：

```powershell
altvoice health
```

配置：

```text
%APPDATA%\ALT-VoiceType\config.json
```

模型：

```text
<安装目录>\models
```

---

## 快捷键

默认：

```text
左 Alt（lalt）
```

设置中可配置：

```text
lalt
ralt
lalt+q
ralt+space
alt+shift
```

录音中：

```text
ESC → 取消本次录音
```

---

## 数据来源与许可

- 代码：**Apache-2.0**
- ASR：Qwen3-ASR-0.6B
- 纠错：Qwen3-1.7B-Abliterated Q4
- 翻译：Index-Translate-2B Q4
- 模型权重不随 Git 仓库分发；完整安装包内置三个模型
- 使用模型前请遵守各自上游许可证

Qwen3-ASR-0.6B 标准模型：

<https://huggingface.co/Qwen/Qwen3-ASR-0.6B>

Index-Translate-2B：

<https://huggingface.co/IndexTeam/Index-Translate-2B-GGUF>

> 破限/abliterated 纠错模型只随完整安装包分发，本仓库不提供单独链接。

---

## 参与贡献

这是一个完全开源、离线优先的语音输入项目。作者已经尽力在**稳定性、体积和响应速度**之间做取舍，但它还可以更好。

欢迎参与：

- CUDA + PyTorch 加速版
- 英文和小语种输入
- 更多纠错规则和数字规范化
- 更轻量的打包方式
- Windows 兼容性测试（20/30/40/50 系）
- UI、文档和翻译改进

如果这个项目对你有价值，欢迎提交 Issue、PR，或者把它分享给需要的人。

**帮助所有人打通世界沟通的隔阂。**

---

## 手动上传 GitHub

源码仓库请上传到 GitHub 仓库；安装包请上传到 **Releases**，不要提交进 Git 历史。

详细的手把手步骤：

[docs/UPLOAD-MANUAL.md](docs/UPLOAD-MANUAL.md)

---

**ALT-VoiceType_Ahee52** · offline voice input for Windows
