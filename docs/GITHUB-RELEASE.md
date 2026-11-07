# GitHub 发布与上传流程

本文对应仓库根目录和 `dist/bundle` 的发布文件。原则：

- **源码进 Git 仓库**
- **安装包和模型分卷进 GitHub Release**
- **不要把 3.93GB 的 bin 提交到 Git 仓库**

## 1. 仓库结构

上传到 GitHub 的源码目录：

```text
C:\Local Repositories\ALT-VoiceType-github\ALT-VoiceType_Ahee52\
```

包含：

```text
README.md              中文说明
README.en.md           英文说明
LICENSE
NOTICE
altvoice/              源代码
tests/
packaging/             打包脚本和安装器脚本
docs/
pyproject.toml
```

以下内容不要提交：

```text
dist/
dist37/
build*/
models/
.pylibs/
*.gguf
*.safetensors
```

仓库已有的 `.gitignore` 已经覆盖这些路径。

## 2. 创建 GitHub 仓库

在 GitHub 新建一个空仓库，例如：

```text
ALT-VoiceType_Ahee52
```

不要勾选自动生成 README、.gitignore 或 license，避免和本地文件冲突。

## 3. 本地初始化并推送

在源码目录打开 PowerShell：

```powershell
cd C:\Local Repositories\ALT-VoiceType-github\ALT-VoiceType_Ahee52

git init
git add .
git commit -m "Initial ALT-VoiceType_Ahee52 source release"

git branch -M main
git remote add origin https://github.com/<你的用户名>/ALT-VoiceType_Ahee52.git
git push -u origin main
```

如果仓库地址使用 SSH：

```powershell
git remote add origin git@github.com:<你的用户名>/ALT-VoiceType_Ahee52.git
git push -u origin main
```

推送前检查：

```powershell
git status
git ls-files | Select-String -Pattern "\.gguf$|\.safetensors$|^dist"
```

不应该出现模型权重或安装分卷。

## 4. 创建 Release

1. 打开 GitHub 仓库页面。
2. 点击 **Releases → Draft a new release**。
3. Tag 填：

```text
v0.1.0
```

4. Release title 填：

```text
ALT-VoiceType_Ahee52 0.1.0
```

5. 上传以下文件，全部来自：

```text
C:\Local Repositories\ALT-VoiceType\dist\installer\
```

文件清单：

```text
ALT-VoiceType-Setup-0.1.0.exe
ALT-VoiceType-Setup-0.1.0-1.bin
ALT-VoiceType-Setup-0.1.0-2.bin
ALT-VoiceType-Setup-0.1.0-3.bin
ALT-VoiceType-Setup-0.1.0-4.bin
ALT-VoiceType-Setup-0.1.0-5.bin
ALT-VoiceType-Setup-0.1.0-3.bin
SHA256SUMS.txt
README-GitHub.txt
```

6. 在 Release 描述中粘贴 `README-GitHub.txt` 的安装说明，或者链接到仓库 README。
7. 点击 **Publish release**。

## 5. GitHub 限制

- 单个 Release asset 最大 **2GB**。
- 当前每个 `.bin` 约 **1.77GB**，不会触发限制。
- 全部 8 个文件合计约 **3.93GB**。
- GitHub 网页上传大文件可能较慢；建议使用 GitHub CLI：

```powershell
gh release create v0.1.0 `
  --title "ALT-VoiceType_Ahee52 0.1.0" `
  --notes-file "C:\Local Repositories\ALT-VoiceType\dist\installer\README-GitHub.txt" `
  "C:\Local Repositories\ALT-VoiceType\dist\installer\ALT-VoiceType-Setup-0.1.0.exe" `
  "C:\Local Repositories\ALT-VoiceType\dist\installer\ALT-VoiceType-Setup-0.1.0-*.bin" `
  "C:\Local Repositories\ALT-VoiceType\dist\installer\SHA256SUMS.txt" `
  "C:\Local Repositories\ALT-VoiceType\dist\installer\README-GitHub.txt"
```

`gh` 需要先登录：

```powershell
gh auth login
```

## 6. 不要做的事

- 不要只上传 `.exe`；没有 6 个 `.bin` 无法安装完整版。
- 不要重命名 `.exe` 或 `.bin`；安装器按文件名查找分卷。
- 不要把 `.bin` 提交进 Git 历史；会让仓库变成数十 GB。
- 不要在 README 中放破限模型的单独下载链接；破限模型只随完整安装包分发。
- 不要使用 FAT32 存放 9GB 文件；Windows 安装包在 NTFS 上使用。

## 7. 发布后检查

在一台干净机器或新目录中测试：

1. 下载全部 exe + bin 到同一目录。
2. 校验 SHA256：

```powershell
certutil -hashfile ALT-VoiceType-Setup-0.1.0.exe SHA256
```

3. 运行安装器。
4. 启动后等待模型预热。
5. 测试四个档位、快捷键、自动粘贴和两个复制按钮。

## 8. 精简版

如果不想发布 3.93GB 全量包，可以只发布：

```text
ALT-VoiceType_Ahee52-Setup-0.1.0.exe
```

约 341MB。用户按仓库 README 的“手动下载非破限模型”章节自行放置模型。

## 9. 校验清单

发布前确认：

- `README.md` 和 `README.en.md` 都存在；
- README 中的 Hugging Face 链接可以打开；
- 模型存放路径和程序实际读取路径一致；
- `SHA256SUMS.txt` 与当前分卷匹配；
- 安装包可以找到同目录的 3 个 bin；
- 完整包安装后约 5.4GB，四个档位都能选择；
- 没有把 `.gguf`、`.safetensors` 或 `dist/` 提交到 Git。




