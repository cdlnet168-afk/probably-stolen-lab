# 深空化学工作台 · Probably Stolen Lab

《深空当铺：可能是偷的》的非官方中文辅助工具。选药品、填光谱仪读数，就能得到本批配料、温度与处理步骤；也能计算去脂、去蛋白、酸碱中和和试剂稀释，并保存自己的实验。

## 普通玩家：点这里下载

**[下载 Windows 免安装版 ZIP](https://github.com/cdlnet168-afk/probably-stolen-lab/releases/latest/download/Probably-Stolen-Lab-v1.0.0-Windows-x64.zip)**

如果上面打不开：[进入下载页面](https://github.com/cdlnet168-afk/probably-stolen-lab/releases/latest)，在 **Assets（资源）** 下选择名称含 **Windows-x64.zip** 的文件。

**不要选 Source code.zip，也不要用绿色 Code 按钮的 Download ZIP：那是给开发者的源码，需要Python。普通玩家下载上面的Windows包，不需要安装Python。**

## 下载后，按这4步打开

1. 找到下载的 `Probably-Stolen-Lab-v1.0.0-Windows-x64.zip`。
2. 鼠标右键 → **全部解压缩**。例如解压到桌面的“深空化学工作台”文件夹；不要直接在压缩包里运行。
3. 进入解压后的文件夹，双击 **`Probably-Stolen-Lab.exe`**。
4. 会出现一个运行窗口，并自动打开浏览器。看到“深空化学工作台 v1.0.0”就可以使用。

运行窗口保持开启；关闭它就停止服务。浏览器未自动打开时，手动访问 [http://127.0.0.1:8873/](http://127.0.0.1:8873/)。这个地址只指向你自己的电脑，不是在线网站，必须先运行程序。

适用：Windows 10/11 x64，带Chrome、Edge等现代浏览器。程序无需登录、无需安装游戏模组，不读取或改写游戏存档；下载完成后核心功能可以离线使用。外部资料链接需要联网。EXE未做数字签名，若系统拦截，请先核对下载来源与本页发布的SHA256；不要直接关闭系统防护。

## 第一次怎么填

**一批制作向导**：先选成品，再输入搅拌/预处理后光谱仪显示的“原料成分mL”，不是整瓶液体体积。试剂浓度填写你手里那瓶的实测百分比。

- “料液中本来已有的目标有效成分”：例如做梦尘时，原料里已经有的梦帽菇萃取液mL；没有就填0。它与菇糊分开，不要重复填写。
- “快捷除杂”：输入要去掉的杂质绝对mL、对应试剂的实测浓度、量具刻度。程序先算有效用量，再给出原液、水和取用工作液的步骤。
- “刻度”填1，表示按整mL量取；填0.1表示能量取到0.1mL。它不是本次加液量。只有显示“均已对齐”的方案才承诺原液、水和取样量都是该刻度的整数倍。
- “成品与纯度”：用处理完成后实测的混合物总体积和有效成分比例检查；理论产量不代替这一步。

常用配方：梦尘、梦魇尘、咖啡因、芬太片、奥克莫吸；山奈德与避孕药仅提供已有成分的重封装。操作步骤可以勾选，刷新后仍保存。开始下一批请点击“清空勾选”。高级工具里保留个人实验记录、实测校准、稀释与混合计算。

## 数据核对到什么程度

**这是社区资料核对版，不是官方配方数据库，也没有逐项游戏实测。**

[完整数据核对报告](docs/DATA-AUDIT.md)逐项列明来源、数值、冲突与程序测试范围。油脂的1:8按“有效脂合剂:油脂”计算，蛋白质约1:1；均用于单目标、无竞争反应的估算。芬太来源有等量简写与净消耗1:0.75的冲突，本工具采用专门配方页的净消耗说明。

先少量处理、等反应稳定后重扫。原料杂质、试剂杂质、温度、游戏补丁和微升取整都会影响结果。普通滤材不能清除所有杂质，本工具不会承诺任意原料都能得到100%纯度。[B站教学核对范围](static/research.html)也随源码提供，并可在程序内打开。

## 数据存在哪里，怎么备份

首次启动会在EXE旁生成 `data/lab.sqlite3`，保存你自己的实验、名称和勾选进度。公开下载包不含作者的数据库或实验记录。

- 方便备份：点击页面右上角 **导出实验备份**，保存JSON文件。
- 换电脑：复制整个工作台文件夹，包含 `data`；或在新程序里导入JSON备份。
- 升级：先导出备份并关闭旧程序，再解压新版到新文件夹，复制旧 `data` 文件夹或导入JSON。不要运行两版服务后混用同一个端口。
- 导入按记录ID合并，不覆盖同ID记录；导入、删除前会在data中生成SQLite备份。

**不要把自己的data文件夹、实验JSON或其他私人记录上传到公开仓库。**

## 打不开时

- 下载的是Source code：回到上面的下载入口，改下Windows-x64.zip。
- 双击后没网页：保留运行窗口，手动打开 http://127.0.0.1:8873/ 。
- 显示端口被占用：关闭旧工作台运行窗口；需要另开端口时用命令 `Probably-Stolen-Lab.exe --port 8874`，再访问8874。
- 无法保存：把解压目录放到自己可写的位置，如桌面；不要放在Program Files或只读目录。首次打开EXE可能需要等待解包。
- 发现配方有误：[提交Issue](https://github.com/cdlnet168-afk/probably-stolen-lab/issues)，说明游戏版本、温度、加入前后绝对mL与试剂浓度；先去掉私人信息。

## 开发者：从源码运行

需要Python 3.10+（当前构建/测试环境为Python 3.14）。运行时只使用标准库，无需pip安装依赖。

```powershell
python server.py
```

或双击 `启动化学工作台.cmd`。测试：

```powershell
python -m unittest discover -v
```

Windows重建免安装EXE：

```powershell
python -m venv .tools/build-venv
.tools/build-venv/Scripts/python.exe -m pip install -r requirements-build.txt
.tools/build-venv/Scripts/python.exe -m PyInstaller --noconfirm --clean --onefile --name Probably-Stolen-Lab --add-data "static;static" server.py
```

构建产物在dist下，发布时另附说明与许可，不要复制自己的data目录。GitHub Actions会运行源码测试；测试证明程序符合所列数学/社区模型，不等于游戏复现实验。

## 许可

代码：[MIT](LICENSE)。配方数据及BWIKI衍生资料：[CC BY-NC-SA 4.0](DATA-LICENSE.md)，感谢深空当铺BWIKI贡献者。未包含游戏贴图、视频或游戏代码；游戏名称和商标属于其权利人。
