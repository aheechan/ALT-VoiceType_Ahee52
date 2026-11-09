# 双语版 GitHub 上传完整手册

本手册对应两个独立产品：

```text
中文版：ALT-VoiceType
英文版：ALT-VoiceType English
```

原则只有一条：

> **源码进仓库，安装包进 Releases。**

不要反过来。

---

# 一、先认清两个地方

## 1. GitHub 仓库

放：

```text
README.md          (English, GitHub default)
README.zh.md       (Chinese)
altvoice/
tests/
packaging/
docs/
release/
pyproject.toml
LICENSE
NOTICE
CHANGELOG.md
.gitignore
```

不放：

```text
dist/
models/
*.gguf
*.safetensors
*.bin
*.exe
.pylibs/
.whisperlibs/
```

## 2. GitHub Releases

中文版 Release：

```text
v0.1.0-zh
```

附件：

```text
ALT-VoiceType-Setup-0.1.0.exe
ALT-VoiceType-Setup-0.1.0-1.bin
ALT-VoiceType-Setup-0.1.0-2.bin
ALT-VoiceType-Setup-0.1.0-3.bin
README-GitHub.txt
SHA256SUMS.txt
```

英文版 Release：

```text
v0.1.0-en
```

附件：

```text
ALT-VoiceType-EN-Setup-0.1.0.exe
ALT-VoiceType-EN-Setup-0.1.0-1.bin
ALT-VoiceType-EN-Setup-0.1.0-2.bin
ALT-VoiceType-EN-Setup-0.1.0-3.bin
README-EN.txt
SHA256SUMS.txt
```

两个 Release 分开，不要混在一起。

---

# 二、上传前检查

## 1. 进入本地仓库

```powershell
cd C:\Local Repositories\ALT-VoiceType-github\ALT-VoiceType_Ahee52
```

## 2. 确认分支

```powershell
git branch --show-current
```

应为：

```text
main
```

## 3. 确认远程地址

```powershell
git remote -v
```

应只有：

```text
origin  https://github.com/aheechan/ALT-VoiceType_Ahee52.git
```

如果看到 `ghp_`、`github_pat_` 之类的 Token，立刻：

```powershell
git remote set-url origin https://github.com/aheechan/ALT-VoiceType_Ahee52.git
```

并去 GitHub 撤销旧 Token。

## 4. 确认没有模型和安装包

```powershell
git status --short
git ls-files | Select-String -Pattern "\.gguf$|\.safetensors$|\.bin$|\.exe$"
```

第二条命令应该没有输出。

## 5. 确认关键文件存在

```powershell
Test-Path README.md
Test-Path README.zh.md
Test-Path altvoice
Test-Path packaging
Test-Path docs
Test-Path docs/UPLOAD-BILINGUAL.md
```

应全部为 `True`。

## 6. 运行测试

```powershell
python -m unittest discover -s tests
```

应为：

```text
105 tests OK
```

---

# 三、方式 A：GitHub Desktop 上传源码（推荐）

## 1. 安装并登录

安装 GitHub Desktop，使用你的 GitHub 账号登录。

## 2. 添加本地仓库

```text
File → Add local repository
```

选择：

```text
C:\Local Repositories\ALT-VoiceType-github\ALT-VoiceType_Ahee52
```

## 3. 查看变更

左侧会列出：

```text
Changes
History
```

确认没有：

```text
dist
models
.pylibs
.whisperlibs
*.gguf
*.safetensors
```

## 4. 提交

底部填写：

```text
feat: bilingual Chinese and English editions
```

点击：

```text
Commit to main
```

## 5. 发布仓库

首次上传点击：

```text
Publish repository
```

确认：

```text
Name: ALT-VoiceType_Ahee52
```

不要勾选：

```text
Keep this code private
```

## 6. 以后更新

每次修改后：

```text
Changes → 填写说明 → Commit to main → Push origin
```

---

# 四、方式 B：浏览器上传源码

仓库页面：

```text
Add file → Upload files
```

## 第 1 批

拖入：

```text
README.md          (English, GitHub default)
README.zh.md       (Chinese)
LICENSE
NOTICE
CHANGELOG.md
config.example.json
pyproject.toml
.gitignore
altvoice\
docs\
```

提交：

```text
docs: add bilingual source and guides
```

## 第 2 批

再次 Upload files，拖入：

```text
packaging\
release\
scripts\
tests\
benchmarks\
.github\
```

提交：

```text
chore: add packaging, tests and release docs
```

## 注意

- 网页单次最多 100 个文件；
- `.github` 是隐藏目录，需要先在资源管理器开启“显示隐藏的项目”；
- 文件夹拖不进去时，用 GitHub Desktop；
- 不要直接拖入整个 `C:\Local Repositories\ALT-VoiceType`，那会带上 `dist`、`models`。

---

# 五、创建中文版 Release

## 1. 打开

```text
Repository → Releases → Create a new release
```

## 2. 填写

```text
Tag: v0.1.0-zh
Target: main
Title: ALT-VoiceType 中文版 0.1.0
```

## 3. 上传附件

来源目录：

```text
C:\Local Repositories\ALT-VoiceType\dist\installer
```

选择：

```text
ALT-VoiceType-Setup-0.1.0.exe
ALT-VoiceType-Setup-0.1.0-1.bin
ALT-VoiceType-Setup-0.1.0-2.bin
ALT-VoiceType-Setup-0.1.0-3.bin
README-GitHub.txt
SHA256SUMS.txt
```

## 4. 描述

粘贴：

```text
C:\Local Repositories\ALT-VoiceType\dist\installer\README-GitHub.txt
```

或写：

```text
中文版 ALT-VoiceType 0.1.0
CPU ASR + 内置 CUDA llama.cpp
下载 exe 和全部 3 个 bin 到同一文件夹后运行 exe。
```

## 5. 发布

点击：

```text
Publish release
```

---

# 六、创建英文版 Release

再次：

```text
Releases → Create a new release
```

## 1. 填写

```text
Tag: v0.1.0-en
Target: main
Title: ALT-VoiceType English 0.1.0
```

## 2. 上传附件

来源目录：

```text
C:\Local Repositories\ALT-VoiceType\dist\installer-en
```

选择：

```text
ALT-VoiceType-EN-Setup-0.1.0.exe
ALT-VoiceType-EN-Setup-0.1.0-1.bin
ALT-VoiceType-EN-Setup-0.1.0-2.bin
ALT-VoiceType-EN-Setup-0.1.0-3.bin
README-EN.txt
SHA256SUMS.txt
```

## 3. 描述

粘贴：

```text
C:\Local Repositories\ALT-VoiceType\dist\installer-en\README-EN.txt
```

## 4. 发布

```text
Publish release
```

---

# 七、README 中应该写什么

README 必须告诉用户两件事：

## 1. 下载哪个版本

```text
中文用户 → v0.1.0-zh
English users → v0.1.0-en
```

## 2. 模型放在哪里

已安装版：

```text
<安装目录>\models
```

源码中文版：

```text
%LOCALAPPDATA%\ALT-VoiceType\models
```

源码英文版：

```text
%LOCALAPPDATA%\ALT-VoiceType-EN\models
```

配置和日志：

```text
%APPDATA%\ALT-VoiceType
%APPDATA%\ALT-VoiceType-EN
```

---

# 八、模型下载地址

## 中文版

| 角色 | 模型 | 地址 | 放置目录 |
|---|---|---|---|
| ASR | Qwen3-ASR-0.6B | https://huggingface.co/Qwen/Qwen3-ASR-0.6B | `models\qwen3_asr_0_6b` |
| 纠错 | Qwen3-1.7B-Abliterated Q4 | https://huggingface.co/mradermacher/Qwen3-1.7B-abliterated-v2-i1-GGUF | `models\qwen3_1_7b_abliterated_q4` |
| 翻译 | Index-Translate-2B Q4 | https://huggingface.co/IndexTeam/Index-Translate-2B-GGUF | `models\index_translate_2b_q4` |

## 英文版

| 角色 | 模型 | 地址 | 放置目录 |
|---|---|---|---|
| ASR | faster-whisper small.en | https://huggingface.co/Systran/faster-whisper-small.en | `models\faster_whisper_small_en` |
| 纠错 | Qwen3-1.7B-Abliterated Q4 | https://huggingface.co/mradermacher/Qwen3-1.7B-abliterated-v2-i1-GGUF | `models\qwen3_1_7b_abliterated_q4` |
| 翻译 | Index-Translate-2B Q4 | https://huggingface.co/IndexTeam/Index-Translate-2B-GGUF | `models\index_translate_2b_q4` |

> 完整安装包已经包含这些模型。上面的地址是给源码用户和自行构建者使用的。

## 源码版本默认模型目录

中文：

```text
%LOCALAPPDATA%\ALT-VoiceType\models
```

英文：

```text
%LOCALAPPDATA%\ALT-VoiceType-EN\models
```

安装版：

```text
<安装目录>\models
```

---

# 九、从源码构建到可用

## 中文版

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1

pip install -e ".[ui,audio,asr-qwen,download]"

python -m altvoice setup --profile 12gb-balanced
python -m altvoice health
python -m altvoice run
```

## 英文版

```powershell
$env:ALT_VOICE_EDITION = "en"

pip install -e ".[ui,audio,asr-whisper,download]"

python -m altvoice setup --profile 12gb-balanced
python -m altvoice health
python -m altvoice run
```

## 打包程序

中文：

```powershell
$env:PYTHONPATH = ".pylibs"
python -m PyInstaller --noconfirm --workpath build --distpath dist packaging/altvoice.spec
```

英文：

```powershell
$env:PYTHONPATH = ".pylibs;.whisperlibs"
python -m PyInstaller --noconfirm --workpath build-en --distpath dist-en packaging/altvoice-en.spec
```

## 打包安装器

中文：

```powershell
$iscc = "$env:LOCALAPPDATA\Programs\Inno Setup 6\ISCC.exe"
& $iscc "/DSourceDir=$PWD\dist\ALT-VoiceType" `
  "/DModelsDir=D:\ALT-VoiceType\models" `
  "/DLlamaDir=D:\llama.cpp" `
  packaging\installer-bundle.iss
```

英文：

```powershell
& $iscc "/DSourceDir=$PWD\dist-en\ALT-VoiceType-EN" `
  "/DModelsDir=D:\ALT-VoiceType\models" `
  "/DLlamaDir=D:\llama.cpp" `
  "/DWhisperModelDir=$env:LOCALAPPDATA\ALT-VoiceType-EN\models" `
  packaging\installer-en.iss
```

产物：

```text
dist\installer
dist\installer-en
```

---

# 十、上传后验证

## 中文版

1. 下载 exe + 3 个 bin；
2. 放同一文件夹；
3. 运行 exe；
4. 安装目录可自选；
5. 启动后等待预热；
6. 说中文，确认中文输出；
7. 切换日语，确认翻译。

## 英文版

1. 下载 exe + 3 个 bin；
2. 放同一文件夹；
3. 运行 exe；
4. 安装目录可自选；
5. 启动后环境检查应显示：

```text
whisper available
Requested ASR: whisper
```

6. 说英文，确认英文输出；
7. 切换中文，确认中文翻译；
8. 切换日语，确认日语翻译。

---

# 十一、常见错误

## 1. 上传超过 100 个文件

拆成两批，或使用 GitHub Desktop。

## 2. Release 附件超过 2GB

当前每个 bin 约 1.77GB，安全。  
如果未来超过，需要重新分卷。

## 3. 只上传了 exe

必须同时上传全部 bin。  
用户必须把 exe 和 bin 放在同一文件夹。

## 4. 把 bin 提交进了仓库

不要。  
Release 附件不是 Git 文件。

## 5. 中文版和英文版 Release 混在一起

不要。  
使用两个 tag：

```text
v0.1.0-zh
v0.1.0-en
```

## 6. Token 泄露

不要使用：

```text
https://username:ghp_xxx@github.com/...
```

使用 GitHub Desktop 或 SSH。

## 7. Windows 提示未知发布者

安装包未签名。  
这是正常现象，不是上传错误。

---

# 十二、最终检查清单

## 仓库

```text
[ ] README.md
[ ] README.zh.md
[ ] docs/UPLOAD-BILINGUAL.md
[ ] altvoice/
[ ] packaging/altvoice.spec
[ ] packaging/altvoice-en.spec
[ ] packaging/installer-bundle.iss
[ ] packaging/installer-en.iss
[ ] tests/
[ ] 没有 dist/
[ ] 没有 models/
[ ] 没有 *.gguf
[ ] 没有 *.exe
```

## Release v0.1.0-zh

```text
[ ] exe
[ ] 3 个 bin
[ ] README-GitHub.txt
[ ] SHA256SUMS.txt
```

## Release v0.1.0-en

```text
[ ] exe
[ ] 3 个 bin
[ ] README-EN.txt
[ ] SHA256SUMS.txt
```

## 发布后

```text
[ ] README 能正常打开
[ ] 中文 Release 能下载
[ ] 英文 Release 能下载
[ ] 两个安装包都能安装
[ ] 中文版能中文输入
[ ] 英文版能英文输入
[ ] 英文版能翻译成中文
[ ] 英文版能翻译成日语/韩语
```
