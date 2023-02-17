<div align="center">
  <a href="https://v2.nonebot.dev/store"><img src="https://raw.githubusercontent.com/tkgs0/nbpt/resources/nbp_logo.png" width="180" height="180" alt="NoneBotPluginLogo"></a>
  <br>
  <p><img src="https://raw.githubusercontent.com/tkgs0/nbpt/resources/NoneBotPlugin.svg" width="240" alt="NoneBotPluginText"></p>
</div>

<div align="center">

# nonebot-plugin-dicky-pk

_✨ NoneBot Dicky-PK ✨_


<a href="./LICENSE">
    <img src="https://img.shields.io/github/license/tkgs0/nonebot-plugin-dicky-pk.svg" alt="license">
</a>
<a href="https://pypi.python.org/pypi/nonebot-plugin-dicky-pk">
    <img src="https://img.shields.io/pypi/v/nonebot-plugin-dicky-pk.svg" alt="pypi">
</a>
<a href="https://www.python.org">
    <img src="https://img.shields.io/badge/python-3.8+-blue.svg" alt="python">
</a>

</div>

## 📖 介绍

移植自 OPQBot 的群聊小游戏 [CHINCHIN-PK](https://github.com/opq-osc/chinchin-pk)

<p>
<img src="https://raw.githubusercontent.com/tkgs0/nonebot-plugin-dicky-pk/resources/dicky_pk.gif" width="150" alt="你不许参加牛子PK">
</p>

## 💿 安装

**nb-cli安装, 包管理器安装  二选一**

<details>
<summary>使用 nb-cli 安装</summary>

在 nonebot2 项目的根目录下打开命令行, 输入以下指令即可安装

    nb plugin install nonebot-plugin-dicky-pk

</details>

<details>
<summary>使用包管理器安装</summary>

在 nonebot2 项目的插件目录下, 打开命令行,

**根据你使用的包管理器, 输入相应的安装命令**

<details>
<summary>pip</summary>

    pip install nonebot-plugin-dicky-pk

</details>
<details>
<summary>pdm</summary>

    pdm add nonebot-plugin-dicky-pk

</details>
<details>
<summary>poetry</summary>

    poetry add nonebot-plugin-dicky-pk

</details>
<details>
<summary>conda</summary>

    conda install nonebot-plugin-dicky-pk

</details>

打开 bot项目下的 `pyproject.toml` 文件,

在其 `plugins` 里加入 `nonebot_plugin_dicky_pk`

    plugins = ["nonebot_plugin_dicky_pk"]

</details>
</details>

## ⚙️ 配置

首次运行该插件会生成 `Dicky_PK.json` 到Bot项目的 `configs` 文件夹里,

可根据 `Dicky_PK.json` 内的注释进行配置.

## 🎉 使用

### 指令表

**注意:**

以下命令不可省略前缀 `/`

如果bot项目的 `.env` 里只设置了前缀 `/`, 那么你发送以下命令时前缀应该是 `//`

```
/开启(关闭)牛子秘境         # 插件总开关
/牛子帮助                   # 查看帮助
/启用(禁用)牛子pk           # 插件在群聊的开关
/牛子                       # 查看自己的牛子信息
/pk @用户                   # 对at的用户进行牛子PK, 一次只能PK一个用户
/🔒(/suo/嗦/锁)我           # 嗦自己的牛子
/🔒(/suo/嗦/锁) @用户       # 嗦at用户的牛子
/打胶                       # 安抚自己的牛子
/看他牛子(/看看牛子) @用户  # 查看at用户的牛子
/注册牛子                   # 注册属于你的牛子
/牛子排名(/牛子排行)        # 查看牛子排行榜
/牛子转生
/牛子成就
/牛子仙境
/牛子修炼(/牛子练功/牛子修仙)
```

**注:**

**插件服务默认关闭, 首次运行时需向Bot发送 `/开启牛子秘境`**

群聊发送 `/开启牛子秘境` 同时会在当前群聊启用 `牛子PK`,

`/关闭牛子秘境` 同时会清除所有群聊的开关状态, 但不会删除用户的牛子信息.

