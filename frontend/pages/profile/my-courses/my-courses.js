const { courses } = require('../../../utils/mock.js');

Page({
  data: {
    list: courses.map((c, i) => ({
      ...c,
      progress: [80, 45, 20, 0][i % 4]
    }))
  },

  onCourseTap(e) {
    const id = e.currentTarget.dataset.id;
    wx.navigateTo({ url: `/pages/guide-cert/course/course?id=${id}` });
  }
});