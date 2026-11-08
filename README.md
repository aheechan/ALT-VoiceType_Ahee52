# ALT-VoiceType_Ahee52

[English](README.en.md) | **中文**

![ALT-VoiceType](altvoice/assets/logo.png)

**完全离线的 Windows 语音输入工具：中文语音识别、上下文纠错、自然多语言翻译。**

按一下快捷键开始说话，再按一下结束；识别、纠错和翻译全部在本机完成，结果直接输入到当前光标位置，不经过云端。

> 作者：**Ahee52**  
> 状态：0.1.0 预览版  
> 当前发布包：**CPU ASR + 内置 CUDA llama.cpp**  
> 配置与日志：`%APPDATA%\ALT-VoiceType`  
> 安装版模型：`<安装目录>\models`  
> 源码版模型：`%LOCALAPPDATA%\ALT-VoiceType\models`

---

## 版本选择（先看这里）

| | 中文版 | 英文版 |
|---|---|---|
| 产品名 | ALT-VoiceType | ALT-VoiceType English |
| 默认输入 | 中文 | English |
| 默认输出 | 中文 | English |
| ASR | Qwen3-ASR-0.6B | faster-whisper small.en |
| 安装包 | 约 4.42GB | 约 3.57GB |
| 安装后 | 约 6.0GB | 约 5.6GB |
| 数据目录 | `%APPDATA%\ALT-VoiceType` | `%APPDATA%\ALT-VoiceType-EN` |
| Release | `v0.1.0-zh` | `v0.1.0-en` |

中文用户下载中文版，English users download the English edition。两个版本可以同时安装。

完整上传流程见 [docs/UPLOAD-BILINGUAL.md](docs/UPLOAD-BILINGUAL.md)。

---

## 目录

- [版本选择（先看这里）](#版本选择先看这里)
- [这个仓库是什么](#这个仓库是什么)
- [两条使用路线](#两条使用路线)
- [作者的取舍：为什么是 CPU ASR](#作者的取舍为什么是-cpu-asr)
- [固定模型与三个档位](#固定模型与三个档位)
- [中文版模型下载与放置](#中文版模型下载与放置)
- [英文版模型下载与放置](#英文版模型下载与放置)
- [方式一：一键安装包](#方式一一键安装包)
- [方式二：从源码体验](#方式二从源码体验)
- [构建两个版本](#构建两个版本)
- [运行机制](#运行机制)
- [缓存与自动清理](#缓存与自动清理)
- [CUDA 扩展](#cuda-扩展)
- [快捷键与 ESC](#快捷键与-esc)
- [开发、测试与打包](#开发测试与打包)
- [常见问题](#常见问题)
- [参与贡献](#参与贡献)
- [许可](#许可)

---

## 这个仓库是什么

这是一个可以直接运行的 Windows 语音输入项目，不只是安装包下载页。

仓库包含：

```text
altvoice/          Python 包：ASR、纠错、翻译、热键、注入、UI
tests/             105 个单元/UI 测试
packaging/         PyInstaller + Inno Setup 打包脚本
scripts/           辅助脚本
docs/              架构、部署、上传说明
benchmarks/        ASR 测试清单
```

它适合：

- 直接下载安装包使用；
- 从源码运行和修改；
- 研究离线 ASR、纠错、翻译的完整链路；
- 贡献 CUDA 加速、英语/小语种输入或新的 UI。

---

## 两条使用路线

| 路线 | 适合 | 需要 |
|---|---|---|
| **一键安装包** | 普通用户 | 下载 4.42GB 分卷，双击安装 |
| **源码运行** | 开发者、想体验仓库的人 | Python、模型文件、麦克风 |

安装包是“开箱即用”；源码路线是“可修改、可实验、可贡献”。

---

## 作者的取舍：为什么是 CPU ASR

作者已经尝试过更快的 **CUDA + PyTorch** 方案，但最终没有把它放进当前发布包。

原因：

1. **打包体积**  
   CUDA 版 PyTorch 会增加约 2.5–3.5GB 安装体积，安装包增加约 1.5–2.5GB。

2. **显卡与驱动差异**  
   RTX 20/30/40/50 系对 CUDA 版本要求不同。50 系 Blackwell 需要 CUDA 12.8+，老驱动必须先更新。

3. **机器环境差异**  
   CUDA Toolkit、驱动、DLL、PATH 都可能冲突；CPU 版更容易复现和排错。

当前发布包的组合是：

```text
ASR：CPU + Torch
纠错/翻译：内置 CUDA llama.cpp
```

这不是“只能这样”，而是一个优先保证**可运行、可复现、体积可控**的选择。

**鼓励社区实现 CUDA + PyTorch 加速版。**  
ASR 适配器、设备配置和模型服务已经预留了扩展入口。

---

## 固定模型与三个档位

当前固定只使用三个模型：

| 角色 | 模型 | 大小 |
|---|---|---:|
| ASR | Qwen3-ASR-0.6B | 1.75 GB |
| 纠错 | Qwen3-1.7B-Abliterated Q4 | 1.03 GB |
| 翻译 | Index-Translate-2B Q4 | 1.22 GB |
| **合计** | | **4.00 GB** |

三个档位只改变输入时长和资源策略：

| 档位 | 输入上限 | 资源模式 | 说明 |
|---|---:|---|---|
| **eco** | 20 秒 | CPU | 最低资源 |
| **standard** | 45 秒 | GPU（目标） | 默认档位 |
| **extended** | 120 秒 | GPU（目标） | 长句/连续听写 |

当前 CPU ASR 发布包中，`standard` / `extended` 的纠错和翻译使用 GPU；ASR 仍是 CPU。

---

## 英文独立版

英文输入版是独立产品，不和中文版共用安装目录或数据目录：

```text
产品：ALT-VoiceType English
安装包：ALT-VoiceType-EN-Setup-0.1.0.exe
数据：%APPDATA%\ALT-VoiceType-EN
ASR：faster-whisper small.en（英文专用，CPU）
纠错/翻译：Qwen3-1.7B + Index-Translate-2B
```

英文版安装包约 **3.57GB**，安装后约 **5.6GB**。

英文版特点：

- 默认输入 English
- 默认输出 English
- 主界面、设置、托盘菜单全部英文
- 独立 AppId、独立快捷方式、独立历史记录
- 可与中文版同时安装
- 单独发布：`v0.1.0-en`

源码运行英文版：

```powershell
$env:ALT_VOICE_EDITION = "en"
python -m altvoice run
```

构建英文版：

```powershell
python -m PyInstaller --noconfirm --workpath build-en --distpath dist-en packaging/altvoice-en.spec
```

## 方式一：一键安装包

### 需要下载

```text
ALT-VoiceType-Setup-0.1.0.exe
ALT-VoiceType-Setup-0.1.0-1.bin
ALT-VoiceType-Setup-0.1.0-2.bin
ALT-VoiceType-Setup-0.1.0-3.bin
SHA256SUMS.txt
README-GitHub.txt
```

全部放在同一个文件夹，双击 exe。

安装时**会显示目录选择页**，你可以选择 C/D/E 任意磁盘。

### 实测大小

```text
安装包：约 4.42 GB
安装后：约 6.0 GB
安装峰值磁盘：约 14 GB
```

包含：

- 程序本体
- 三个模型
- 内置 CUDA llama.cpp
- 配置和日志目录

### 系统要求

```text
Windows 10/11 64 位
麦克风
可选 NVIDIA 显卡（50 系需要较新驱动）
```

### 安装后

```text
<安装目录>\ALT-VoiceType.exe
<安装目录>\models
<安装目录>\llama
```

配置文件：

```text
%APPDATA%\ALT-VoiceType\config.json
```

---

## 方式二：从源码体验

这是 GitHub 仓库最有价值的部分：你可以直接运行和修改它。

### 1. 环境

```text
Windows 10/11 64 位
Python 3.11 或 3.12
Git
麦克风
可选：NVIDIA 驱动、ffmpeg
```

### 2. 克隆

```powershell
git clone https://github.com/aheechan/ALT-VoiceType_Ahee52.git
cd ALT-VoiceType_Ahee52
```

### 3. 创建虚拟环境

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 4. 安装依赖

```powershell
pip install -e ".[ui,audio,asr-qwen,download]"  # 中文版
pip install -e ".[ui,audio,asr-whisper,download]"  # 英文版
```

需要 sherpa 回退时：

```powershell
pip install -e ".[ui,audio,asr-qwen,asr-sherpa,download]"
```

### 5. 准备模型

源码模式默认从：

```text
%LOCALAPPDATA%\ALT-VoiceType\models
```

读取模型。

可以手动下载，也可以把安装包里的 `models` 目录复制到这个位置。

### 6. 写配置

```powershell
python -m altvoice setup --profile 12gb-balanced
```

这会生成：

```text
%APPDATA%\ALT-VoiceType\config.json
```

### 7. 检查环境

```powershell
python -m altvoice health
```

输出应包含：

```text
[OK] asr
[OK] corrector
[OK] translator
```

### 8. 启动

```powershell
python -m altvoice run
```

或者安装后的命令：

```powershell
altvoice run
```

### 9. 源码模式的日志

```text
%APPDATA%\ALT-VoiceType\logs\app.log
%APPDATA%\ALT-VoiceType\logs\corrector.log
%APPDATA%\ALT-VoiceType\logs\translator.log
```

---

## 中文版模型下载与放置

源码模式需要自己准备模型。安装版已经包含这些文件，目录是 `<安装目录>\models`。

### 1. ASR：Qwen3-ASR-0.6B

Hugging Face：

<https://huggingface.co/Qwen/Qwen3-ASR-0.6B>

放置目录：

```text
%LOCALAPPDATA%\ALT-VoiceType\models\qwen3_asr_0_6b
```

下载：

```powershell
huggingface-cli download Qwen/Qwen3-ASR-0.6B `
  --local-dir "$env:LOCALAPPDATA\ALT-VoiceType\models\qwen3_asr_0_6b"
```

### 2. 纠错：Qwen3-1.7B-Abliterated Q4

完整安装包会内置该模型。

Hugging Face：

<https://huggingface.co/mradermacher/Qwen3-1.7B-abliterated-v2-i1-GGUF>

源码用户可以下载该仓库中的 Q4_K_M GGUF，放到下面的目录：

```text
%LOCALAPPDATA%\ALT-VoiceType\models\qwen3_1_7b_abliterated_q4
```

配置字段：

```json
"corrector": {
  "model_path": "...\\qwen3_1_7b_abliterated_q4\\你的模型.gguf"
}
```

### 3. 翻译：Index-Translate-2B Q4

Hugging Face：

<https://huggingface.co/IndexTeam/Index-Translate-2B-GGUF>

目标文件：

```text
Index-Translate-2B.Q4_K_M.gguf
```

目标目录：

```text
%LOCALAPPDATA%\ALT-VoiceType\models\index_translate_2b_q4
```

下载：

```powershell
huggingface-cli download IndexTeam/Index-Translate-2B-GGUF `
  --include "*Index-Translate-2B.Q4_K_M.gguf" `
  --local-dir "$env:LOCALAPPDATA\ALT-VoiceType\models\index_translate_2b_q4"
```

### 4. llama.cpp

源码模式还需要 `llama-server`：

```text
llama-server.exe
```

安装方式：

```powershell
winget install ggml.llamacpp
```

完整安装包已经内置 CUDA 版 `llama-server`，源码模式需要自己准备。

---

## 英文版模型下载与放置

英文版使用自己的数据目录和模型目录：

```text
%LOCALAPPDATA%\ALT-VoiceType-EN\models
```

### 1. ASR：faster-whisper small.en

Hugging Face：

<https://huggingface.co/Systran/faster-whisper-small.en>

放置目录：

```text
%LOCALAPPDATA%\ALT-VoiceType-EN\models\faster_whisper_small_en
```

下载：

```powershell
huggingface-cli download Systran/faster-whisper-small.en `
  --local-dir "$env:LOCALAPPDATA\ALT-VoiceType-EN\models\faster_whisper_small_en"
```

### 2. 纠错：Qwen3-1.7B-Abliterated Q4

同一个模型，放到英文版目录：

```text
%LOCALAPPDATA%\ALT-VoiceType-EN\models\qwen3_1_7b_abliterated_q4
```

### 3. 翻译：Index-Translate-2B Q4

同一个模型，放到英文版目录：

```text
%LOCALAPPDATA%\ALT-VoiceType-EN\models\index_translate_2b_q4
```

目标文件：

```text
Index-Translate-2B.Q4_K_M.gguf
```

下载：

```powershell
huggingface-cli download IndexTeam/Index-Translate-2B-GGUF `
  --include "*Index-Translate-2B.Q4_K_M.gguf" `
  --local-dir "$env:LOCALAPPDATA%\ALT-VoiceType-EN\models\index_translate_2b_q4"
```

### 4. 源码启动英文版

```powershell
$env:ALT_VOICE_EDITION = "en"
pip install -e ".[ui,audio,asr-whisper,download]"
python -m altvoice setup --profile 12gb-balanced
python -m altvoice health
python -m altvoice run
```

`health` 中应出现：

```text
whisper    available
Requested ASR: whisper
```

---

## 构建两个版本

### 中文版程序

```powershell
$env:ALT_VOICE_EDITION = "zh"
$env:PYTHONPATH = ".pylibs"
python -m PyInstaller --noconfirm --workpath build --distpath dist packaging/altvoice.spec
```

### 英文版程序

```powershell
$env:ALT_VOICE_EDITION = "en"
$env:PYTHONPATH = ".pylibs;.whisperlibs"
python -m PyInstaller --noconfirm --workpath build-en --distpath dist-en packaging/altvoice-en.spec
```

### 中文版安装器

```powershell
$iscc = "$env:LOCALAPPDATA\Programs\Inno Setup 6\ISCC.exe"
& $iscc "/DSourceDir=$PWD\dist\ALT-VoiceType" `
  "/DModelsDir=D:\ALT-VoiceType\models" `
  "/DLlamaDir=D:\llama.cpp" `
  packaging\installer-bundle.iss
```

输出：

```text
dist\installer
```

### 英文版安装器

```powershell
& $iscc "/DSourceDir=$PWD\dist-en\ALT-VoiceType-EN" `
  "/DModelsDir=D:\ALT-VoiceType\models" `
  "/DLlamaDir=D:\llama.cpp" `
  "/DWhisperModelDir=$env:LOCALAPPDATA\ALT-VoiceType-EN\models" `
  packaging\installer-en.iss
```

输出：

```text
dist\installer-en
```

### 上传 GitHub

完整手把手流程见：

[docs/UPLOAD-BILINGUAL.md](docs/UPLOAD-BILINGUAL.md)

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
   ▼
ASR（Qwen3-ASR-0.6B）
   ▼
纠错（Qwen3-1.7B-Abliterated）
   ▼
数字规范化
   ▼
翻译（Index-Translate-2B）
   ▼
Windows 文本注入
   ▼
双栏主界面
```

关键设计：

- 录音、ASR、纠错、翻译在后台线程；
- 主窗口自动出现时不抢焦点；
- 只拦截真正触发录音的主按键，Alt 不被独占；
- 录音结束有 **0.39 秒**收尾；
- 录音中按 **ESC** 取消；
- 本地 `qwen-asr` / `llama.cpp` 推理，无云端 API。

---

## 缓存与自动清理

| 数据 | 位置 | 生命周期 |
|---|---|---|
| 录音内存 | 进程内存 | 识别/取消后立即释放 |
| 临时 WAV | `%TEMP%\altvoice_*.wav` | 处理完删除；启动清 1 小时前残留 |
| 历史文本 | `%APPDATA%\ALT-VoiceType\history.db` | 7 天 / 500 条自动清理 |
| 会话上下文 | 进程内存 | 退出即消失 |
| 日志 | `%APPDATA%\ALT-VoiceType\logs` | 不保存完整识别文本 |
| 模型 | 安装目录 `models` | 卸载时随目录删除 |

手动清空历史：

```powershell
Remove-Item "$env:APPDATA\ALT-VoiceType\history.db"
```

---

## CUDA 扩展

当前发布包不包含 CUDA 版 PyTorch，ASR 走 CPU。

如果要做 CUDA ASR，建议：

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

- 驱动足够新；
- wheel 包含对应算力；
- 50 系必须 CUDA 12.8+。

体积预估：

```text
安装后增加：约 2.5–3.5 GB
安装包增加：约 1.5–2.5 GB
```

CUDA 版应单独发布：

```text
ALT-VoiceType-CUDA-Setup-0.1.0.exe
```

不要和 CPU 包混在一起。

---

## 快捷键与 ESC

默认：

```text
左 Alt（lalt）
```

可配置：

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

取消后不会识别、不会插入、不会写历史。

---

## 开发、测试与打包

### 测试

```powershell
python -m unittest discover -s tests
```

当前：

```text
105 tests OK
```

### 打包程序

```powershell
$env:PYTHONPATH = ".pylibs"
python -m PyInstaller --noconfirm --workpath build --distpath dist packaging/altvoice.spec
```

### 打包安装器

```powershell
$iscc = "$env:LOCALAPPDATA\Programs\Inno Setup 6\ISCC.exe"
& $iscc "/DSourceDir=$PWD\dist\ALT-VoiceType" packaging\installer.iss
```

完整包需要同时指定模型目录和 llama.cpp 目录：

```powershell
& $iscc "/DSourceDir=$PWD\dist\ALT-VoiceType" `
  "/DModelsDir=$PWD\models" `
  "/DLlamaDir=C:\path\to\llama.cpp" `
  packaging\installer-bundle.iss
```

### 手动上传到 GitHub

见：

[docs/UPLOAD-MANUAL.md](docs/UPLOAD-MANUAL.md)

---

## 常见问题

### 翻译一直输出中文

先检查：

```text
%APPDATA%\ALT-VoiceType\logs\translator.log
```

常见原因：

1. 没有 `llama-server`；
2. GPU 初始化失败；
3. 模型服务没有拿到 `content`。

完整安装包已经内置 CUDA `llama-server`，并使用：

```text
--reasoning off
```

如果仍然中文，请提交日志。

### 按 Alt 没反应

- 检查设置中的快捷键；
- 等待“加载完毕”；
- 检查日志是否有热键错误。

### 识别很慢

- CPU ASR 首次加载较慢；
- 先点击“预热模型”；
- 长音频受 20/45/120 秒档位限制。

### 安装时提示未知发布者

安装包未做代码签名。  
选择“更多信息 → 仍要运行”，或用 `SHA256SUMS.txt` 校验。

---

## 参与贡献

这是一个完全开源、离线优先的项目。作者已经在稳定性、体积和响应速度之间做了取舍，但它还可以更好。

欢迎：

- CUDA + PyTorch 加速
- 英文和小语种输入
- 纠错规则与数字规范化
- 更轻量的打包
- RTX 20/30/40/50 兼容性测试
- UI、文档、翻译

如果这个项目对你有价值，欢迎 Issue、PR 或分享给需要的人。

**帮助所有人打通世界沟通的隔阂。**

---

## 许可

- 代码：**Apache-2.0**
- 模型权重不随 Git 仓库分发
- 使用模型时遵守各上游许可证

---

**ALT-VoiceType_Ahee52** · offline voice input for Windows
