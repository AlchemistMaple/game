# game
# GRAVITAS MECHANICA (重力沉压俄罗斯方块)

一个结合了古典素描画风与离散材料物理引擎的俄罗斯方块变种。

与传统俄罗斯方块不同，本作引入了 **重力 (Gravity)**、**材料硬度 (Material)** 和 **历史行链接强度 (Link)** 三个物理变量。当已消除的“历史行”承受的顶部压力超过其链接阈值时，它会瓦解、沉降，并再次填补底部的空白。

## 📸 游戏截图
<img width="1076" height="892" alt="ing" src="https://github.com/user-attachments/assets/7382d6a0-7dfa-4d56-baf3-cba23600d280" />


## 🚀 如何游玩 (源码运行)

1. 确保你安装了 Python (推荐 3.10 或以上版本)。
2. 克隆本仓库：
   ```bash
   git clone https://github.com/AlchemistMaple/game.git

pip install -r requirements.txt

python main.py


由于 Github 仓库对单文件体积的限制（<25MB），本仓库未包含背景音乐文件 bgm.mp3。

游戏在无背景音乐下可以完美正常运行。

如果你想获得完整体验，请自行准备一个你喜欢的 .mp3 格式音频文件，将其重命名为 bgm.mp3 并放在与 main.py 同级的根目录下，游戏启动时会自动循环播放。
   
如果你不想配置 Python 环境，请前往本仓库的 Releases 页面，下载最新的 .zip 压缩包，解压后双击 .exe 即可开始游戏。
