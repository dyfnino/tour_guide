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
    // 后端 answer 字段为 JSON：单选/判断为 int，多选为 [int]；
    // 数据库经反序列化也可能把 int 包成 [int]，此处统一兼容。
    const ans = cur.answer;
    if (cur.type === 'multi') {
      const ansArr = Array.isArray(ans) ? ans : [ans];
      const a = [...ansArr].sort().join(',');
      const s = [...this.data.selected].sort().join(',');
      correct = a === s;
    } else {
      const ansVal = Array.isArray(ans) ? ans[0] : ans;
      correct = this.data.selected.length === 1 && this.data.selected[0] === ansVal;
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