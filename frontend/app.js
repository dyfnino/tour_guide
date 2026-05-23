App({
  onLaunch() {
    // 启动时仅恢复登录态，不强制跳转登录页（无后端环境下避免卡死）
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