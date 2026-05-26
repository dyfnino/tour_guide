const { startExam, submitExam } = require('../../../utils/api.js');

Page({
  data: {
    started: false,
    questions: [],       // 仅包含 id/type/title/options（不含答案）
    index: 0,
    current: null,
    answers: {},         // { qid: [选项索引,...] }
    currentSelected: [],
    cardStatus: [],
    countdown: '60:00',
    finished: false,
    score: 0,
    correct: 0,
    total: 0,
    timeoutTip: false,
    submitting: false
  },

  _timer: null,
  _remain: 60 * 60,
  _examId: null,
  _duration: 3600,

  onUnload() {
    if (this._timer) clearInterval(this._timer);
  },

  promptLogin() {
    wx.showModal({
      title: '请先登录',
      content: '登录后才能参加模拟考试',
      confirmText: '去登录',
      success: (res) => {
        if (res.confirm) wx.navigateTo({ url: '/pages/login/login' });
      }
    });
  },

  async startExam() {
    const token = wx.getStorageSync('token');
    if (!token) {
      this.promptLogin();
      return;
    }
    wx.showLoading({ title: '抽题中...' });
    try {
      const res = await startExam({ count: 10, duration: 3600 });
      wx.hideLoading();
      const questions = (res.questions || []).map(q => ({
        id: q.id,
        type: q.type,
        title: q.title,
        options: q.options
      }));
      if (questions.length === 0) {
        wx.showToast({ title: '暂无题目', icon: 'none' });
        return;
      }
      this._examId = res.exam_id;
      this._duration = res.duration || 3600;
      this._remain = this._duration;

      this.setData({
        started: true,
        questions,
        index: 0,
        current: questions[0],
        answers: {},
        currentSelected: [],
        cardStatus: questions.map((_, i) => (i === 0 ? 'cur' : '')),
        finished: false,
        total: questions.length
      });

      this.updateCountdown();
      this._timer = setInterval(() => {
        this._remain -= 1;
        if (this._remain <= 0) {
          clearInterval(this._timer);
          this.submitExam(true);
          return;
        }
        this.updateCountdown();
      }, 1000);
    } catch (err) {
      wx.hideLoading();
      console.error('开始考试失败:', err);
      if (err && err.statusCode === 401) {
        this.promptLogin();
      } else {
        wx.showToast({ title: '开始考试失败', icon: 'none' });
      }
    }
  },

  updateCountdown() {
    const m = String(Math.floor(this._remain / 60)).padStart(2, '0');
    const s = String(this._remain % 60).padStart(2, '0');
    this.setData({ countdown: `${m}:${s}` });
  },

  rebuildCardStatus(answers, index) {
    return this.data.questions.map((q, i) => {
      if (i === index) return 'cur';
      const sel = answers[q.id];
      return sel && sel.length ? 'done' : '';
    });
  },

  onOptionTap(e) {
    const idx = e.currentTarget.dataset.index;
    const cur = this.data.current;
    const answers = { ...this.data.answers };
    let arr;
    if (cur.type === 'multi') {
      arr = answers[cur.id] ? [...answers[cur.id]] : [];
      const pos = arr.indexOf(idx);
      if (pos >= 0) arr.splice(pos, 1);
      else arr.push(idx);
    } else {
      arr = [idx];
    }
    answers[cur.id] = arr;
    this.setData({
      answers,
      currentSelected: arr,
      cardStatus: this.rebuildCardStatus(answers, this.data.index)
    });
  },

  goToQuestion(e) {
    const i = e.currentTarget.dataset.index;
    this.switchTo(i);
  },

  onPrev() {
    const i = this.data.index;
    if (i === 0) return wx.showToast({ title: '已是第一题', icon: 'none' });
    this.switchTo(i - 1);
  },

  onNext() {
    const i = this.data.index;
    if (i >= this.data.questions.length - 1) {
      return wx.showToast({ title: '已是最后一题', icon: 'none' });
    }
    this.switchTo(i + 1);
  },

  switchTo(i) {
    const q = this.data.questions[i];
    this.setData({
      index: i,
      current: q,
      currentSelected: this.data.answers[q.id] ? [...this.data.answers[q.id]] : [],
      cardStatus: this.rebuildCardStatus(this.data.answers, i)
    });
  },

  confirmSubmit() {
    wx.showModal({
      title: '交卷',
      content: '确认提交试卷吗？',
      success: (res) => res.confirm && this.submitExam(false)
    });
  },

  async submitExam(timeout) {
    if (this._timer) clearInterval(this._timer);
    if (!this._examId || this.data.submitting) return;
    this.setData({ submitting: true });
    wx.showLoading({ title: '提交中...' });
    try {
      // 把 answers 转成 {qid: [选项索引,...]} 字符串 key
      const payload = {};
      Object.keys(this.data.answers).forEach(k => {
        payload[String(k)] = this.data.answers[k] || [];
      });
      const res = await submitExam(this._examId, payload);
      wx.hideLoading();
      this.setData({
        finished: true,
        score: res.score || 0,
        correct: res.correct_count || 0,
        total: res.total || this.data.questions.length,
        timeoutTip: !!timeout,
        submitting: false
      });
    } catch (err) {
      wx.hideLoading();
      this.setData({ submitting: false });
      console.error('交卷失败:', err);
      wx.showToast({ title: '交卷失败，请重试', icon: 'none' });
    }
  },

  backToList() {
    wx.navigateBack();
  }
});