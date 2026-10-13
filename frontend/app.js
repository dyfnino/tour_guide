App({
  onLaunch() {
    // 初始化云开发环境
    if (!wx.cloud) {
      console.error('请使用 2.2.3 或以上的基础库以使用云能力');
      return;
    }
    wx.cloud.init({
      resourceAppid: 'wxa6ebf64c09f3f7f4', // 服务商appid、公众号或小程序appid
      resourceEnv: 'd9gdz4gnae844e735', // 微信云托管的环境ID
      traceUser: true,               // 是否在将用户访问记录到用户管理中
    });
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
    apiBase: 'https://django-pb2g-321426-9-1442307866.sh.run.tcloudbase.com'
  }
});