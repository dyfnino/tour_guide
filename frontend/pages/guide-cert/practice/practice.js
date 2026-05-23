const { questionBank } = require('../../../utils/mock.js');

Page({
  data: {
    questions: questionBank,
    index: 0,
    current: null,
    selected: [],   // 多选支持
    submitted: false,
    isCorrect: false,
    correctCount: 0
  },

  onLoad() {
    this.loadQuestion(0);
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