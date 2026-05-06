App({
  onLaunch() {
    // 小程序启动时执行
    console.log('App launched');
    // 检查用户是否已登录
    this.checkLoginStatus();
  },
  onShow() {
    // 小程序显示时执行
    console.log('App shown');
  },
  onHide() {
    // 小程序隐藏时执行
    console.log('App hidden');
  },
  // 检查登录状态
  checkLoginStatus() {
    const token = wx.getStorageSync('token');
    const userInfo = wx.getStorageSync('userInfo');
    
    if (token && userInfo) {
      this.globalData.token = token;
      this.globalData.userInfo = userInfo;
      console.log('User already logged in');
    } else {
      // 未登录，跳转到登录页面
      console.log('User not logged in, redirecting to login page');
      wx.redirectTo({ url: '/pages/login/login' });
    }
  },
  // 微信登录
  async wechatLogin() {
    return new Promise((resolve, reject) => {
      wx.login({
        success: (res) => {
          if (res.code) {
            console.log('Login code:', res.code);
            // 调用后端API进行微信登录
            wx.request({
              url: 'http://localhost:8000/api/auth/wechat',
              method: 'POST',
              data: { code: res.code },
              success: (response) => {
                console.log('Wechat login response:', response.data);
                if (response.statusCode === 200) {
                  const { access_token, user } = response.data;
                  // 存储token和用户信息
                  wx.setStorageSync('token', access_token);
                  wx.setStorageSync('userInfo', user);
                  // 更新全局变量
                  this.globalData.token = access_token;
                  this.globalData.userInfo = user;
                  resolve(user);
                } else {
                  reject(new Error('Login failed'));
                }
              },
              fail: (err) => {
                console.error('Wechat login request failed:', err);
                reject(err);
              }
            });
          } else {
            reject(new Error('Failed to get login code'));
          }
        },
        fail: (err) => {
          console.error('Login failed:', err);
          reject(err);
        }
      });
    });
  },
  // 退出登录
  logout() {
    wx.removeStorageSync('token');
    wx.removeStorageSync('userInfo');
    this.globalData.token = null;
    this.globalData.userInfo = null;
    // 跳转到登录页面
    wx.redirectTo({ url: '/pages/login/login' });
  },
  globalData: {
    userInfo: null,
    token: null,
    // 数据库配置
    dbConfig: {
      host: 'localhost',
      port: 3306,
      database: 'guide',
      username: 'root',
      password: ''
    }
  }
})