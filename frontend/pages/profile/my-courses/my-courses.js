const { myCoursesDetail, listCourses } = require('../../../utils/api.js');

Page({
  data: {
    list: []
  },

  onLoad() {
    this.loadMyCourses();
  },

  async loadMyCourses() {
    try {
      // 先尝试获取我的课程（含学习进度）
      const res = await myCoursesDetail();
      const list = (res || []).map(c => ({
        id: c.course_id || c.id,
        name: c.name || '课程',
        image: c.image || '',
        desc: c.description || '',
        price: c.is_free ? '免费' : ('¥' + (c.price || 0)),
        progress: c.progress || 0,
        category: c.category || ''
      }));
      this.setData({ list });
    } catch (err) {
      // 如果接口报错（如未登录），回退到课程列表
      console.warn('我的课程接口失败，回退课程列表:', err);
      try {
        const res = await listCourses();
        const list = (res || []).map((c, i) => ({
          id: c.id,
          name: c.name,
          image: c.image,
          desc: c.description || '',
          price: c.is_free ? '免费' : ('¥' + c.price),
          progress: 0,
          category: c.category
        }));
        this.setData({ list });
      } catch (e) {
        console.error('课程列表加载失败:', e);
      }
    }
  },

  onCourseTap(e) {
    const id = e.currentTarget.dataset.id;
    wx.navigateTo({ url: `/pages/guide-cert/course/course?id=${id}` });
  }
});