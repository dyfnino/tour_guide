Page({
  data: { title: '功能开发中' },
  onLoad(options) {
    const title = options.title || '功能开发中';
    this.setData({ title });
    wx.setNavigationBarTitle({ title });
  }
});