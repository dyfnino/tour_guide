const { getMe } = require('../../utils/api.js');

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

  async loadUserInfo() {
    const token = wx.getStorageSync('token');
    if (token && !String(token).startsWith('mock-')) {
      // 有真实 token，从服务端获取用户信息
      try {
        const res = await getMe();
        this.setData({
          isLogin: true,
          userInfo: {
            avatarUrl: res.avatar || 'https://picsum.photos/80/80?random=12',
            nickName: res.nickname || '用户',
            action: '已登录'
          }
        });
        // 同步到本地缓存
        wx.setStorageSync('userInfo', {
          nickName: res.nickname,
          avatarUrl: res.avatar
        });
      } catch (err) {
        // token 过期，清除登录态
        console.error('获取用户信息失败:', err);
        this.clearLoginState();
      }
    } else {
      // 检查本地缓存（可能是 mock 登录的旧数据）
      const stored = wx.getStorageSync('userInfo');
      if (stored && stored.nickName && token) {
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
    }
  },

  clearLoginState() {
    wx.removeStorageSync('userInfo');
    wx.removeStorageSync('token');
    this.setData({
      isLogin: false,
      userInfo: {
        avatarUrl: 'https://picsum.photos/80/80?random=12',
        nickName: '游客',
        action: '点击登录/注册'
      }
    });
  },

  onShareAppMessage() {
    return { title: '导游服务平台', path: '/pages/home/home' };
  },

  onLoginTap() {
    if (this.data.isLogin) {
      wx.showActionSheet({
        itemList: ['退出登录'],
        success: (res) => {
          if (res.tapIndex === 0) {
            this.clearLoginState();
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