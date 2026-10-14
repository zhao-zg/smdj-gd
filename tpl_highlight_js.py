# -*- coding: utf-8 -*-
"""
阅读器划线/标记/批注 JS（对齐 books 项目移植，适配 smdj-gd 轻量 PWA）

数据模型：{id, start, end, text, prefix, suffix, color, underline, note, timestamp}
  color:   'yellow'|'green'|'blue'|'pink' | null（无底色）
  underline: 布尔（下划线）
  note:      字符串批注
  color/underline/note 三者正交；全部为空时自动删除该记录。

存储：localStorage 单 key 'reader_highlights'，值 { [pagePath]: [highlight, ...] }
  pagePath 用 location.pathname（每个 page_XXXX.htm 独立一个标注数组）。
  不引入任何 vendor 库（对齐 books 的 localStorage 降级写法）。

容器：#reader-content（smdj-gd 正文容器）
换页：reader.js 的 afterSwap() 会调用 window.SMHighlights.refresh() 重应用标注。
"""

HIGHLIGHT_JS = r"""
(function () {
  'use strict';
  if (window.SMHighlights) return;

  var CONFIG = {
    storageKey: 'reader_highlights',
    colors: {
      yellow: '#E8D18C',
      green:  '#A8D4B0',
      blue:   '#9DC0D4',
      pink:   '#D9A5A6'
    },
    dotColors: {
      yellow: '#D4A843',
      green:  '#6DA880',
      blue:   '#6A9DB5',
      pink:   '#C4787A'
    },
    defaultColor: 'yellow'
  };

  var SMHighlights = {
    config: CONFIG,
    highlights: [],
    _pendingRange: null,
    _pendingHighlightId: null,
    _selectedColor: 'yellow',
    _selectedUnderline: false,
    _pointerDown: false,
    _restoreGen: 0,
    _listenersSetup: false
  };

  /* ─── 存储适配层（纯 localStorage 单 key，{pagePath: [records]}）────────── */
  function loadAll() {
    try { return JSON.parse(localStorage.getItem(CONFIG.storageKey) || '{}'); }
    catch (e) { return {}; }
  }
  function saveAll(all) {
    try { localStorage.setItem(CONFIG.storageKey, JSON.stringify(all)); }
    catch (e) { console.warn('[划线] 保存失败:', e); }
  }
  function getPageKey() {
    // Android Capacitor 环境可能带 /android_asset/public 前缀，归一化
    var p = location.pathname;
    p = p.replace(/^\/android_asset\/public/, '')
         .replace(/^\/public(?=\/)/, '')
         .replace(/^\/index\.html$/, '/');
    return p || '/';
  }

  /* ─── 数据读写当前页 ───────────────────────────────────────── */
  function loadHighlights() {
    var all = loadAll();
    var arr = (all[getPageKey()] || []).map(function (h) {
      if (h.underline === undefined) h.underline = false;
      if (h.note === undefined)      h.note      = '';
      return h;
    });
    SMHighlights.highlights = arr;
    return arr;
  }
  function saveHighlights() {
    var all = loadAll();
    all[getPageKey()] = SMHighlights.highlights;
    saveAll(all);
  }
  function clearAllHighlightsForce() {
    SMHighlights.highlights = [];
    clearAllMarks();
    var all = loadAll();
    delete all[getPageKey()];
    saveAll(all);
  }

  /* ─── 容器定位（适配 smdj-gd：<main id="reader-content">） ─────── */
  function getContainer() {
    return document.getElementById('reader-content')
        || document.getElementById('reader-app')
        || document.querySelector('.page-view');
  }

  /* ─── 文本节点遍历 ──────────────────────────────────────────── */
  function getTextNodes(element) {
    var textNodes = [];
    var walker = document.createTreeWalker(element, NodeFilter.SHOW_TEXT, null);
    var node;
    while ((node = walker.nextNode())) textNodes.push(node);
    return textNodes;
  }

  /* ─── 选区 → 绝对字符偏移 ───────────────────────────────────── */
  function getSelectionPosition(container, range) {
    var textNodes = getTextNodes(container);
    var charCount = 0, start = -1, end = -1;
    for (var i = 0; i < textNodes.length; i++) {
      var node = textNodes[i];
      var nodeLength = node.textContent.length;
      if (node === range.startContainer) start = charCount + range.startOffset;
      if (node === range.endContainer)   { end = charCount + range.endOffset; break; }
      charCount += nodeLength;
    }
    return (start >= 0 && end >= 0 && end > start) ? { start: start, end: end } : null;
  }

  /* ─── TextQuoteSelector 辅助 ────────────────────────────────── */
  function extractContext(pageText, start, end, win) {
    win = win || 25;
    return {
      prefix: pageText.substring(Math.max(0, start - win), start),
      suffix: pageText.substring(end, Math.min(pageText.length, end + win))
    };
  }
  function overlapRight(saved, actual) {
    var i = saved.length - 1, j = actual.length - 1, count = 0;
    while (i >= 0 && j >= 0 && saved[i] === actual[j]) { i--; j--; count++; }
    return count;
  }
  function overlapLeft(saved, actual) {
    var i = 0, count = 0;
    while (i < saved.length && i < actual.length && saved[i] === actual[i]) { i++; count++; }
    return count;
  }

  /* ─── 插入笔记图标 ─────────────────────────────────────────── */
  function insertNoteIcon(markEl, highlightId) {
    if (document.querySelector('.bk-hl-note-icon[data-highlight-id="' + highlightId + '"]')) return;
    var next = markEl.nextSibling;
    if (next && next.classList && next.classList.contains('bk-hl-note-icon')) return;
    var icon = document.createElement('span');
    icon.className = 'bk-hl-note-icon';
    icon.textContent = '📝';
    icon.dataset.highlightId = highlightId;
    markEl.parentNode.insertBefore(icon, markEl.nextSibling);
  }

  /* ─── 应用单个划线到 DOM ───────────────────────────────────── */
  function applyHighlight(highlight) {
    var container = getContainer();
    if (!container) return;
    if (document.querySelector('.bk-highlight[data-highlight-id="' + highlight.id + '"]')) return;
    var textNodes = getTextNodes(container);
    var charCount = 0;

    if (highlight.text) {
      var fullText = '';
      for (var j = 0; j < textNodes.length; j++) {
        var tn = textNodes[j];
        var tnStart = charCount;
        var tnEnd   = tnStart + tn.textContent.length;
        if (tnEnd > highlight.start && tnStart < highlight.end) {
          var s = Math.max(0, highlight.start - tnStart);
          var e = Math.min(tn.textContent.length, highlight.end - tnStart);
          fullText += tn.textContent.substring(s, e);
        }
        charCount += tn.textContent.length;
        if (tnStart >= highlight.end) break;
      }
      charCount = 0;
      if (fullText !== highlight.text) {
        var pageText = '';
        for (var k = 0; k < textNodes.length; k++) pageText += textNodes[k].textContent;
        var candidates = [];
        var searchFrom = 0;
        while (true) {
          var pos = pageText.indexOf(highlight.text, searchFrom);
          if (pos < 0) break;
          candidates.push(pos);
          searchFrom = pos + 1;
        }
        if (!candidates.length) {
          console.warn('[划线] 文本已不存在，跳过恢复:', highlight.text.substring(0, 20));
          return;
        }
        var bestPos = -1;
        if (highlight.prefix !== undefined && highlight.suffix !== undefined) {
          var bestScore = -1;
          for (var ci = 0; ci < candidates.length; ci++) {
            var cp = candidates[ci];
            var ce = cp + highlight.text.length;
            var actualPrefix = pageText.substring(Math.max(0, cp - 25), cp);
            var actualSuffix = pageText.substring(ce, Math.min(pageText.length, ce + 25));
            var score = overlapRight(highlight.prefix, actualPrefix) +
                        overlapLeft(highlight.suffix, actualSuffix);
            if (score > bestScore ||
                (score === bestScore && Math.abs(cp - highlight.start) < Math.abs(bestPos - highlight.start))) {
              bestScore = score; bestPos = cp;
            }
          }
        } else {
          var bestDist = Infinity;
          for (var di = 0; di < candidates.length; di++) {
            var dist = Math.abs(candidates[di] - highlight.start);
            if (dist < bestDist) { bestDist = dist; bestPos = candidates[di]; }
          }
        }
        highlight.start = bestPos;
        highlight.end   = bestPos + highlight.text.length;
        var newCtx = extractContext(pageText, highlight.start, highlight.end);
        highlight.prefix = newCtx.prefix;
        highlight.suffix = newCtx.suffix;
        setTimeout(function () { saveHighlights(); }, 0);
        charCount = 0;
      }
    }

    for (var i = 0; i < textNodes.length; i++) {
      var node       = textNodes[i];
      var nodeLength = node.textContent.length;
      var nodeStart  = charCount;
      var nodeEnd    = charCount + nodeLength;

      if (nodeEnd > highlight.start && nodeStart < highlight.end) {
        var startOffset = Math.max(0, highlight.start - nodeStart);
        var endOffset   = Math.min(nodeLength, highlight.end - nodeStart);

        var range = document.createRange();
        range.setStart(node, startOffset);
        range.setEnd(node, endOffset);

        var mark = document.createElement('mark');
        mark.className = 'bk-highlight';

        if (highlight.color && highlight.color !== 'note' && CONFIG.colors[highlight.color]) {
          mark.style.backgroundColor = CONFIG.colors[highlight.color];
          mark.dataset.color = highlight.color;
        } else {
          mark.style.backgroundColor = 'transparent';
        }
        if (highlight.underline) mark.dataset.underline = 'true';
        if (highlight.note)      mark.dataset.note      = 'true';
        mark.dataset.highlightId = highlight.id;

        try {
          range.surroundContents(mark);
          if (highlight.note && (nodeStart + endOffset >= highlight.end)) {
            insertNoteIcon(mark, highlight.id);
          }
        } catch (e) {
          console.warn('[划线] 无法应用划线:', e);
        }
      }
      charCount += nodeLength;
    }
  }

  /* ─── 恢复全部划线 ─────────────────────────────────────────── */
  function restoreHighlights() {
    var gen = ++SMHighlights._restoreGen;
    loadHighlights();
    setTimeout(function () {
      if (SMHighlights._restoreGen !== gen) return;
      var seen = {};
      SMHighlights.highlights = SMHighlights.highlights.filter(function (h) {
        if (seen[h.id]) return false;
        seen[h.id] = true;
        return true;
      });
      SMHighlights.highlights.forEach(function (h) { applyHighlight(h); });
    }, 0);
  }

  /* ─── 清除所有 DOM 标记 ────────────────────────────────────── */
  function clearAllMarks() {
    document.querySelectorAll('.bk-hl-note-icon').forEach(function (el) { el.remove(); });
    document.querySelectorAll('.bk-highlight').forEach(function (mark) {
      var parent = mark.parentNode;
      while (mark.firstChild) parent.insertBefore(mark.firstChild, mark);
      parent.removeChild(mark);
    });
    var c = getContainer();
    if (c && c.normalize) c.normalize();
  }

  /* ═══════════════════════════ CRUD ═══════════════════════════ */
  function addHighlight(color, underline) {
    var range = SMHighlights._pendingRange;
    if (!range) return null;
    var rangeNode = range.commonAncestorContainer;
    var container = (rangeNode.nodeType === 3 ? rangeNode.parentElement : rangeNode)
                    .closest('#reader-content, .page-view');
    if (!container) return null;
    var position = getSelectionPosition(container, range);
    if (!position) return null;

    var textNodes = getTextNodes(container);
    var pageText = '';
    for (var ti = 0; ti < textNodes.length; ti++) pageText += textNodes[ti].textContent;
    var ctx = extractContext(pageText, position.start, position.end);

    var highlight = {
      id:        Date.now().toString(),
      start:     position.start,
      end:       position.end,
      text:      range.toString(),
      prefix:    ctx.prefix,
      suffix:    ctx.suffix,
      color:     (color === null || color === 'note' || color === undefined) ? null : (color || CONFIG.defaultColor),
      underline: !!underline,
      note:      '',
      timestamp: Date.now()
    };

    SMHighlights.highlights.push(highlight);
    SMHighlights._pendingRange = null;
    SMHighlights._suppressSelMenuUntil = Date.now() + 800;
    saveHighlights();
    clearAllMarks();
    restoreHighlights();
    SMHighlights._suppressSelMenuUntil = 0;
    try { document.dispatchEvent(new CustomEvent('marks-changed')); } catch (e) {}
    return highlight.id;
  }

  function updateHighlight(id, changes) {
    var h = SMHighlights.highlights.find(function (x) { return x.id === id; });
    if (!h) return;
    if (changes.color     !== undefined) h.color     = changes.color;
    if (changes.underline !== undefined) h.underline = changes.underline;
    saveHighlights(); clearAllMarks(); restoreHighlights();
    try { document.dispatchEvent(new CustomEvent('marks-changed')); } catch (e) {}
  }

  function removeHighlight(id) {
    SMHighlights.highlights = SMHighlights.highlights.filter(function (h) { return h.id !== id; });
    saveHighlights(); clearAllMarks(); restoreHighlights();
    try { document.dispatchEvent(new CustomEvent('marks-changed')); } catch (e) {}
  }

  function removeMark(id) {
    var h = SMHighlights.highlights.find(function (x) { return x.id === id; });
    if (!h) return;
    h.color = null; h.underline = false;
    if (!h.note) { removeHighlight(id); return; }
    saveHighlights(); clearAllMarks(); restoreHighlights();
    try { document.dispatchEvent(new CustomEvent('marks-changed')); } catch (e) {}
  }

  function saveNote(id, text) {
    var h = SMHighlights.highlights.find(function (x) { return x.id === id; });
    if (!h) return;
    h.note = text || '';
    if (!h.note && !h.color && !h.underline) { removeHighlight(id); return; }
    saveHighlights(); clearAllMarks(); restoreHighlights();
    try { document.dispatchEvent(new CustomEvent('marks-changed')); } catch (e) {}
  }

  function removeNote(id) { saveNote(id, ''); }

  /* ═══════════════════════════ UI ═══════════════════════════ */
  function colorPanelHTML(prefix) {
    return Object.keys(CONFIG.colors).map(function (name) {
      return '<button class="hl-color-dot ' + prefix + '" data-color="' + name +
             '" style="background:' + CONFIG.dotColors[name] + '" title="' + name + '"></button>';
    }).join('');
  }

  function stopPropagation(menu) {
    ['touchstart', 'touchend', 'mousedown'].forEach(function (evt) {
      menu.addEventListener(evt, function (e) { e.stopPropagation(); });
    });
  }

  function createSelectionMenu() {
    if (document.getElementById('hl-selection-menu')) return;
    var menu = document.createElement('div');
    menu.id = 'hl-selection-menu';
    menu.className = 'hl-menu';
    menu.innerHTML =
      '<div class="hl-menu-row hl-sel-row">' +
        colorPanelHTML('hl-sel-dot') +
        '<button class="hl-underline-btn" id="hl-sel-ul" title="下划线">U</button>' +
        '<span class="hl-sel-sep"></span>' +
        '<button class="hl-menu-btn hl-sel-note-btn" id="hl-sel-note">添加批注</button>' +
      '</div>';
    stopPropagation(menu);
    document.body.appendChild(menu);

    menu.querySelectorAll('.hl-sel-dot').forEach(function (dot) {
      dot.addEventListener('click', function (e) {
        e.stopPropagation();
        addHighlight(dot.dataset.color, false);
        hideAllMenus();
      });
    });
    document.getElementById('hl-sel-ul').addEventListener('click', function (e) {
      e.stopPropagation();
      addHighlight(null, true);
      hideAllMenus();
    });
    document.getElementById('hl-sel-note').addEventListener('click', function (e) {
      e.stopPropagation();
      var newId = addHighlight('note', false);
      hideAllMenus();
      if (newId) showNoteEditor(newId);
    });
  }

  function createAnnotationMenu() {
    if (document.getElementById('hl-annotation-menu')) return;
    var menu = document.createElement('div');
    menu.id = 'hl-annotation-menu';
    menu.className = 'hl-menu hl-ann-menu';
    menu.innerHTML =
      '<div class="hl-ann-note-bubble" id="hl-ann-note-preview">' +
        '<div class="hl-ann-note-body" id="hl-ann-note-text"></div>' +
        '<button class="hl-ann-note-expand" id="hl-ann-expand">展开 ▾</button>' +
      '</div>' +
      '<div class="hl-ann-toolbar" id="hl-ann-toolbar">' +
        '<button class="hl-ann-tool" id="hl-ann-edit-note">' +
          '<span class="hl-ann-tool-icon">✏️</span><span class="hl-ann-tool-label" id="hl-ann-edit-note-label">批注</span>' +
        '</button>' +
        '<button class="hl-ann-tool hl-ann-tool-danger" id="hl-ann-del-note">' +
          '<span class="hl-ann-tool-icon">🗑</span><span class="hl-ann-tool-label">删除</span>' +
        '</button>' +
        '<span class="hl-ann-tool-sep"></span>' +
        '<button class="hl-ann-tool" id="hl-ann-modify-mark">' +
          '<span class="hl-ann-tool-icon">🎨</span><span class="hl-ann-tool-label" id="hl-ann-mark-label">标记</span>' +
        '</button>' +
        '<button class="hl-ann-tool hl-ann-tool-danger" id="hl-ann-del-mark">' +
          '<span class="hl-ann-tool-icon">✕</span><span class="hl-ann-tool-label">删除</span>' +
        '</button>' +
      '</div>' +
      '<div class="hl-color-panel">' + colorPanelHTML('') + '<button class="hl-underline-btn hl-ann-ul" title="下划线">U</button></div>';
    stopPropagation(menu);
    document.body.appendChild(menu);

    document.getElementById('hl-ann-modify-mark').addEventListener('click', function (e) {
      e.stopPropagation();
      var panel = menu.querySelector('.hl-color-panel');
      var isOpen = panel.classList.contains('open');
      panel.classList.toggle('open', !isOpen);
      if (!isOpen) {
        var h = SMHighlights.highlights.find(function (x) { return x.id === SMHighlights._pendingHighlightId; });
        if (h) syncColorPanel(panel, h.color, h.underline);
      }
    });
    document.getElementById('hl-ann-del-mark').addEventListener('click', function (e) {
      e.stopPropagation();
      var id = SMHighlights._pendingHighlightId;
      hideAllMenus();
      if (id) {
        var h = SMHighlights.highlights.find(function (x) { return x.id === id; });
        var hasNote = h && h.note;
        var msg = hasNote ? '确定删除此划线？含批注将一并删除' : '确定删除此划线？';
        if (confirm(msg)) removeMark(id);
      }
    });
    document.getElementById('hl-ann-edit-note').addEventListener('click', function (e) {
      e.stopPropagation();
      var id = SMHighlights._pendingHighlightId;
      hideAllMenus();
      if (id) showNoteEditor(id);
    });
    document.getElementById('hl-ann-del-note').addEventListener('click', function (e) {
      e.stopPropagation();
      var id = SMHighlights._pendingHighlightId;
      hideAllMenus();
      if (id && confirm('确定删除此批注？')) removeNote(id);
    });
    // 展开按钮（批注长文时展开为全屏查看，smdj-gd 无 BK.openDialog，用模态框展示）
    document.getElementById('hl-ann-expand').addEventListener('click', function (e) {
      e.stopPropagation();
      var id = SMHighlights._pendingHighlightId;
      var h  = SMHighlights.highlights.find(function (x) { return x.id === id; });
      if (!h || !h.note) return;
      hideAllMenus();
      var modal = document.getElementById('hl-note-modal');
      modal.dataset.highlightId = id;
      var ta = document.getElementById('hl-note-textarea');
      ta.value = h.note;
      document.getElementById('hl-note-title').textContent = '批注';
      modal.style.display = 'flex';
      document.getElementById('hl-note-save').style.display = 'none';
      document.getElementById('hl-note-cancel').textContent = '关闭';
    });
    bindColorPanel(menu.querySelector('.hl-color-panel'), 'existing');
  }

  function createNoteModal() {
    if (document.getElementById('hl-note-modal')) return;
    var modal = document.createElement('div');
    modal.id = 'hl-note-modal';
    modal.className = 'hl-modal-mask';
    modal.innerHTML =
      '<div class="hl-modal-card">' +
        '<div class="hl-modal-title" id="hl-note-title">批注</div>' +
        '<textarea class="hl-note-textarea" id="hl-note-textarea" placeholder="输入批注内容…" rows="5"></textarea>' +
        '<div class="hl-modal-actions">' +
          '<button class="hl-modal-btn hl-modal-cancel" id="hl-note-cancel">取消</button>' +
          '<button class="hl-modal-btn hl-modal-save" id="hl-note-save">保存</button>' +
        '</div>' +
      '</div>';
    document.body.appendChild(modal);

    function closeModal() {
      var id = modal.dataset.highlightId;
      modal.style.display = 'none';
      document.getElementById('hl-note-save').style.display = '';
      if (id) {
        var h = SMHighlights.highlights.find(function (x) { return x.id === id; });
        if (h && !h.note && !h.color && !h.underline) removeHighlight(id);
      }
    }
    document.getElementById('hl-note-cancel').addEventListener('click', closeModal);
    document.getElementById('hl-note-save').addEventListener('click', function () {
      var id   = modal.dataset.highlightId;
      var text = document.getElementById('hl-note-textarea').value.trim();
      if (id) saveNote(id, text);
      closeModal();
    });
    modal.addEventListener('click', function (e) { if (e.target === modal) closeModal(); });
  }

  function bindColorPanel(panel, target) {
    panel.querySelectorAll('.hl-color-dot').forEach(function (dot) {
      dot.addEventListener('click', function (e) {
        e.stopPropagation();
        var isSame = SMHighlights._selectedColor === dot.dataset.color;
        panel.querySelectorAll('.hl-color-dot').forEach(function (d) { d.classList.remove('selected'); });
        if (isSame) SMHighlights._selectedColor = null;
        else { SMHighlights._selectedColor = dot.dataset.color; dot.classList.add('selected'); }
        if (target === 'existing') {
          var id = SMHighlights._pendingHighlightId;
          if (id) {
            if (!SMHighlights._selectedColor && !SMHighlights._selectedUnderline) removeMark(id);
            else updateHighlight(id, { color: SMHighlights._selectedColor, underline: SMHighlights._selectedUnderline });
          }
          hideAllMenus();
        }
      });
    });
    panel.querySelector('.hl-underline-btn').addEventListener('click', function (e) {
      e.stopPropagation();
      this.classList.toggle('active');
      SMHighlights._selectedUnderline = this.classList.contains('active');
      if (target === 'existing') {
        var id = SMHighlights._pendingHighlightId;
        if (id) {
          if (!SMHighlights._selectedColor && !SMHighlights._selectedUnderline) removeMark(id);
          else updateHighlight(id, { color: SMHighlights._selectedColor, underline: SMHighlights._selectedUnderline });
        }
        hideAllMenus();
      }
    });
  }

  function syncColorPanel(panel, color, underline) {
    panel.querySelectorAll('.hl-color-dot').forEach(function (d) {
      d.classList.toggle('selected', d.dataset.color === color);
    });
    panel.querySelector('.hl-underline-btn').classList.toggle('active', !!underline);
    SMHighlights._selectedColor     = color;
    SMHighlights._selectedUnderline = !!underline;
  }

  function hideAllMenus() {
    ['hl-selection-menu', 'hl-annotation-menu'].forEach(function (id) {
      var el = document.getElementById(id);
      if (!el) return;
      el.style.display = 'none';
      var panel = el.querySelector('.hl-color-panel');
      if (panel) panel.classList.remove('open');
    });
  }

  function showSelectionMenu(range) {
    hideAllMenus();
    SMHighlights._pendingRange      = range;
    SMHighlights._selectedColor     = CONFIG.defaultColor;
    SMHighlights._selectedUnderline = false;
    var menu = document.getElementById('hl-selection-menu');
    positionMenuByRect(menu, range.getBoundingClientRect());
  }

  function showAnnotationMenu(highlightId, targetEl) {
    hideAllMenus();
    SMHighlights._pendingHighlightId = highlightId;
    var h = SMHighlights.highlights.find(function (x) { return x.id === highlightId; });
    if (!h) return;

    var bubble    = document.getElementById('hl-ann-note-preview');
    var noteBody  = document.getElementById('hl-ann-note-text');
    var expandBtn = document.getElementById('hl-ann-expand');
    if (h.note) {
      noteBody.textContent = h.note;
      expandBtn.style.display = 'none';
      bubble.style.display = 'block';
    } else {
      noteBody.textContent = '';
      expandBtn.style.display = 'none';
      bubble.style.display = 'none';
    }
    var noteEditLabel = document.getElementById('hl-ann-edit-note-label');
    if (noteEditLabel) noteEditLabel.textContent = h.note ? '编辑' : '批注';
    document.getElementById('hl-ann-del-note').style.display = h.note ? '' : 'none';

    var hasVisibleMark = !!(h.color || h.underline);
    var markLabel = document.getElementById('hl-ann-mark-label');
    if (markLabel) markLabel.textContent = hasVisibleMark ? '修改' : '标记';
    document.getElementById('hl-ann-del-mark').style.display = hasVisibleMark ? '' : 'none';

    var menu = document.getElementById('hl-annotation-menu');
    positionMenuByRect(menu, targetEl.getBoundingClientRect());
  }

  function showNoteEditor(id) {
    var h     = SMHighlights.highlights.find(function (x) { return x.id === id; });
    var modal = document.getElementById('hl-note-modal');
    modal.dataset.highlightId = id;
    document.getElementById('hl-note-title').textContent = '批注';
    document.getElementById('hl-note-save').style.display = '';
    document.getElementById('hl-note-textarea').value = h ? (h.note || '') : '';
    modal.style.display = 'flex';
    setTimeout(function () { document.getElementById('hl-note-textarea').focus(); }, 100);
  }

  function positionMenuByRect(menu, rect) {
    menu.style.position  = 'fixed';
    menu.style.transform = 'none';
    menu.style.top       = '-9999px';
    menu.style.left      = '-9999px';
    menu.style.display   = 'flex';
    menu.style.opacity   = '0';
    requestAnimationFrame(function () {
      var vvp = window.visualViewport;
      var vpH = vvp ? vvp.height : window.innerHeight;
      var vpW = vvp ? vvp.width  : window.innerWidth;
      var GAP_BELOW = 88;
      var GAP_ABOVE = 78;
      var belowAvail = vpH - rect.bottom - GAP_BELOW;
      var aboveAvail = rect.top - GAP_ABOVE;
      var viewTop;
      if (belowAvail >= menu.offsetHeight || belowAvail >= aboveAvail) viewTop = rect.bottom + GAP_BELOW;
      else viewTop = rect.top - menu.offsetHeight - GAP_ABOVE;
      viewTop = Math.max(GAP_BELOW, Math.min(viewTop, vpH - menu.offsetHeight - 10));
      var left = rect.left + rect.width / 2 - menu.offsetWidth / 2;
      left = Math.max(10, Math.min(left, vpW - menu.offsetWidth - 10));
      menu.style.left = left + 'px';
      menu.style.top  = viewTop + 'px';
      if (menu.id === 'hl-annotation-menu') {
        var nb = document.getElementById('hl-ann-note-text');
        var eb = document.getElementById('hl-ann-expand');
        if (nb && eb && nb.textContent) eb.style.display = nb.scrollHeight > nb.clientHeight ? '' : 'none';
      }
      menu.style.opacity = '1';
    });
  }

  /* ─── 事件处理 ────────────────────────────────────────────── */
  function handleTextSelection(e) {
    var selMenu = document.getElementById('hl-selection-menu');
    if (e && e.target && selMenu && selMenu.contains(e.target)) return;
    if (SMHighlights._suppressSelMenuUntil && Date.now() < SMHighlights._suppressSelMenuUntil) return;
    var sel = window.getSelection();
    if (!sel || sel.toString().trim().length === 0) return;
    if (!sel.rangeCount) return;
    var range     = sel.getRangeAt(0);
    var rangeNode = range.commonAncestorContainer;
    var container = (rangeNode.nodeType === 3 ? rangeNode.parentElement : rangeNode)
                    .closest('#reader-content, .page-view');
    if (!container) return;
    showSelectionMenu(range.cloneRange());
  }

  function setupEventListeners() {
    if (SMHighlights._listenersSetup) return;
    SMHighlights._listenersSetup = true;
    var _showTimer = null;

    function hideSelMenu() {
      var m = document.getElementById('hl-selection-menu');
      if (m && m.style.display !== 'none') m.style.display = 'none';
    }

    document.addEventListener('touchstart', function () { clearTimeout(_showTimer); hideSelMenu(); }, { passive: true });
    document.addEventListener('mouseup', function (e) {
      clearTimeout(_showTimer);
      _showTimer = setTimeout(function () { handleTextSelection(e); }, 50);
    });
    document.addEventListener('selectionchange', function () {
      hideSelMenu();
      clearTimeout(_showTimer);
      _showTimer = setTimeout(function () {
        var sel = window.getSelection();
        if (sel && sel.toString().trim().length > 0) handleTextSelection();
      }, 350);
    });
    window.addEventListener('scroll', function () { hideAllMenus(); }, { passive: true });
    document.addEventListener('click', function (e) {
      var ni = e.target.closest ? e.target.closest('.bk-hl-note-icon') : null;
      var hl = e.target.closest ? e.target.closest('.bk-highlight') : null;
      if (ni) { e.stopPropagation(); showAnnotationMenu(ni.dataset.highlightId, ni); return; }
      if (hl) {
        var sel = window.getSelection();
        if (sel && sel.toString().trim().length > 0) return;
        e.stopPropagation();
        showAnnotationMenu(hl.dataset.highlightId, hl);
        return;
      }
      var selMenu = document.getElementById('hl-selection-menu');
      var annMenu = document.getElementById('hl-annotation-menu');
      var outsideSel = selMenu && selMenu.style.display !== 'none' && !selMenu.contains(e.target);
      var outsideAnn = annMenu && annMenu.style.display !== 'none' && !annMenu.contains(e.target);
      if (outsideSel || outsideAnn) hideAllMenus();
    });
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape') hideAllMenus();
    });
  }

  /* ─── 初始化 ──────────────────────────────────────────────── */
  function init() {
    SMHighlights._selectedColor = CONFIG.defaultColor;
    createSelectionMenu();
    createAnnotationMenu();
    createNoteModal();
    setupEventListeners();
    restoreHighlights();
  }

  // 供 reader.js 换页后调用（doPageSwap → afterSwap → refresh）
  function refresh() {
    clearAllMarks();
    restoreHighlights();
  }

  SMHighlights.init = init;
  SMHighlights.refresh = refresh;
  SMHighlights.clearAllHighlightsForce = clearAllHighlightsForce;
  window.SMHighlights = SMHighlights;

  // 暴露 refresh 到 window，reader.js 换页后可调用
  if (!window.SMReader) window.SMReader = {};
  window.SMReader.refreshHighlights = refresh;

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
"""


def __helper_bind_public_api():
    """占位：确保本模块被模板导出时语义清晰（无需真正调用）。"""
    return HIGHLIGHT_JS