const { getCourse } = require('../../../utils/api.js');

Page({
  data: { course: null },

  onLoad(options) {
    const id = options.id;
    if (id) {
      this.loadCourse(id);
    }
  },

  async loadCourse(id) {
    try {
      const res = await getCourse(id);
      this.setData({
        course: {
          id: res.id,
          name: res.name,
          image: res.image,
          desc: res.description || '',
          price: res.is_free ? '免费' : ('¥' + res.price),
          lecturer: res.level || '',
          category: res.category
        }
      });
      wx.setNavigationBarTitle({ title: res.name });
    } catch (err) {
      console.error('课程详情加载失败:', err);
      wx.showToast({ title: '加载失败', icon: 'none' });
    }
  },

  onEnroll() {
    wx.showToast({ title: '已加入学习', icon: 'success' });
  }
});