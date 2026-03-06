# -*- coding: utf-8 -*-
"""
前端模板常量：CSS / JS / HTML

文件按功能拆分：
  tpl_css.py          – 核心样式 (CORE_CSS_BASE / FULL / LIGHT, THEMES_CSS, FONTS_CSS_TEMPLATE)
  tpl_reader_js.py    – 阅读器核心 JS (READER_JS)
  tpl_app_update_js.py – APK 自更新 JS (APP_UPDATE_JS)
  tpl_tts_js.py       – TTS 双引擎 JS (TTS_JS)
  tpl_sw.py           – Service Worker 注册 / SW 模板 / 离线页 / 图标占位 (SW_REGISTER_JS,
                         SERVICE_WORKER_JS_NEW, OFFLINE_HTML, BASE64_ICON_192, BASE64_ICON_512)
"""

from tpl_css import *            # noqa: F401,F403
from tpl_reader_js import *      # noqa: F401,F403
from tpl_app_update_js import *  # noqa: F401,F403
from tpl_tts_js import *         # noqa: F401,F403
from tpl_sw import *             # noqa: F401,F403
