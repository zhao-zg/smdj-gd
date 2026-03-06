# -*- coding: utf-8 -*-
"""TTS JS（Capacitor 原生 + Web Speech API）"""

# ================== TTS JS – native Capacitor TTS + Web Speech API fallback ==================
TTS_JS = r"""
/* 句级 TTS v4.0 – Capacitor 原生 TTS (APK) / Web Speech API (PWA/浏览器) */

/* ---- 语音引擎适配器 ---- */
class WebSpeechEngine{
  constructor(){
    this.synth=window.speechSynthesis;this.voice=null;this._retry=0;this._timer=null;
    const load=()=>{const vs=this.synth.getVoices();if(vs&&vs.length){this.voice=vs.find(v=>/^zh/i.test(v.lang))||vs.find(v=>/Chinese/i.test(v.name))||vs[0];}else{this._retry++;this._timer=setTimeout(load,Math.min(5000,500+this._retry*250));}};
    if('onvoiceschanged' in this.synth)this.synth.onvoiceschanged=load;
    load();
  }
  speak(text,rate,pitch,volume){
    return new Promise((resolve,reject)=>{
      const u=new SpeechSynthesisUtterance(text);
      u.lang='zh-CN';if(this.voice)u.voice=this.voice;
      u.rate=rate;u.pitch=pitch;u.volume=volume;
      u.onend=()=>resolve();u.onerror=e=>reject(e);
      this.synth.speak(u);
    });
  }
  stop(){this.synth.cancel();}
  pause(){this.synth.pause();}
  resume(){this.synth.resume();}
  get supportsPause(){return true;}
}

class NativeEngine{
  constructor(p){this.p=p;}
  speak(text,rate,pitch,volume){return this.p.speak({text,lang:'zh-CN',rate,pitch,volume,category:'ambient'});}
  stop(){return this.p.stop().catch(()=>{});}
  pause(){return this.stop();}  /* 原生 TTS 无 pause，停止后保留位置 */
  resume(){}
  get supportsPause(){return false;}
}

function createEngine(){
  const cap=window.Capacitor;
  if(cap&&typeof cap.isNativePlatform==='function'&&cap.isNativePlatform()){
    const p=cap.Plugins?.TextToSpeech;
    if(p&&typeof p.speak==='function'){console.log('[TTS] 使用原生 Capacitor TTS');return new NativeEngine(p);}
    console.warn('[TTS] Capacitor 已检测但找不到 TextToSpeech 插件');
  }
  if('speechSynthesis' in window){console.log('[TTS] 使用 Web Speech API');return new WebSpeechEngine();}
  return null;
}

/* ---- TTSDock ---- */
class TTSDock{
  constructor(){
    this.engine=createEngine();
    if(!this.engine){
      window.TTS_SUPPORTED=false;
      setTimeout(()=>{if('speechSynthesis' in window){this.engine=new WebSpeechEngine();window.TTS_SUPPORTED=true;document.querySelectorAll('#tts-toggle-chips .chip').forEach(c=>{c.classList.remove('disabled');c.style.opacity='';});}},1500);
      document.getElementById('tts-dock')?.setAttribute('data-visible','false');
      return;
    }
    window.TTS_SUPPORTED=true;
    this.sentences=[];this.index=0;
    this.playing=false;this.paused=false;this.continuous=false;
    this.rate=1;this.pitch=1;this.volume=1;
    this._dragging=false;this._lastSpokenIndex=-1;
    this._segmented=false;this._wasPlayingBeforeDrag=false;
    this.presegment=document.getElementById('reader-content')?.dataset.presegment==='true';
    this.restore();this.cache();this.bind();
    if(this.presegment){this.segmentDocument();this.collect();}
    else{window.addEventListener('tts-lazy-segment',()=>this.lazySegment(),{once:true});}
    this.updateAll();
  }
  lazySegment(){if(this._segmented)return;this.segmentDocument();this.collect();}
  restore(){try{const s=JSON.parse(localStorage.getItem('tts.dock.settings')||'{}');this.rate=s.rate??1;this.pitch=s.pitch??1;this.volume=s.volume??1;this.continuous=s.continuous??false;}catch(e){}}
  save(){localStorage.setItem('tts.dock.settings',JSON.stringify({rate:this.rate,pitch:this.pitch,volume:this.volume,continuous:this.continuous}));}
  cache(){this.dock=document.getElementById('tts-dock');this.btnPrev=document.getElementById('tts-btn-prev');this.btnPlay=document.getElementById('tts-btn-play');this.btnNext=document.getElementById('tts-btn-next');this.btnStop=document.getElementById('tts-btn-stop');this.btnMode=document.getElementById('tts-btn-mode');this.btnClose=document.getElementById('tts-btn-close');this.bar=document.getElementById('tts-progress-bar');this.fill=document.getElementById('tts-progress-fill');this.handle=document.getElementById('tts-progress-handle');this.text=document.getElementById('tts-progress-text');}
  bind(){
    this.btnPlay?.addEventListener('click',()=>this.togglePlay());
    this.btnPrev?.addEventListener('click',()=>this.previous());
    this.btnNext?.addEventListener('click',()=>this.next());
    this.btnStop?.addEventListener('click',()=>this.stop());
    this.btnMode?.addEventListener('click',()=>{this.continuous=!this.continuous;this.updateMode();this.save();});
    this.btnClose?.addEventListener('click',()=>{this.stop();this.dock.setAttribute('data-visible','false');try{const r=JSON.parse(localStorage.getItem('reader.settings.v3.6.3')||'{}');r.ttsVisible=false;localStorage.setItem('reader.settings.v3.6.3',JSON.stringify(r));document.querySelectorAll('#tts-toggle-chips .chip').forEach(ch=>{if(ch.dataset.tts==='show')ch.classList.remove('active');if(ch.dataset.tts==='hide')ch.classList.add('active');});}catch(e){}});
    this.bar?.addEventListener('click',e=>{if(this._dragging)return;this._seek(e,true);});
    const startDrag=e=>{if(!this.sentences.length)return;this._dragging=true;this._wasPlayingBeforeDrag=this.playing;if(this.playing||this.paused){this.engine.stop();this.playing=false;this.paused=false;}this._seek(e,false);document.addEventListener('mousemove',moveDrag);document.addEventListener('mouseup',endDrag);document.addEventListener('touchmove',moveDrag,{passive:false});document.addEventListener('touchend',endDrag);};
    const moveDrag=e=>{if(!this._dragging)return;e.preventDefault();this._seek(e,false);};
    const endDrag=()=>{if(!this._dragging)return;this._dragging=false;document.removeEventListener('mousemove',moveDrag);document.removeEventListener('mouseup',endDrag);document.removeEventListener('touchmove',moveDrag);document.removeEventListener('touchend',endDrag);if(this._wasPlayingBeforeDrag){this.playing=true;this.paused=false;this.speakCurrent();}else{this.highlightCurrent();this.updateProgress();}};
    this.bar?.addEventListener('mousedown',startDrag);this.handle?.addEventListener('mousedown',startDrag);
    this.bar?.addEventListener('touchstart',startDrag,{passive:false});this.handle?.addEventListener('touchstart',startDrag,{passive:false});
    document.addEventListener('keydown',e=>{if(['INPUT','TEXTAREA','SELECT'].includes(e.target.tagName))return;if(e.key===' '){e.preventDefault();this.togglePlay();}else if(e.key==='Escape'){this.stop();}});
    document.addEventListener('visibilitychange',()=>{if(document.hidden&&this.playing)this.pause();});
  }
  _clientX(e){return e.touches&&e.touches.length?e.touches[0].clientX:e.clientX;}
  _seek(e,play){
    if(!this.sentences.length)return;
    const rect=this.bar.getBoundingClientRect();
    let pct=(this._clientX(e)-rect.left)/rect.width;pct=Math.min(1,Math.max(0,pct));
    this.index=Math.round(pct*(this.sentences.length-1));
    if(play&&(this.playing||this.paused)){this.engine.stop();setTimeout(()=>this.speakCurrent(),60);}
    else{this.highlightCurrent();this.updateProgress();}
  }
  segmentDocument(){
    const root=document.getElementById('reader-content');if(!root||root.dataset.ttsSegmented==='true')return;
    const walker=document.createTreeWalker(root,NodeFilter.SHOW_TEXT,{acceptNode:n=>{if(!n.parentElement)return NodeFilter.FILTER_REJECT;if(['SCRIPT','STYLE','NOSCRIPT'].includes(n.parentElement.tagName))return NodeFilter.FILTER_REJECT;if(!n.textContent.trim())return NodeFilter.FILTER_REJECT;return NodeFilter.FILTER_ACCEPT;}});
    let node;const nodes=[];while(node=walker.nextNode())nodes.push(node);
    const splitter=/([^。！？!?；;…]*[。！？!?；;…]|[^。！？!?；;…]+$)/g;let idx=0;
    nodes.forEach(tn=>{const parts=tn.textContent.match(splitter);if(!parts)return;const frag=document.createDocumentFragment();parts.forEach(p=>{const s=p.trim();if(!s)return;const sp=document.createElement('span');sp.className='tts-sentence';sp.dataset.ttsIndex=String(idx++);sp.textContent=s;frag.appendChild(sp);});tn.parentNode.replaceChild(frag,tn);});
    root.dataset.ttsSegmented='true';this._segmented=true;
  }
  collect(){this.sentences=[...document.querySelectorAll('#reader-content .tts-sentence')].map(sp=>({el:sp,text:sp.textContent}));this.updateProgress();}
  togglePlay(){this.playing?this.pause():this.play();}
  play(){
    if(!this._segmented){this.segmentDocument();this.collect();}
    if(!this.sentences.length)return;
    if(this.paused&&this.engine.supportsPause){this.engine.resume();this.paused=false;this.playing=true;this.updateAll();return;}
    this.playing=true;this.paused=false;this.updateAll();this.speakCurrent();
  }
  pause(){
    if(!this.playing)return;
    this.engine.pause();
    this.playing=false;this.paused=true;this.updateAll();
  }
  stop(){this.engine.stop();this.playing=false;this.paused=false;this.index=0;this._lastSpokenIndex=-1;this.clearHighlight();this.updateAll();}
  previous(){this.index=Math.max(0,this.index-1);if(this.playing||this.paused){this.engine.stop();this.playing=true;this.paused=false;setTimeout(()=>this.speakCurrent(),60);}else{this.highlightCurrent();this.updateProgress();}}
  next(){this.index=Math.min(this.sentences.length-1,this.index+1);if(this.playing||this.paused){this.engine.stop();this.playing=true;this.paused=false;setTimeout(()=>this.speakCurrent(),60);}else{this.highlightCurrent();this.updateProgress();}}
  async speakCurrent(){
    if(!this.sentences.length){this.stop();return;}
    if(this.index>=this.sentences.length){
      if(this.continuous&&window.PAGE_INFO?.nextPage){setTimeout(()=>window.location.href=window.PAGE_INFO.nextPage,600);}else{this.stop();}
      return;
    }
    const myIndex=this.index;
    const seg=this.sentences[myIndex];
    this.highlightElement(seg.el);this.updateProgress();
    this._lastSpokenIndex=myIndex;
    try{
      await this.engine.speak(seg.text,this.rate,this.pitch,this.volume);
    }catch(e){
      if(!this.playing)return;
      this.index++;setTimeout(()=>this.speakCurrent(),120);return;
    }
    if(!this.playing||this.index!==myIndex)return;
    this.index++;setTimeout(()=>this.speakCurrent(),40);
  }
  highlightElement(el){this.clearHighlight();if(!el)return;el.classList.add('tts-active');const r=el.getBoundingClientRect(),vh=window.innerHeight;if(r.top<80||r.bottom>vh-120){el.scrollIntoView({behavior:'smooth',block:'center'});}}
  highlightCurrent(){const seg=this.sentences[this.index];if(seg)this.highlightElement(seg.el);}
  clearHighlight(){document.querySelectorAll('.tts-active').forEach(e=>e.classList.remove('tts-active'));}
  updateProgress(){if(!this.sentences.length){this.fill&&(this.fill.style.width='0%');this.handle&&(this.handle.style.left='0%');this.text&&(this.text.textContent='0 / 0');return;}if(this.sentences.length===1){this.fill&&(this.fill.style.width='100%');this.handle&&(this.handle.style.left='100%');this.text&&(this.text.textContent='1 / 1');return;}const pct=(this.index/(this.sentences.length-1))*100;this.fill&&(this.fill.style.width=pct+'%');this.handle&&(this.handle.style.left=pct+'%');this.text&&(this.text.textContent=`${this.index+1} / ${this.sentences.length}`);}
  updateMode(){if(this.btnMode)this.btnMode.textContent=this.continuous?'🔁':'🔂';}
  updateButtons(){const disabled=window.TTS_SUPPORTED===false;[this.btnPrev,this.btnPlay,this.btnNext,this.btnStop,this.btnMode].forEach(b=>{if(b)b.disabled=disabled;});}
  updateAll(){if(this.btnPlay)this.btnPlay.textContent=this.playing?'⏸️':'▶️';this.updateMode();this.updateProgress();this.updateButtons();}
}
document.addEventListener('DOMContentLoaded',()=>{window._ttsDock=new TTSDock();});
"""

# ================== SW 注册 (多候选探测) ==================
