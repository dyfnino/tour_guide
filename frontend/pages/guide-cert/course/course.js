const { courses } = require('../../../utils/mock.js');

Page({
  data: { course: null },

  onLoad(options) {
    const id = parseInt(options.id, 10);
    const course = courses.find(c => c.id === id) || courses[0];
    this.setData({ course });
    wx.setNavigationBarTitle({ title: course.name });
  },

  onEnroll() {
    wx.showToast({ title: '已加入学习', icon: 'success' });
  }
});