const { listCourses, listProducts } = require('../../utils/api.js');

// 商品分类名称映射（与商品列表页保持一致）
const SPECIALTY_CATEGORY_NAMES = {
  food: '特色食品',
  creative: '文创产品',
  craft: '手工艺品',
  local: '地方特产'
};

Page({
  data: {
    swiperList: [
      { id: 1, image: 'https://picsum.photos/id/1036/800/400', text: '西安兵马俑 - 世界文化遗产' },
      { id: 2, image: 'https://picsum.photos/id/1039/800/400', text: '大雁塔 - 唐代建筑瑰宝' },
      { id: 3, image: 'https://picsum.photos/id/1018/800/400', text: '西安城墙 - 明代古城墙' }
    ],
    courseList: [],
    specialtyList: []
  },

  onLoad() {
    this.loadData();
  },

  async loadData() {
    await Promise.all([this.loadCourses(), this.loadProducts()]);
  },

  // 推荐课程（首页仅展示 2 个）
  async loadCourses() {
    try {
      const coursesRes = await listCourses({ limit: 2 });
      this.setData({
        courseList: (coursesRes || []).map(c => ({
          id: c.id,
          name: c.name,
          image: c.image,
          desc: c.description || '',
          price: c.is_free ? '免费' : ('¥' + c.price),
          students: '2000+人已学',
          category: c.category
        }))
      });
    } catch (err) {
      console.error('首页课程数据加载失败:', err);
    }
  },

  // 特产与文创（首页仅展示 2 个）
  async loadProducts() {
    try {
      const productsRes = await listProducts({ limit: 2 });
      this.setData({
        specialtyList: (productsRes || []).map(p => ({
          id: p.id,
          name: p.name,
          image: p.image,
          price: '¥' + p.price,
          tag: p.is_hot ? '热销' : (p.is_new ? '新品' : (SPECIALTY_CATEGORY_NAMES[p.category] || '特产')),
          category: p.category
        }))
      });
    } catch (err) {
      console.error('首页特产与文创数据加载失败:', err);
    }
  },

  onPullDownRefresh() {
    this.loadData().then(() => wx.stopPullDownRefresh());
  },

  onShareAppMessage() {
    return { title: '经纬途礼服务平台', path: '/pages/home/home' };
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

  // 特产与文创入口 -> 商品列表页
  navigateToSpecialty() {
    wx.navigateTo({ url: '/pages/specialty/specialty' });
  },

  onCourseMoreTap() {
    wx.switchTab({ url: '/pages/guide-cert/guide-cert' });
  },

  onCourseTap(e) {
    const id = e.currentTarget.dataset.id;
    wx.navigateTo({ url: `/pages/guide-cert/course/course?id=${id || 1}` });
  },

  // 特产与文创「更多」-> 商品列表页
  onSpecialtyMoreTap() {
    wx.navigateTo({ url: '/pages/specialty/specialty' });
  },

  // 点击商品 -> 商品详情页
  onSpecialtyTap(e) {
    const id = e.currentTarget.dataset.id;
    if (!id) return;
    wx.navigateTo({ url: `/pages/specialty/detail/detail?id=${id}` });
  }
});
