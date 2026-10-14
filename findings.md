# 多本 EPUB 合并调研记录

## 实现前基线

- main.py 的 collect_epub_files 对 resource/*.epub 按文件名排序。
- main.py 的 main 对每本 EPUB 单独实例化 EPUBToHTMLConverter；多本时默认输出到书名子目录。
- 显式传入同一个 --output 也仍然是逐本转换，不是合并。
- converter.py 的 convert 每次独立生成正文、目录和 PWA。
- 转换器持有单本书的 opf_dir、spine_items、toc_items 和 _link_map。

## 源码核对结果

- converter.py 的 _generate_content_pages 按 spine 顺序生成 page_NNNN.htm，索引从 0 开始。
- _build_content_page 按 idx-1/idx+1 生成导航，并注入 PAGE_INFO、PAGE_DATE_MAP；合并后的全局索引可复用现有消费方式。
- _parse_toc 在单书解析阶段调用 _adjust_toc_weekday_by_start_date；日期由“第几天”相对该书首个日号计算。直接分别转换会导致两本书日期重置。
- _build_title_date_page_map 从目录标题日期映射到物理页，同日取最早页；合并需要一次建立全局映射。
- _find_spine_index 使用后缀匹配，_build_link_map 还存 basename；不同书籍同名正文会误匹配，需要书籍命名空间。
- _clean_body 把所有 src 引用改到 images/<basename>，_copy_images 也按 basename 复制；合并时会覆盖同名图片。
- _merge_epub_css 将 CSS 合入全局 extra.css，没有书籍作用域。
- 默认书内目录页生成到 index.html 的重定向；若第二本首部包含该页，简单连续加 1 翻页会返回总目录。
- tpl_reader_js.py 的 reader.lastPage.v1 存储 page_NNNN.htm；续读未核对页面是否仍存在，保留罗马页号能降低兼容风险。
- initTodayLinks 优先用 PAGE_DATE_MAP，否则按物理页每天递增；合并模式须避免这个回退消耗非研读页。
- doPageSwap 通过 content.innerHTML 替换正文，只同步 pageIndex 和 PAGE_INFO，未自动换书籍样式或复制任意 data 属性；书籍包装节点应位于正文内部。
- _write_pwa 递归收集输出目录全部文件，排除 sw.js、_headers 和 APK；旧输出目录未清理时历史文件会混入缓存。
- capacitor.config.json 的 webDir 为 output，应将统一阅读器生成到该根目录。

## 实施后确认

- 默认编号扫描与合并已实现，原单本入口和 --separate 保留。
- 两本 EPUB 已添加编号，247+172=419 页，不修改源内容。
- 两个 GitHub Actions 发布流程记录开始日期 2026-03-07；生成已沿用并保存，后续自动复用。
- 罗马 241 个阅读日（431-671），加拉太 168 个阅读日（673-841，缺 693）；罗马原日期和页号经单本基线核对不变。
- 源字体存在缺失或不可解码问题，实际过滤无效声明并回退；其他本地资源引用完整。
- 现有滚动保存/恢复函数为空，本次只保留续读页，不新增滚动恢复。
- 原 SW 仅核心缓存安装，已改为全量缓存；实际验证 421 个页面缓存条目及断网未读末页。

## 初始待核对项（已完成）

- 两本真实 EPUB 的总页数、每日研读日数、NCX/nav 细节和资源内容。
- 罗马当前实际部署路径、生产开始日期及旧滚动位置键兼容行为。
- 源 EPUB 是否包含复杂 CSS、字体重名或无法可靠识别的日程序列。
- 现有测试基础设施与 Android 构建环境。

上述书籍结构、日期和资源已核对；Android 构建环境、原生 TTS 与远端用户 PWA 升级未验证，不由本地结果替代。

## 工作区状态

- git status 确认新增加拉太 EPUB 尚未跟踪，未修改或删除该文件。
- 实施已生成 output 并修改相关代码与 CI 依赖步骤；应用版本未变更，无 Git 提交。

## 用户偏好与约束

- 明确顺序为罗马研读，然后加拉太研读，不能直接依赖文件名字典序。
- 最新要求：以后将编号 EPUB 放入 resource，运行命令后自动按编号合并，无需维护固定书单。
- 规划改为正整数编号_书名.epub、整数排序、默认合并与 --separate；取消原固定配置方案。
- 旧页号兼容限定为末尾追加更大编号，删除、替换、重编号或中间插入不承诺自动迁移。
- 最新请求已授权实现，核心功能与本地验证已完成。