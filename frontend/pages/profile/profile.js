Page({
  /**
   * 页面的初始数据
   */
  data: {
    userInfo: {
      name: '游客123456',
      action: '点击登录/注册'
    }
  },

  /**
   * 生命周期函数--监听页面加载
   */
  onLoad(options) {
    console.log('Profile page loaded');
  },

  /**
   * 生命周期函数--监听页面初次渲染完成
   */
  onReady() {
    console.log('Profile page ready');
  },

  /**
   * 生命周期函数--监听页面显示
   */
  onShow() {
    console.log('Profile page shown');
  },

  /**
   * 生命周期函数--监听页面隐藏
   */
  onHide() {
    console.log('Profile page hidden');
  },

  /**
   * 生命周期函数--监听页面卸载
   */
  onUnload() {
    console.log('Profile page unloaded');
  },

  /**
   * 页面相关事件处理函数--监听用户下拉动作
   */
  onPullDownRefresh() {
    console.log('Profile page pull down refresh');
    // 模拟刷新数据
    setTimeout(() => {
      wx.stopPullDownRefresh();
    }, 1000);
  },

  /**
   * 页面上拉触底事件的处理函数
   */
  onReachBottom() {
    console.log('Profile page reach bottom');
  },

  /**
   * 用户点击右上角分享
   */
  onShareAppMessage() {
    return {
      title: '个人中心',
      path: '/pages/profile/profile'
    };
  },

  // 登录/注册
  onLoginTap() {
    console.log('Login tapped');
    // 实现登录逻辑
  },

  // 我的课程
  onMyCoursesTap() {
    console.log('My courses tapped');
    // 跳转到我的课程页面
  },

  // 我的订单
  onMyOrdersTap() {
    console.log('My orders tapped');
    // 跳转到我的订单页面
  },

  // 分销中心
  onDistributionTap() {
    console.log('Distribution tapped');
    // 跳转到分销中心页面
  },

  // 在线客服
  onCustomerServiceTap() {
    console.log('Customer service tapped');
    // 跳转到在线客服页面
  },

  // 常见问题
  onFAQTap() {
    console.log('FAQ tapped');
    // 跳转到常见问题页面
  },

  // 联系我们
  onContactUsTap() {
    console.log('Contact us tapped');
    // 跳转到联系我们页面
  }
})