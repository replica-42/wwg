# Weibo Wordcloud Generator

爬取微博并根据文字内容生成词云

## 安装

需要 Python 3.14 及以上版本，仓库默认使用 Python 3.14。推荐使用 uv 创建虚拟环境并安装依赖：

```console
$ git clone https://github.com/replica-42/wwg.git
$ cd wwg
$ uv sync
$ uv run wwg --help
```

开发环境使用 `uv sync --extra dev`。下文的 `wwg` 命令可通过 `uv run wwg` 执行，或先激活 `.venv` 后执行。

回归测试使用 `uv run --locked --extra dev pytest`。按照 [pytest 对 src 布局的建议](https://docs.pytest.org/en/stable/explanation/goodpractices.html#tests-outside-application-code)，使用 `importlib` 导入模式，不手动向 `sys.path` 或 `PYTHONPATH` 添加仓库或 `src` 路径；应用通过 `.venv` 中的 editable 安装导入。

过滤回归测试以 HanLP 为基准。设置 `WWG_TEST_HANLP_MODEL` 为已下载的 `COARSE_ELECTRA_SMALL_ZH` 模型目录，可在同一 pytest 命令中运行真实模型推理用例；未设置时跳过该用例，其余过滤测试使用固定候选词，不需要下载模型。

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

如果输出文件已存在，爬取和生成命令都会提示是否覆盖，默认选择 N。网络请求会在连接或读取超时、请求失败时进行有限重试，仍失败则报错退出。

继续执行

```console
$ wwg generate --font %SystemRoot%\Fonts\simsun.ttc
```

运行结束后当前目录下应当有名为 `weibo.png` 的文件，即为生成的词云

输入文件使用 JSONL 格式，每行必须是包含字符串字段 `content` 和 `create_at` 的 JSON 对象，时间格式为 `YYYY-MM-DDTHH:MM:SS`。读取时逐行校验，遇到无效记录会报告文件路径、行号和原因，并中断生成。

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

`custom_dict` 类型为字符串，指定分词时使用的自定义词典路径，供所有分词后端使用。对于一些分词算法未能识别的专用词语（如人名/作品名），可以通过自定义词典指导分词。词典类型为文本文件，格式为一个词语一行。HanLP 使用 `COARSE_ELECTRA_SMALL_ZH` 模型，将词典传入 `dict_force`，不启用 `dict_combine`。默认值为空，即不使用词典。

自定义词典也用于保护过滤阶段的候选词：清理外围空白、句读标点和括号后，命中词典的词不受停用词、单字和最低出现次数限制。普通词仍须至少出现两次。长词的出现不会导致短词被整体删除。

当前过滤流程如下：

1. 在 `after` 至 `before` 的闭区间内选取微博，使用所选后端分词。
2. 清理候选词外围空白、句读标点和括号，保留内部字符；清理后为空的候选直接丢弃。
3. 自定义词优先保留。其他候选必须超过一个字符、至少包含一个字母或数字，且不在完整词停用表或固定排除项（`网页链接`、`网页`、`链接`、`jpg`、`.jpg`）中。
4. 按清理后的词统计所选时间区间内的出现次数；普通词至少出现两次，自定义词允许一次。
5. 将最终词频直接传入词云生成器，由 `max_word` 限制最多展示词数。

停用词表已增补低信息表达：只能、都是、一点、一遍、有种、有没有、能不能、那种、又是、尤其是、没什么、是因为。停用判断只匹配完整词，不按组成字符或子串删除词。当前不使用词性过滤，不自动合并别名、大小写或简繁体，也不对数字词整体排除。自定义词保护只作用于后端实际输出的候选，不保证词典中的所有词都会被分出或显示在词云中。

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
