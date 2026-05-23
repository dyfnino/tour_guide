const { listQuestions } = require('../../../utils/api.js');

Page({
  data: {
    started: false,
    questions: [],
    index: 0,
    current: null,
    answers: {},
    currentSelected: [],
    cardStatus: [],
    countdown: '60:00',
    finished: false,
    score: 0,
    correct: 0,
    timeoutTip: false
  },

  _timer: null,
  _remain: 60 * 60,

  onLoad() {
    this.loadQuestions();
  },

  async loadQuestions() {
    try {
      const res = await listQuestions({ limit: 50 });
      const questions = (res || []).map(q => ({
        id: q.id,
        type: q.type,
        title: q.title,
        options: q.options,
        answer: q.answer,
        analysis: q.analysis
      }));
      this.setData({ questions });
    } catch (err) {
      console.error('题库加载失败:', err);
      wx.showToast({ title: '题库加载失败', icon: 'none' });
    }
  },

  onUnload() {
    if (this._timer) clearInterval(this._timer);
  },

  startExam() {
    const total = this.data.questions.length;
    if (total === 0) {
      wx.showToast({ title: '暂无题目', icon: 'none' });
      return;
    }
    this.setData({
      started: true,
      index: 0,
      current: this.data.questions[0],
      answers: {},
      currentSelected: [],
      cardStatus: new Array(total).fill('').map((_, i) => (i === 0 ? 'cur' : '')),
      finished: false
    });
    this._remain = 60 * 60;
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

  submitExam(timeout) {
    if (this._timer) clearInterval(this._timer);
    let correct = 0;
    this.data.questions.forEach(q => {
      const sel = (this.data.answers[q.id] || []).slice().sort().join(',');
      const ans = q.type === 'multi'
        ? [...q.answer].sort().join(',')
        : String(q.answer);
      if (sel === ans) correct += 1;
    });
    const total = this.data.questions.length;
    const score = Math.round((correct / total) * 100);
    this.setData({ finished: true, score, correct, timeoutTip: !!timeout });
  },

  backToList() {
    wx.navigateBack();
  }
});