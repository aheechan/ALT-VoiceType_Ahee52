# 手动上传 GitHub 完整步骤

这份文档面向第一次上传项目的人，全部使用浏览器或 GitHub Desktop，不需要命令行。

---

# 一、先分清两个地方

## 1. GitHub 仓库

放：

```text
README.md
README.zh.md
altvoice/
tests/
packaging/
docs/
release/
pyproject.toml
LICENSE
NOTICE
...
```

不放：

```text
dist/
build/
models/
.pylibs/
*.gguf
*.safetensors
*.bin
*.exe
```

## 2. GitHub Releases

放：

```text
ALT-VoiceType-Setup-0.1.0.exe
ALT-VoiceType-Setup-0.1.0-1.bin
ALT-VoiceType-Setup-0.1.0-2.bin
ALT-VoiceType-Setup-0.1.0-3.bin
SHA256SUMS.txt
README-GitHub.txt
```

Release 是 GitHub 提供给二进制附件的区域，不会进入 Git 历史。

---

# 二、创建空仓库

打开：

```text
https://github.com/new
```

填写：

```text
Repository name: ALT-VoiceType_Ahee52
Visibility: Public
```

不要勾选：

```text
Add a README file
Add .gitignore
Choose a license
```

点击 **Create repository**。

---

# 三、方式 A：浏览器手动上传源码

仓库页面点击：

```text
Add file → Upload files
```

## 第 1 批

拖入以下内容：

```text
README.md
README.zh.md
LICENSE
NOTICE
CHANGELOG.md
config.example.json
pyproject.toml
.gitignore
altvoice\
docs\
```

约 70 个文件以内。

提交信息：

```text
docs: add source and bilingual README
```

点击 **Commit changes**。

## 第 2 批

再次：

```text
Add file → Upload files
```

拖入：

```text
packaging\
release\
scripts\
tests\
benchmarks\
.github\
```

提交信息：

```text
chore: add packaging, tests and release docs
```

## 常见问题

### 上传 100 个文件失败

GitHub 网页单次最多上传 100 个文件。  
如果一次拖入超过 100 个，请拆成两批。

### 文件夹拖不进去

浏览器不支持拖文件夹时：

1. 先新建目录；
2. 进入该目录再点 Upload files；
3. 或者使用 GitHub Desktop。

### 隐藏文件

`.gitignore`、`.github` 属于隐藏文件。  
如果 Windows 资源管理器看不到：

```text
查看 → 显示 → 隐藏的项目
```

---

# 四、方式 B：GitHub Desktop（推荐新手）

1. 安装 GitHub Desktop；
2. 登录 GitHub 账号；
3. 菜单：

```text
File → Add local repository
```

4. 选择：

```text
C:\Local Repositories\ALT-VoiceType-github\ALT-VoiceType_Ahee52
```

5. 如果提示不是 Git 仓库，选择：

```text
create a repository
```

6. 左下角填写提交信息：

```text
Initial ALT-VoiceType source
```

7. 点击：

```text
Commit to main
```

8. 点击：

```text
Publish repository
```

9. 确认仓库名：

```text
ALT-VoiceType_Ahee52
```

10. 不要把以下目录勾选上去：

```text
dist
models
.pylibs
build
```

GitHub Desktop 会自动忽略 `.gitignore` 中列出的内容。

---

# 五、上传 Release 安装包

## 1. 打开 Release 页面

仓库页面右侧：

```text
Releases → Create a new release
```

## 2. 填写

```text
Tag: v0.1.0
Target: main
Release title: ALT-VoiceType_Ahee52 0.1.0
```

## 3. 上传附件

来源目录：

```text
C:\Local Repositories\ALT-VoiceType\dist\installer
```

上传：

```text
ALT-VoiceType-Setup-0.1.0.exe
ALT-VoiceType-Setup-0.1.0-1.bin
ALT-VoiceType-Setup-0.1.0-2.bin
ALT-VoiceType-Setup-0.1.0-3.bin
SHA256SUMS.txt
README-GitHub.txt
```

## 4. Release 描述

直接粘贴：

```text
C:\Local Repositories\ALT-VoiceType\dist\installer\README-GitHub.txt
```

或写：

```text
ALT-VoiceType 0.1.0
CPU + Torch 版本，内置三个模型。
下载 exe 和全部 3 个 bin 到同一文件夹后运行 exe。
详见 README。
```

## 5. 发布

点击：

```text
Publish release
```

---

# 六、上传文件大小

当前实际测试：

```text
安装包分卷合计：约 3.93 GB
安装后：约 5.4 GB
安装峰值：约 10 GB
```

单个 `.bin` 约 1.77 GB，低于 GitHub Release 单文件 2GB 限制。

---

# 七、上传前检查

## 仓库

```text
README.md 存在（英文，默认显示）
README.zh.md 存在（中文）
altvoice/ 存在
packaging/ 存在
tests/ 存在
docs/UPLOAD-MANUAL.md 存在
```

## 不应出现

```text
*.gguf
*.safetensors
*.bin
dist/
models/
.pylibs/
```

在仓库搜索栏搜索：

```text
gguf
```

结果应为空。

## Release

确认有 6 个附件：

```text
1 个 exe
3 个 bin
SHA256SUMS.txt
README-GitHub.txt
```

---

# 八、发布后验证

1. 打开仓库首页，确认 README 正常渲染；
2. 点击 README 中的英文链接，确认跳转；
3. 打开 Release，确认附件都能下载；
4. 下载 exe 和 3 个 bin 到同一目录；
5. 运行 exe，确认安装；
6. 启动后等待 ASR 预热；
7. 测试 ESC 取消、数字规范化、翻译和窗口缩放。

---

# 九、以后更新版本

每次更新：

```text
修改源码
→ 本地测试
→ 提交并推送源码
→ 重新生成安装包
→ 新建 Release 标签 v0.1.1
→ 上传新的 exe/bin
```

不要把旧版本的 bin 提交进仓库。

---

# 十、备注

- 仓库默认分支使用 `main`；
- Release 标签建议从 `v0.1.0` 开始；
- 安装包未签名时 Windows 会提示“未知发布者”，这是正常的；
- 代码签名需要受信任的代码签名证书，不能用代码“注册”解决。
