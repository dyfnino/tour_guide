const { wechatLogin } = require('../../utils/api.js');

Page({
  data: {
    loading: false
  },

  onLoad() {},

  onShareAppMessage() {
    return { title: '导游服务平台', path: '/pages/login/login' };
  },

  // 微信登录
  wechatLogin() {
    if (this.data.loading) return;
    this.setData({ loading: true });

    // 先获取用户信息
    wx.getUserProfile({
      desc: '用于完善会员资料',
      success: (profileRes) => {
        const userInfo = profileRes.userInfo;
        // 再获取微信登录 code
        wx.login({
          success: (loginRes) => {
            if (loginRes.code) {
              this.doLogin(loginRes.code, userInfo);
            } else {
              wx.showToast({ title: '微信登录失败', icon: 'none' });
              this.setData({ loading: false });
            }
          },
          fail: () => {
            wx.showToast({ title: '获取登录凭证失败', icon: 'none' });
            this.setData({ loading: false });
          }
        });
      },
      fail: () => {
        wx.showToast({ title: '已取消授权', icon: 'none' });
        this.setData({ loading: false });
      }
    });
  },

  async doLogin(code, userInfo) {
    try {
      const res = await wechatLogin(code);
      // 登录成功，存储 token 和用户信息
      wx.setStorageSync('token', res.access_token);
      const userData = {
        nickName: res.user.nickname || userInfo.nickName,
        avatarUrl: res.user.avatar || userInfo.avatarUrl
      };
      wx.setStorageSync('userInfo', userData);
      const app = getApp();
      if (app && app.globalData) {
        app.globalData.token = res.access_token;
        app.globalData.userInfo = userData;
      }
      wx.showToast({ title: '登录成功', icon: 'success' });
      setTimeout(() => {
        wx.switchTab({ url: '/pages/profile/profile' });
      }, 800);
    } catch (err) {
      console.error('登录失败:', err);
      wx.showToast({ title: '登录失败，请重试', icon: 'none' });
    } finally {
      this.setData({ loading: false });
    }
  }
});