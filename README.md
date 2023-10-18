# Weibo Wordcloud Generator

爬取微博并根据文字内容生成词云

## 安装

将本项目 clone 至本地后使用 pip 安装（推荐配合虚拟环境食用）

```console
$ git clone https://github.com/replica-42/wwg.git
$ cd wwg
$ pip install .
```

或在本项目 release 下载 whl 包后使用 pip 安装

## quickstart

### 获取 uid 与 cookie

访问 [weibo.cn](https://weibo.cn) 并登录。点击用户 id 下方的“微博”

![Snipaste_2023-10-12_14-53-43.png](https://s2.loli.net/2023/10/12/wETJfMchCkqobmY.png)

到达个人主页后此时浏览器地址栏的 URL 形如 `https://weibo.cn/{your_uid}/profile`，路径中 profile 前的数字即为 uid

打开开发者工具（Ctrl+Shift+i），刷新页面，在网络标签栏寻找名称为 profile 的请求，请求标头中 `Cookie` 项对应的值即为 cookie

### 爬取微博并创建词云

在当前目录下创建名为 `config.toml` 的文件，并在其中添加内容

```toml
[crawl]
uid = "xxxx"
cookies = "yyyy"
```

对应的值为上一小节获取的内容，类型为 string

执行

```console
$ wwg crawl --original-only
```

即会自动爬取今年 1 月 1 日 0 时 0 分后发布的原创微博内容

运行结束后当前目录下应当有名为 `weibo.jsonl` 的文件

继续执行

```console
$ wwg generate --font %SystemRoot%\Fonts\simsun.ttc
```

运行结束后当前目录下应当有名为 `weibo.png` 的文件，即为生成的词云

## 配置

本项目配置项的优先级是：命令行参数 > 配置文件 > 默认值

除 `uid` 与 `cookies` 外其余配置项均有默认值，即如果通过命令行参数的方式提供 `uid` 与 `cookies`，不需要配置文件也可运行，但依旧建议将这两项按上文的方式配置于配置文件中

### wwg 命令

运行

```console
$ wwg --help
```

即可查看 `wwg` 命令支持的配置项

`--verbose` 用于开启是否输出调试信息

`--config-file` 用于指示配置文件路径。不提供该项时默认读取工作目录下 `config.toml`，如该文件也不存在则使用默认值

上述两项不存在配置文件中的对应配置项

### wwg crawl 子命令

运行

```console
$ wwg crawl --help
```

即可查看 `wwg crawl` 命令支持的配置项。注意区分命令与子命令的参数位置的不同（e.g. `wwg --verbose crawl --max-page 42`）

以下只提供配置文件中配置项的说明。命令行参数的使用参见 `--help` 的输出。配置项的名称即为 toml 中键的名称，类型为 toml 中的类型。crawl 子命令的配置项均位于表 `crawl` 下

`uid` 类型为字符串，无默认值

`cookies` 类型为字符串，无默认值

`original_only` 类型为布尔，默认为 false。该配置为真时仅保存原创微博

`start_page` 类型为整数，该配置指定爬取的起始页数，该参数必须大于等于 1，默认值为 1

`max_page` 类型为整数，该配置值指定爬取的最大页数。默认值为 -1，即不限制最大页数

`after` 类型为各地日期时刻，默认值为 `yyyy-01-01T00:00:00`，其中 yyyy 为当前的年数。该配置项指定爬取的最早时间。同时指定 `max_page` 与该项时会在第一次到达其中一个限制时停止爬取

`output` 类型为字符串，默认值为 `weibo.jsonl`，结果保存路径

crawl 爬取时在两次请求间会默认睡眠 3-5 秒，防止访问频率过高被 403

### wwg generate 子命令

generate 子命令的配置项均位于表 `generate` 下

`input` 类型为字符串，默认值为配置项 `crawl.output` 的值（取值优先级为：命令行参数 > 配置文件 > 配置文件中表 `crawl` 键 `output` 的值 > `crawl.output` 默认值）

`font` 类型为字符串，指定词云使用的字体，为字体文件的路径。建议手动指定中文字体，避免中文显示错误。默认值为空，即使用默认字体

`mask` 类型为字符串，指定词云使用的 mask 图片的路径。本项目在 mask 目录下提供了一个示例图片，更多细节参见 [wordcloud](https://github.com/amueller/word_cloud) 文档。默认值为空，即不使用 mask

`custom_dict` 类型为字符串，指定 jieba 分词时使用的自定义词典路径。对于一些分词算法未能识别的专用词语（如人名/作品名），可以通过自定义词典指导分词。词典类型为文本文件，格式为一个词语一行。更多细节参见 [jieba](https://github.com/fxsjy/jieba) 文档。默认值为空，即不使用词典

`before` 与 `after` 指定创建词云的微博时间区间，默认 `before` 为当前时间，`after` 为 1970 年 1 月 1 日，即不做限制，使用 `input` 的所有内容

`max_word` 类型为整数，指定词云中词语的个数。默认值为 400

`output` 类型为字符串，指定词云图片的保存路径。默认值为 `weibo.png`

### 配置文件示例

```toml
[crawl]
uid = ""
cookies = ""
original_only = true
start_page = 5
max_page = 20
after = 2023-10-01T00:00:00
output = "my_weibo.jsonl"

[generate]
# use crawl.output as input
font = "C:\\Windows\\Fonts\\simsun.ttc"
mask = "mask/2023.png"
custom_dict = "dict.txt"
before = 2022-01-01T00:00:00
after = 2021-01-01T00:00:00
max_word = 300
output = "my_weibo.png"
```
