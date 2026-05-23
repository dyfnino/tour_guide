Page({
  data: {
    loading: false
  },

  onLoad() {},

  onShareAppMessage() {
    return { title: '导游服务平台', path: '/pages/login/login' };
  },

  // 微信登录（演示版：通过 wx.getUserProfile 获取昵称头像后直接本地登录）
  wechatLogin() {
    if (this.data.loading) return;
    this.setData({ loading: true });

    wx.getUserProfile({
      desc: '用于完善会员资料',
      success: (res) => {
        const userInfo = res.userInfo;
        wx.setStorageSync('userInfo', userInfo);
        wx.setStorageSync('token', 'mock-' + Date.now());
        const app = getApp();
        if (app && app.globalData) {
          app.globalData.userInfo = userInfo;
          app.globalData.token = wx.getStorageSync('token');
        }
        wx.showToast({ title: '登录成功', icon: 'success' });
        setTimeout(() => {
          wx.switchTab({ url: '/pages/profile/profile' });
        }, 800);
      },
      fail: () => {
        wx.showToast({ title: '已取消授权', icon: 'none' });
      },
      complete: () => {
        this.setData({ loading: false });
      }
    });
  }
});