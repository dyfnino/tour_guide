const { listQuestions } = require('../../../utils/api.js');

Page({
  data: {
    questions: [],
    index: 0,
    current: null,
    selected: [],
    submitted: false,
    isCorrect: false,
    correctCount: 0
  },

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
      if (questions.length > 0) {
        this.loadQuestion(0);
      }
    } catch (err) {
      console.error('题库加载失败:', err);
      wx.showToast({ title: '题库加载失败', icon: 'none' });
    }
  },

  loadQuestion(i) {
    const list = this.data.questions;
    if (i >= list.length) {
      wx.showModal({
        title: '练习结束',
        content: `本次共答 ${list.length} 题，正确 ${this.data.correctCount} 题`,
        showCancel: false,
        success: () => wx.navigateBack()
      });
      return;
    }
    this.setData({
      index: i,
      current: list[i],
      selected: [],
      submitted: false,
      isCorrect: false
    });
  },

  onOptionTap(e) {
    if (this.data.submitted) return;
    const idx = e.currentTarget.dataset.index;
    const cur = this.data.current;
    if (cur.type === 'multi') {
      let arr = [...this.data.selected];
      if (arr.includes(idx)) arr = arr.filter(v => v !== idx);
      else arr.push(idx);
      this.setData({ selected: arr });
    } else {
      this.setData({ selected: [idx] });
    }
  },

  onSubmit() {
    if (this.data.selected.length === 0) {
      wx.showToast({ title: '请先选择答案', icon: 'none' });
      return;
    }
    const cur = this.data.current;
    let correct = false;
    if (cur.type === 'multi') {
      const ans = [...cur.answer].sort().join(',');
      const sel = [...this.data.selected].sort().join(',');
      correct = ans === sel;
    } else {
      correct = this.data.selected[0] === cur.answer;
    }
    this.setData({
      submitted: true,
      isCorrect: correct,
      correctCount: this.data.correctCount + (correct ? 1 : 0)
    });
  },

  onNext() {
    this.loadQuestion(this.data.index + 1);
  },

  onPrev() {
    if (this.data.index === 0) {
      wx.showToast({ title: '已是第一题', icon: 'none' });
      return;
    }
    this.loadQuestion(this.data.index - 1);
  }
});