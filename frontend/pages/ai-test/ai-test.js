const { aiChat, aiEvaluate, uploadAiMedia, listAiTests } = require('../../utils/api.js');

Page({
  data: {
    chatMessages: [
      { id: 'sys-1', type: 'ai', content: '你好！我是基于通义千问 Qwen 多模态的 AI 导游助手。\n你可以发送文字、图片或语音来与我互动，也可以选择下方测评类型直接进入测评。' }
    ],
    inputValue: '',
    sending: false,
    pendingImages: [],   // [{path, url}] 已上传的图片
    pendingAudio: null,  // {path, url, duration}
    recording: false,
    aiTests: [],
    // 测评态
    evalMode: false,
    evalType: '',
    evalTopic: '',
    evalResult: null,
    scrollTop: 0
  },

  _msgId: 1,
  _recorder: null,

  onLoad() {
    this.loadAiTests();
  },

  async loadAiTests() {
    try {
      const res = await listAiTests();
      this.setData({ aiTests: res || [] });
    } catch (e) { /* ignore */ }
  },

  // ---- 输入 ----
  onInputChange(e) {
    this.setData({ inputValue: e.detail.value });
  },

  // 选择图片
  async onPickImage() {
    try {
      const r = await new Promise((resolve, reject) => {
        wx.chooseMedia({
          count: 3,
          mediaType: ['image'],
          sourceType: ['album', 'camera'],
          sizeType: ['compressed'],
          success: resolve,
          fail: reject
        });
      });
      wx.showLoading({ title: '上传中...' });
      const uploaded = [];
      for (const f of r.tempFiles) {
        const u = await uploadAiMedia(f.tempFilePath);
        uploaded.push({ path: u.path, url: u.url });
      }
      wx.hideLoading();
      this.setData({ pendingImages: [...this.data.pendingImages, ...uploaded] });
      wx.showToast({ title: `已添加 ${uploaded.length} 张图`, icon: 'success' });
    } catch (e) {
      wx.hideLoading();
      if (e && e.errMsg && e.errMsg.indexOf('cancel') >= 0) return;
      console.error('选图失败', e);
      wx.showToast({ title: '上传失败', icon: 'none' });
    }
  },

  removeImage(e) {
    const idx = e.currentTarget.dataset.index;
    const list = [...this.data.pendingImages];
    list.splice(idx, 1);
    this.setData({ pendingImages: list });
  },

  // 录音
  toggleRecord() {
    if (this.data.recording) {
      this.stopRecord();
    } else {
      this.startRecord();
    }
  },

  startRecord() {
    if (!this._recorder) {
      this._recorder = wx.getRecorderManager();
      this._recorder.onStop(async (res) => {
        this.setData({ recording: false });
        if (!res.tempFilePath) return;
        try {
          wx.showLoading({ title: '上传录音...' });
          const u = await uploadAiMedia(res.tempFilePath);
          wx.hideLoading();
          this.setData({
            pendingAudio: { path: u.path, url: u.url, duration: res.duration }
          });
          wx.showToast({ title: '已添加录音', icon: 'success' });
        } catch (e) {
          wx.hideLoading();
          wx.showToast({ title: '录音上传失败', icon: 'none' });
        }
      });
      this._recorder.onError((err) => {
        console.error('录音错误', err);
        this.setData({ recording: false });
      });
    }
    this._recorder.start({
      duration: 60000,
      sampleRate: 16000,
      numberOfChannels: 1,
      encodeBitRate: 48000,
      format: 'mp3'
    });
    this.setData({ recording: true });
  },

  stopRecord() {
    if (this._recorder) this._recorder.stop();
  },

  removeAudio() {
    this.setData({ pendingAudio: null });
  },

  // ---- 发送对话 ----
  async onSendMessage() {
    if (this.data.sending) return;
    const text = (this.data.inputValue || '').trim();
    const imgs = this.data.pendingImages;
    const aud = this.data.pendingAudio;
    if (!text && imgs.length === 0 && !aud) {
      wx.showToast({ title: '请输入或选择内容', icon: 'none' });
      return;
    }

    // 本地追加用户消息
    const userMsg = {
      id: 'u-' + (++this._msgId),
      type: 'user',
      content: text || (imgs.length ? '[图片]' : '') + (aud ? '[语音]' : ''),
      images: imgs.map(i => i.url),
      audio: aud ? aud.url : ''
    };
    this.setData({
      chatMessages: [...this.data.chatMessages, userMsg],
      inputValue: '',
      pendingImages: [],
      pendingAudio: null,
      sending: true,
      scrollTop: this._msgId * 1000
    });

    // 调后端
    try {
      const payload = {
        message: text,
        image_paths: imgs.map(i => i.path),
        audio_paths: aud ? [aud.path] : [],
        history: this.data.chatMessages
          .filter(m => m.type === 'user' || m.type === 'ai')
          .slice(-6)
          .map(m => ({ role: m.type === 'user' ? 'user' : 'assistant', content: m.content }))
      };
      const res = await aiChat(payload);
      const aiMsg = {
        id: 'a-' + (++this._msgId),
        type: 'ai',
        content: res.text || '（无返回）',
        modelTip: res.mock ? `模型：${res.model}（mock）` : `模型：${res.model}`
      };
      this.setData({
        chatMessages: [...this.data.chatMessages, aiMsg],
        sending: false,
        scrollTop: this._msgId * 1000
      });
    } catch (err) {
      console.error('AI 请求失败', err);
      this.setData({
        sending: false,
        chatMessages: [...this.data.chatMessages, {
          id: 'e-' + (++this._msgId), type: 'ai',
          content: '请求失败，请稍后再试'
        }]
      });
    }
  },

  // ---- 测评 ----
  onTestTypeTap(e) {
    const type = e.currentTarget.dataset.type;
    const map = {
      theory: '理论知识测评：请用文字详细回答下面的题目',
      lecture: '导游词讲解测评：请录制一段你对景点的讲解（≤60秒）',
      interview: '面试模拟测评：请结合下面问题用文字或语音作答'
    };
    const topicMap = {
      theory: '请简述《中华人民共和国旅游法》的颁布时间与核心立法目的。',
      lecture: '主题：以"故宫"为例，讲解一段不少于 200 字的导游词。',
      interview: '面试题：作为一名导游，遇到游客突发疾病你会如何应对？'
    };
    this.setData({
      evalMode: true,
      evalType: type,
      evalTopic: topicMap[type],
      evalResult: null,
      inputValue: ''
    });
    wx.showToast({ title: map[type], icon: 'none', duration: 2200 });
  },

  exitEvalMode() {
    this.setData({ evalMode: false, evalType: '', evalTopic: '', evalResult: null });
  },

  async onSubmitEvaluation() {
    if (this.data.sending) return;
    const text = (this.data.inputValue || '').trim();
    const imgs = this.data.pendingImages;
    const aud = this.data.pendingAudio;
    if (!text && imgs.length === 0 && !aud) {
      wx.showToast({ title: '请提供作答内容', icon: 'none' });
      return;
    }
    this.setData({ sending: true });
    wx.showLoading({ title: 'AI 评测中...' });
    try {
      const res = await aiEvaluate({
        test_type: this.data.evalType,
        topic: this.data.evalTopic,
        user_answer: text,
        image_paths: imgs.map(i => i.path),
        audio_paths: aud ? [aud.path] : []
      });
      wx.hideLoading();
      this.setData({
        evalResult: res,
        sending: false,
        pendingImages: [],
        pendingAudio: null,
        inputValue: ''
      });
    } catch (err) {
      wx.hideLoading();
      this.setData({ sending: false });
      console.error('测评失败', err);
      wx.showToast({ title: '测评失败', icon: 'none' });
    }
  },

  previewImage(e) {
    const url = e.currentTarget.dataset.url;
    const list = (e.currentTarget.dataset.list || '').split(',').filter(Boolean);
    wx.previewImage({ current: url, urls: list.length ? list : [url] });
  },

  playAudio(e) {
    const url = e.currentTarget.dataset.url;
    if (!url) return;
    if (this._innerAudio) { this._innerAudio.stop(); this._innerAudio.destroy(); }
    this._innerAudio = wx.createInnerAudioContext();
    this._innerAudio.src = url;
    this._innerAudio.play();
  },

  onUnload() {
    if (this._recorder && this.data.recording) {
      try { this._recorder.stop(); } catch (e) { /* ignore */ }
    }
    if (this._innerAudio) {
      try { this._innerAudio.destroy(); } catch (e) { /* ignore */ }
    }
  },

  onShareAppMessage() {
    return { title: 'AI 导游测评', path: '/pages/ai-test/ai-test' };
  }
});