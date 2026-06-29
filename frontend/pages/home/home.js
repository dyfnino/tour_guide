const { listCourses } = require('../../utils/api.js');

Page({
  data: {
    swiperList: [
      { id: 1, image: 'https://picsum.photos/id/1036/800/400', text: '西安兵马俑 - 世界文化遗产' },
      { id: 2, image: 'https://picsum.photos/id/1039/800/400', text: '大雁塔 - 唐代建筑瑰宝' },
      { id: 3, image: 'https://picsum.photos/id/1018/800/400', text: '西安城墙 - 明代古城墙' }
    ],
    courseList: []
  },

  onLoad() {
    this.loadData();
  },

  async loadData() {
    try {
      const coursesRes = await listCourses({ limit: 4 });
      this.setData({
        courseList: (coursesRes || []).map(c => ({
          id: c.id,
          name: c.name,
          image: c.image,
          desc: c.description || '',
          price: c.is_free ? '免费' : ('¥' + c.price),
          category: c.category
        }))
      });
    } catch (err) {
      console.error('首页数据加载失败:', err);
    }
  },

  onPullDownRefresh() {
    this.loadData().then(() => wx.stopPullDownRefresh());
  },

  onShareAppMessage() {
    return { title: '导游服务平台', path: '/pages/home/home' };
  },

  navigateToGuideCert() {
    wx.switchTab({ url: '/pages/guide-cert/guide-cert' });
  },

  navigateToLive() {
    wx.navigateTo({ url: '/pages/live/live' });
  },

  navigateToAiTest() {
    wx.navigateTo({ url: '/pages/ai-test/ai-test' });
  },

  onCourseMoreTap() {
    wx.switchTab({ url: '/pages/guide-cert/guide-cert' });
  },

  onCourseTap(e) {
    const id = e.currentTarget.dataset.id;
    wx.navigateTo({ url: `/pages/guide-cert/course/course?id=${id || 1}` });
  }
});