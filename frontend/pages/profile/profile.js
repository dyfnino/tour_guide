Page({
  data: {
    isLogin: false,
    userInfo: {
      avatarUrl: 'https://picsum.photos/80/80?random=12',
      nickName: '游客',
      action: '点击登录/注册'
    }
  },

  onShow() {
    this.loadUserInfo();
  },

  loadUserInfo() {
    const stored = wx.getStorageSync('userInfo');
    if (stored && stored.nickName) {
      this.setData({
        isLogin: true,
        userInfo: {
          avatarUrl: stored.avatarUrl || this.data.userInfo.avatarUrl,
          nickName: stored.nickName,
          action: '已登录'
        }
      });
    } else {
      this.setData({
        isLogin: false,
        userInfo: {
          avatarUrl: 'https://picsum.photos/80/80?random=12',
          nickName: '游客',
          action: '点击登录/注册'
        }
      });
    }
  },

  onShareAppMessage() {
    return { title: '导游服务平台', path: '/pages/home/home' };
  },

  // 登录入口
  onLoginTap() {
    if (this.data.isLogin) {
      wx.showActionSheet({
        itemList: ['退出登录'],
        success: (res) => {
          if (res.tapIndex === 0) {
            wx.removeStorageSync('userInfo');
            wx.removeStorageSync('token');
            this.loadUserInfo();
            wx.showToast({ title: '已退出', icon: 'success' });
          }
        }
      });
    } else {
      wx.navigateTo({ url: '/pages/login/login' });
    }
  },

  onMyCoursesTap() {
    wx.navigateTo({ url: '/pages/profile/my-courses/my-courses' });
  },

  onMyOrdersTap() {
    wx.navigateTo({ url: '/pages/profile/orders/orders' });
  },

  onDistributionTap() {
    wx.navigateTo({ url: '/pages/profile/placeholder/placeholder?title=分销中心' });
  },

  onWalletTap() {
    wx.navigateTo({ url: '/pages/profile/placeholder/placeholder?title=我的钱包' });
  },

  onSettingsTap() {
    wx.navigateTo({ url: '/pages/profile/placeholder/placeholder?title=设置' });
  },

  onCustomerServiceTap() {
    wx.makePhoneCall({ phoneNumber: '4001234567', fail: () => {
      wx.showToast({ title: '客服：400-123-4567', icon: 'none' });
    }});
  },

  onFAQTap() {
    wx.navigateTo({ url: '/pages/profile/placeholder/placeholder?title=常见问题' });
  },

  onContactUsTap() {
    wx.showModal({ title: '联系我们', content: '客服电话：400-123-4567\n邮箱：support@guide.com', showCancel: false });
  }
});