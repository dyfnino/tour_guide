const { myCoursesDetail } = require('../../../utils/api.js');

Page({
  data: {
    list: []
  },

  onLoad() {
    this.loadMyCourses();
  },

  onShow() {
    // 从课程详情返回时刷新进度
    this.loadMyCourses();
  },

  async loadMyCourses() {
    try {
      const res = await myCoursesDetail();
      const list = (res || []).map(c => ({
        id: c.id,
        name: c.name || '课程',
        image: c.image || '',
        desc: c.desc || c.description || '',
        progress: c.progress || 0,
        lecturer: c.lecturer || ''
      }));
      this.setData({ list });
    } catch (err) {
      console.error('我的课程加载失败:', err);
      if (err.statusCode === 401) {
        wx.showModal({
          title: '请先登录',
          content: '登录后查看已购课程',
          confirmText: '去登录',
          success: (res) => {
            if (res.confirm) wx.navigateTo({ url: '/pages/login/login' });
          }
        });
      }
    }
  },

  onCourseTap(e) {
    const id = e.currentTarget.dataset.id;
    wx.navigateTo({ url: `/pages/guide-cert/course/course?id=${id}&enrolled=1` });
  }
});