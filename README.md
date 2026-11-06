# ALT-VoiceType_Ahee52

[English](README.en.md) | **中文**

![ALT-VoiceType](altvoice/assets/logo.png)

**完全离线的 Windows 语音输入工具：中文语音识别、上下文纠错、自然多语言翻译。**

按一下快捷键开始说话，再按一下结束；识别、纠错和翻译全部在本机完成，结果直接输入到当前光标位置，不经过云端。

> **状态：0.1.0 预览版。** 仓库包含程序源码、模型档位、Windows 热键/注入、PySide6 主界面、打包脚本和测试。发布用的完整离线安装包包含模型权重，不包含在本仓库中。

---

## 目录

- [功能](#功能)
- [运行机制](#运行机制)
- [四个模型档位](#四个模型档位)
- [安装完整离线版](#安装完整离线版)
- [安装精简版](#安装精简版)
- [手动下载非破限模型](#手动下载非破限模型)
- [从源码运行](#从源码运行)
- [快捷键](#快捷键)
- [项目结构](#项目结构)
- [隐私与许可](#隐私与许可)
- [常见问题](#常见问题)

---

## 功能

- **完全离线**：ASR、纠错、翻译都在本机运行，默认不发送网络请求。
- **中文优先**：Qwen3-ASR 对普通话、口音和中英混说表现稳定。
- **上下文纠错**：识别文本经过 1.7B 纠错模型和规则护栏，减少同音字、断句和人名错误。
- **多语言翻译**：Index-Translate 2B / 4B 负责中文到英语、日语、韩语等目标语言的自然翻译。
- **直接输入**：结果自动粘贴到上一个光标位置，不需要手动复制。
- **主界面双栏显示**：一栏显示识别文字，一栏显示转译文字；两栏都有复制按钮和“已复制”反馈。
- **可拖拽主界面**：黑色/白色无边框窗口，默认显示，不抢占输入焦点。
- **实时音量表**：录音时显示波形；松开快捷键后变灰，但后台继续录音 **2 秒**，避免截断尾音。
- **模型预热按钮**：主界面可手动预热，状态实时显示加载/预热/就绪。
- **可配置快捷键**：支持单独左 Alt、单独右 Alt，以及左/右 Alt + 任意按键组合；不独占 Alt，`Alt+Tab` 等系统快捷键仍可用。
- **离线安装包**：提供完整五模型整合包，也提供精简安装包 + 手动模型下载。

## 运行机制

```text
全局键盘钩子
   │  检测 lalt / ralt / lalt+q / ralt+space ...
   ▼
录音线程
   │  sounddevice，20 ms 音频帧
   ▼
VAD / 静音裁剪
   │
   ▼
ASR（Qwen3-ASR）
   │  中文/多语言语音 → 原始文本
   ▼
纠错（Qwen3-1.7B + 护栏）
   │  同音字、标点、术语、上下文
   ▼
翻译（Index-Translate 2B/4B）
   │  中文 → 目标语言；目标为中文时跳过翻译
   ▼
Windows 文本注入
   │  恢复上一个光标位置，自动粘贴
   ▼
主界面双栏显示（识别 / 转译）
```

关键设计：

- 录音、ASR、纠错、翻译在后台线程执行，UI 只负责显示。
- 主界面默认显示，但在自动出现和更新时使用非激活显示，不抢当前输入框焦点。
- 快捷键命中时只拦截真正触发录音的主按键；Alt 本身不被吞掉。
- 第二次按下快捷键后，音频再继续采集 2 秒，然后才停止识别。
- 模型切换会先停止旧模型服务，再按新档位重新加载和预热。
- 所有模型通过本地 `llama.cpp` / `qwen-asr` 加载，不依赖云端 API。

## 四个模型档位

完整安装包包含以下五个模型，组合成四个档位：

| 档位 | ASR | 纠错 | 翻译 | 适用 |
|---|---|---|---|---|
| **safe** | Qwen3-ASR-0.6B | Qwen3-1.7B Abliterated | Index-Translate-2B | 12GB 显存，速度优先 |
| **balanced** | Qwen3-ASR-0.6B | Qwen3-1.7B Abliterated | Qwen3-4B Abliterated | 12GB，翻译质量优先 |
| **12gb-max** | Qwen3-ASR-1.7B Uncensored | Qwen3-1.7B Abliterated | Index-Translate-2B | 12GB，识别质量优先 |
| **16gb-quality** | Qwen3-ASR-1.7B Uncensored | Qwen3-1.7B Abliterated | Qwen3-4B Abliterated | 16GB 以上，质量优先 |

> **破限模型说明**
>
> `12gb-max` 和 `16gb-quality` 使用的 1.7B Uncensored ASR、1.7B Abliterated 纠错、4B Abliterated 翻译只随**完整离线安装包**分发。
> 本仓库和下文只提供**非破限**标准模型的下载地址，方便源码用户和精简版用户自行安装。破限模型不单独提供 Hugging Face 链接。

## 安装完整离线版

### 文件

完整包位于发布页，包含：

```text
ALT-VoiceType_Ahee52-Full-Setup-0.1.0.exe
ALT-VoiceType_Ahee52-Full-Setup-0.1.0-1.bin
ALT-VoiceType_Ahee52-Full-Setup-0.1.0-2.bin
ALT-VoiceType_Ahee52-Full-Setup-0.1.0-3.bin
ALT-VoiceType_Ahee52-Full-Setup-0.1.0-4.bin
ALT-VoiceType_Ahee52-Full-Setup-0.1.0-5.bin
ALT-VoiceType_Ahee52-Full-Setup-0.1.0-6.bin
SHA256SUMS.txt
```

每个 `.bin` 小于 1.8GB，是为了适配 GitHub Release 单文件 2GB 限制。

### 步骤

1. 将 **exe 和全部 6 个 bin** 下载到同一个文件夹。
2. 不要改名，不要只下载 exe。
3. 双击 `ALT-VoiceType_Ahee52-Full-Setup-0.1.0.exe`。
4. 按安装向导完成安装；安装器会自动读取同目录分卷。
5. 启动 `ALT-VoiceType`，等待“加载完毕，可以开始输入”。
6. 第一次使用建议先点主界面的 **预热模型**，预热完成后再开始听写。

### 系统要求

- Windows 10/11 64 位
- 建议 NVIDIA 12GB 显存以上；CPU 也能运行，但速度较慢
- 安装后约 **12.1GB**
- 下载文件约 **9.43GB**
- 安装时建议至少 **25GB** 可用空间（安装包和已安装文件同时存在）
- 麦克风（3.5mm 或 USB 均可）

### 校验

```powershell
certutil -hashfile ALT-VoiceType_Ahee52-Full-Setup-0.1.0.exe SHA256
```

其他分卷的期望值见 `SHA256SUMS.txt`。

## 安装精简版

精简版约 **341MB**，只包含程序，不包含模型：

```text
ALT-VoiceType_Ahee52-Setup-0.1.0.exe
```

安装后首次启动会检查模型；缺失时可在设置/安装向导中下载，或按下一节手动下载。

精简版适合：

- 已经有模型文件的用户；
- 只想先安装程序、再按需选择模型的用户；
- 磁盘空间有限的用户。

## 手动下载非破限模型

以下模型均为**非破限标准模型**。完整安装包中的破限模型不在此列。

统一模型根目录：

```text
%LOCALAPPDATA%\AltVoice\models
```

在 PowerShell 中可写为：

```powershell
$m = "$env:LOCALAPPDATA\AltVoice\models"
```

### 1. ASR：Qwen3-ASR-0.6B

Hugging Face：

<https://huggingface.co/Qwen/Qwen3-ASR-0.6B>

存放路径：

```text
%LOCALAPPDATA%\AltVoice\models\qwen3_asr_0_6b
```

下载：

```powershell
huggingface-cli download Qwen/Qwen3-ASR-0.6B `
  --local-dir "$env:LOCALAPPDATA\AltVoice\models\qwen3_asr_0_6b"
```

这是 **safe / balanced** 两个档位的标准 ASR。

### 2. ASR：Qwen3-ASR-1.7B（标准版）

Hugging Face：

<https://huggingface.co/Qwen/Qwen3-ASR-1.7B>

存放路径：

```text
%LOCALAPPDATA%\AltVoice\models\qwen3_asr_1_7b
```

下载：

```powershell
huggingface-cli download Qwen/Qwen3-ASR-1.7B `
  --local-dir "$env:LOCALAPPDATA\AltVoice\models\qwen3_asr_1_7b"
```

这是 `12gb-max` / `16gb-quality` 中破限 ASR 的**非破限替代品**。使用它需要把配置文件中的 `asr.model_path` 指向此目录。

### 3. 纠错：Qwen3-1.7B-Instruct Q8

Hugging Face：

<https://huggingface.co/Qwen/Qwen3-1.7B-GGUF>

文件名：

```text
Qwen3-1.7B-Q8_0.gguf
```

存放路径：

```text
%LOCALAPPDATA%\AltVoice\models\qwen3_1_7b_instruct_q4\Qwen3-1.7B-Q8_0.gguf
```

下载：

```powershell
huggingface-cli download Qwen/Qwen3-1.7B-GGUF `
  --include "*Qwen3-1.7B-Q8_0.gguf" `
  --local-dir "$env:LOCALAPPDATA\AltVoice\models\qwen3_1_7b_instruct_q4"
```

### 4. 翻译：Index-Translate-2B Q4

Hugging Face：

<https://huggingface.co/IndexTeam/Index-Translate-2B-GGUF>

文件名：

```text
Index-Translate-2B.Q4_K_M.gguf
```

存放路径：

```text
%LOCALAPPDATA%\AltVoice\models\index_translate_2b_q4\Index-Translate-2B.Q4_K_M.gguf
```

下载：

```powershell
huggingface-cli download IndexTeam/Index-Translate-2B-GGUF `
  --include "*Index-Translate-2B.Q4_K_M.gguf" `
  --local-dir "$env:LOCALAPPDATA\AltVoice\models\index_translate_2b_q4"
```

### 5. 翻译：Qwen3-4B-Instruct Q4（标准版）

Hugging Face：

<https://huggingface.co/Qwen/Qwen3-4B-GGUF>

文件名：

```text
Qwen3-4B-Q4_K_M.gguf
```

存放路径：

```text
%LOCALAPPDATA%\AltVoice\models\qwen3_4b_instruct_q4\Qwen3-4B-Q4_K_M.gguf
```

下载：

```powershell
huggingface-cli download Qwen/Qwen3-4B-GGUF `
  --include "*Qwen3-4B-Q4_K_M.gguf" `
  --local-dir "$env:LOCALAPPDATA\AltVoice\models\qwen3_4b_instruct_q4"
```

这是 `balanced` / `16gb-quality` 中破限 4B 翻译的**非破限替代品**。

### 手动配置标准模型

模型下载后，编辑：

```text
%APPDATA%\AltVoice\config.json
```

确保以下字段指向实际文件：

```json
{
  "asr": {
    "model_path": "C:\\Users\\<你>\\AppData\\Local\\AltVoice\\models\\qwen3_asr_0_6b"
  },
  "corrector": {
    "model_path": "C:\\Users\\<你>\\AppData\\Local\\AltVoice\\models\\qwen3_1_7b_instruct_q4\\Qwen3-1.7B-Q8_0.gguf"
  },
  "translator": {
    "model_path": "C:\\Users\\<你>\\AppData\\Local\\AltVoice\\models\\index_translate_2b_q4\\Index-Translate-2B.Q4_K_M.gguf"
  }
}
```

注意：完整安装包中的档位预设默认指向破限模型路径。手动换成标准模型后，不要再次在设置中切换档位，否则路径会被重置。

### 国内网络

如果 Hugging Face 直连较慢，可临时使用镜像：

```powershell
$env:HF_ENDPOINT = "https://hf-mirror.com"
```

下载命令不变。

## 从源码运行

要求：

- Windows 10/11 64 位
- Python 3.11 或 3.12
- NVIDIA 驱动（可选；CPU 也可运行）
- 麦克风

```powershell
git clone https://github.com/<your-name>/ALT-VoiceType_Ahee52.git
cd ALT-VoiceType_Ahee52

py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1

pip install -e ".[ui,audio,asr-qwen,download]"
```

首次运行：

```powershell
altvoice run
```

只检查环境：

```powershell
altvoice health
```

程序会使用 `%APPDATA%\AltVoice\config.json`，模型默认从 `%LOCALAPPDATA%\AltVoice\models` 读取。

## 快捷键

默认：

```text
左 Alt（lalt）
```

设置中可以配置：

```text
lalt
ralt
lalt+q
ralt+space
lalt+shift
alt+q
```

- 左 Alt / 右 Alt 分开识别。
- 不再独占 Alt：`Alt+Tab`、`Alt+F4` 等系统组合仍然可用。
- 只有真正触发录音的组合主按键会被拦截。
- 保存后立即生效，无需重启。

## 项目结构

```text
altvoice/
  asr/             ASR 适配器（Qwen3-ASR、Sherpa 回退）
  correct/         纠错模型、提示词、规则护栏
  translate/       翻译提示词、客户端和清理逻辑
  llm/             OpenAI 兼容的本地 llama.cpp 客户端
  hotkey/          Windows 全局钩子、左/右 Alt 组合键
  inject/          Windows 文本注入、焦点恢复
  ui/              PySide6 托盘、主界面、设置、历史
  audio.py         麦克风采集和音量回调
  pipeline.py      ASR → 纠错 → 翻译 → 注入
  app.py           控制器、录音状态机、2 秒收尾
  models.py        模型目录和四个档位
  servers.py       llama.cpp 模型服务管理

packaging/         PyInstaller spec、Inno Setup 安装器、整合包脚本
tests/             单元测试和 UI smoke tests
docs/              架构、模型、运行、发布文档
```

## 隐私与许可

- 默认完全离线；音频不写入磁盘。
- 历史记录保存在本地 SQLite，可在设置中关闭/清理。
- 代码采用 **Apache-2.0**。
- 模型权重不随仓库分发；每个模型遵循其上游许可证。
- 完整离线安装包中包含的破限模型只随安装包分发，本仓库不提供单独链接。

## 常见问题

### 安装器提示找不到分卷

确认 exe 和 `-1.bin` 到 `-6.bin` 在**同一个文件夹**，且文件名没有被改成 `.bin.txt` 或加上 `(1)`。

### SmartScreen 提示未知发布者

当前安装包未做代码签名。选择“更多信息 → 仍要运行”，或用 `SHA256SUMS.txt` 校验文件完整性。

### 按 Alt 没有反应

确认设置中的快捷键是 `lalt`/`ralt`，而不是被其他软件占用；确认程序已预热完成。

### 识别很慢

- 确认使用的是 GPU，而不是 CPU；
- `12gb-max`/`16gb-quality` 使用 1.7B ASR，CPU 上会明显变慢；
- 先点“预热模型”，避免第一次识别承担加载时间；
- 关闭占用显存的其他程序。

### 没有自动粘贴

确认目标输入框支持 Ctrl+V；部分游戏或管理员权限窗口会阻止注入，尝试以相同权限运行程序。

---

**ALT-VoiceType_Ahee52** · offline voice input for Windows
