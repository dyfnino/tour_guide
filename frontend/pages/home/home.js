const { listCourses, listProducts } = require('../../utils/api.js');

Page({
  data: {
    swiperList: [
      { id: 1, image: 'https://picsum.photos/id/1036/800/400', text: '西安兵马俑 - 世界文化遗产' },
      { id: 2, image: 'https://picsum.photos/id/1039/800/400', text: '大雁塔 - 唐代建筑瑰宝' },
      { id: 3, image: 'https://picsum.photos/id/1018/800/400', text: '西安城墙 - 明代古城墙' },
      { id: 4, image: 'https://picsum.photos/id/292/800/400', text: '西安特产 - 肉夹馍 泡馍 凉皮' },
      { id: 5, image: 'https://picsum.photos/id/401/800/400', text: '西安文创 - 兵马俑纪念品' }
    ],
    courseList: [],
    specialtyList: []
  },

  onLoad() {
    this.loadData();
  },

  async loadData() {
    try {
      const [coursesRes, productsRes] = await Promise.all([
        listCourses({ limit: 2 }),
        listProducts({ limit: 2 })
      ]);
      this.setData({
        courseList: (coursesRes || []).map(c => ({
          id: c.id,
          name: c.name,
          image: c.image,
          desc: c.description || '',
          price: c.is_free ? '免费' : ('¥' + c.price),
          category: c.category
        })),
        specialtyList: (productsRes || []).map(p => ({
          id: p.id,
          name: p.name,
          image: p.image,
          price: '¥' + p.price,
          tag: p.is_hot ? '热销' : (p.is_new ? '新品' : '')
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

  navigateToSpecialty() {
    wx.switchTab({ url: '/pages/specialty/specialty' });
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

  onSpecialtyMoreTap() {
    wx.switchTab({ url: '/pages/specialty/specialty' });
  },

  onCourseTap(e) {
    const id = e.currentTarget.dataset.id;
    wx.navigateTo({ url: `/pages/guide-cert/course/course?id=${id || 1}` });
  },

  onSpecialtyTap() {
    wx.showToast({ title: '商品详情开发中', icon: 'none' });
  }
});