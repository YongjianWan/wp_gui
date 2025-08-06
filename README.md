# wp_gui

## Windows：
1. 安装Python依赖：

```bash
pip install pillow pystray
```
3. 保存代码为 'wp_gui.py'
4. 创建启动脚本 'wp_gui.bat'：

```batch
@echo off
cd /d "%~dp0"
start /min pythonw wp_gui.py
exit
```
6. 设置开机自启（可选）：

把 'wp_gui.bat' 放到启动文件夹
按 'Win+R'，输入 'shell:startup'，把快捷方式放进去

## macos

平稳运行并设置 wp\_gui.py 的开机自启**
用 `Automator` 创建一个启动器，然后设置为登录启动项。

打开「终端 Terminal」，输入以下命令安装依赖包：

```bash
pip3 install pillow pystray
```

---

1. 打开VSCode
2. 将你的 Python 脚本保存为 `wp_gui.py`
3. 放在一个固定的位置，比如 `~/Documents/WPGUI/`（我们后面都以这个目录为例）

---

创建一个用于后台运行的 mac 脚本。

### 3.1 打开终端，输入以下命令：

```bash
mkdir -p ~/Documents/WPGUI
cd ~/Documents/WPGUI
touch wp_gui.command
open wp_gui.command
```

终端会自动打开文本编辑器，接下来：

```bash
#!/bin/bash
cd "$(dirname "$0")"
python3 wp_gui.py &
```

然后保存并关闭编辑器。

在终端中输入：

```bash
chmod +x wp_gui.command
```
双击 `wp_gui.command` 文件来启动你的 Python 脚本**了！

创建一个 mac 启动器（用 Automator）

我们要让这个脚本可以随 mac 开机自动运行。

* 用 Spotlight 搜索「Automator」打开

### 4.2 新建一个「应用程序」

* 点击「新建文稿」
* 选择 **应用程序（Application）**

### 4.3 添加一个动作：「运行 Shell 脚本」

* 在左边的搜索栏输入「运行 Shell 脚本」
* 拖动它到右边的空白区域

### 4.4 修改脚本内容：

把默认的内容替换为以下：

```bash
cd ~/Documents/WPGUI
./wp_gui.command
```

### 4.5 保存为 App

* 文件 → 存储
* 命名为：`WPGUI_启动器.app`
* 存到你愿意放的地方（建议：`~/Applications/` 或 `~/Documents/WPGUI/`）

1. 打开「系统设置」→「用户与群组」→「登录项」
2. 找到“在登录时打开的项目”
3. 点击 `+` 按钮
4. 添加刚刚保存的 `WPGUI_启动器.app`
你可以重启电脑或者注销一次，然后观察：
* 系统顶部菜单栏是否出现你的图标（取决于 `pystray` 设置）
* 后台是否正常运行了你的 `wp_gui.py`

* `pystray` 的实现方式为 macOS 适配（建议用 `PIL.Image.open()` 而非 Windows 系统路径方法）

