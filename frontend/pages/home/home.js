const { courses } = require('../../utils/mock.js');

Page({
  data: {
    swiperList: [
      { id: 1, image: 'https://picsum.photos/id/1036/800/400', text: '西安兵马俑 - 世界文化遗产' },
      { id: 2, image: 'https://picsum.photos/id/1039/800/400', text: '大雁塔 - 唐代建筑瑰宝' },
      { id: 3, image: 'https://picsum.photos/id/1018/800/400', text: '西安城墙 - 明代古城墙' },
      { id: 4, image: 'https://picsum.photos/id/292/800/400', text: '西安特产 - 肉夹馍 泡馍 凉皮' },
      { id: 5, image: 'https://picsum.photos/id/401/800/400', text: '西安文创 - 兵马俑纪念品' }
    ],
    courseList: courses.slice(0, 2),
    specialtyList: [
      { id: 1, name: '手工特色糕点礼盒', image: 'https://picsum.photos/300/180?random=3', price: '¥88', tag: '热销' },
      { id: 2, name: '地方特色文创书签', image: 'https://picsum.photos/300/180?random=4', price: '¥39', tag: '新品' }
    ]
  },

  onLoad() {},

  onPullDownRefresh() {
    setTimeout(() => wx.stopPullDownRefresh(), 800);
  },

  onShareAppMessage() {
    return { title: '导游服务平台', path: '/pages/home/home' };
  },

  onSearchTap() {
    wx.showToast({ title: '搜索功能开发中', icon: 'none' });
  },

  onCartTap() {
    wx.showToast({ title: '购物车开发中', icon: 'none' });
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