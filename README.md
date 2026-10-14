# 共读 EPUB 阅读器

## 日常生成

首次安装依赖：

```powershell
python -m pip install -r requirements.txt
```

将 EPUB 放在 resource 顶层，用“正整数编号_书名.epub”命名：

```text
resource/
  001_罗马研读（富）.epub
  002_加拉太研读 （富）V2.epub
  003_下一本研读.epub
```

运行：

```powershell
python main.py
```

自动扫描并按数字大小合并到 output，共用分组目录、连续翻页和阅读日程。新增书籍不用改代码或维护配置。允许编号空缺；重复编号、0、空书名、未编号 EPUB 会报错，1 与 001 视为重复。

首次生成询问开始日期，后续从 output/books-manifest.json 自动复用，不再询问。本项目已沿用历史发布日期 2026-03-07；首次回车跳过日期可生成普通阅读器。非交互初次构建使用：

```powershell
python main.py --auto-start-date 2026-03-07
```

每日阅读只识别目录标题中的“第几天”，同日多章节合为一天，按原日号整理阅读顺序，再统一连续编号和排日期，不保留原编号缺口。封面、说明、使用生命读经的方法、前言和目录均不占天数。物理页号不改，只调整研读翻页顺序和标题。设置开始日期时如无法识别某本书的阅读日，会报错而不是按物理页猜测。

## 追加与兼容

只在末尾追加更大编号，不更改已有编号、替换旧 EPUB 或在中间插书。原页号、日期和续读记录保持；开始日期及文件指纹保存于 books-manifest.json。发现已有书籍或日期变化时拒绝覆盖旧输出；确需调整请使用新的 --output 目录并自行决定进度迁移。

输入或资源错误在临时目录处理，不覆盖正式产物。不要手工修改 assets/books 内由生成器管理的资源，重新生成会重建这些目录，保留其他文件和图标。

资源按书隔离；跨书采用整页切换加载独立样式，书内保持平滑翻页。缺失或不可解码的源字体声明会过滤并回退到阅读器字体，不修改 EPUB 原内容。

## 其他命令

```powershell
python main.py "resource/001_罗马研读（富）.epub" -o output-single
python main.py --separate
python -m unittest discover -s tests -p test_merge.py -v
python -m http.server 8765 --directory output --bind 127.0.0.1
```

显式单本路径无需编号。--separate 保留原独立批量方式，默认按书名建子目录；多本独立转换不要指定同一个 --output，否则仍会覆盖。

预览：http://127.0.0.1:8765/ 。Service Worker 首次安装缓存全部正文与资源，缓存就绪后可断网阅读。网页与 Android 发布流程安装同一份 requirements.txt，Android webDir 保持 output；APK 构建及远端发布需另行执行现有流程。