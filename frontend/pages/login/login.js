Page({
  /**
   * 页面的初始数据
   */
  data: {
    loading: false
  },

  /**
   * 生命周期函数--监听页面加载
   */
  onLoad(options) {
    console.log('Login page loaded');
  },

  /**
   * 生命周期函数--监听页面初次渲染完成
   */
  onReady() {
    console.log('Login page ready');
  },

  /**
   * 生命周期函数--监听页面显示
   */
  onShow() {
    console.log('Login page shown');
  },

  /**
   * 生命周期函数--监听页面隐藏
   */
  onHide() {
    console.log('Login page hidden');
  },

  /**
   * 生命周期函数--监听页面卸载
   */
  onUnload() {
    console.log('Login page unloaded');
  },

  /**
   * 用户点击右上角分享
   */
  onShareAppMessage() {
    return {
      title: '导游服务平台',
      path: '/pages/login/login'
    };
  },

  // 微信登录
  async wechatLogin() {
    if (this.data.loading) return;
    
    this.setData({ loading: true });
    wx.showLoading({ title: '登录中...' });
    
    try {
      // 调用App实例的微信登录方法
      const app = getApp();
      const userInfo = await app.wechatLogin();
      
      console.log('Wechat login successful:', userInfo);
      wx.showToast({ title: '登录成功', icon: 'success' });
      
      // 登录成功后跳转到首页
      setTimeout(() => {
        wx.switchTab({ url: '/pages/home/home' });
      }, 1000);
    } catch (error) {
      console.error('Wechat login failed:', error);
      wx.showToast({ title: '登录失败，请重试', icon: 'none' });
    } finally {
      this.setData({ loading: false });
      wx.hideLoading();
    }
  }
})