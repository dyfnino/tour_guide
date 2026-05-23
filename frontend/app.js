App({
  onLaunch() {
    const token = wx.getStorageSync('token');
    const userInfo = wx.getStorageSync('userInfo');
    if (token && userInfo) {
      this.globalData.token = token;
      this.globalData.userInfo = userInfo;
    }
  },

  // 主动退出登录
  logout() {
    wx.removeStorageSync('token');
    wx.removeStorageSync('userInfo');
    this.globalData.token = null;
    this.globalData.userInfo = null;
    wx.reLaunch({ url: '/pages/login/login' });
  },

  globalData: {
    userInfo: null,
    token: null,
    apiBase: 'http://localhost:8000'
  }
});