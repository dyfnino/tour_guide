Page({
  /**
   * 页面的初始数据
   */
  data: {
    currentTab: 'online',
    selectedCategory: 'all',
    courseList: [
      {
        id: 1,
        name: '导游资格证考试全程班',
        image: 'https://picsum.photos/120/80?random=5',
        desc: '36课时 | 适合零基础',
        price: '¥199',
        rating: '98%好评'
      },
      {
        id: 2,
        name: '导游词创作与讲解技巧',
        image: 'https://picsum.photos/120/80?random=6',
        desc: '18课时 | 进阶提升',
        price: '¥99',
        rating: '96%好评'
      },
      {
        id: 3,
        name: '政策法规高频考点解析',
        image: 'https://picsum.photos/120/80?random=7',
        desc: '12课时 | 考点精讲',
        price: '¥69',
        rating: '99%好评'
      }
    ]
  },

  /**
   * 生命周期函数--监听页面加载
   */
  onLoad(options) {
    console.log('Guide cert page loaded');
  },

  /**
   * 生命周期函数--监听页面初次渲染完成
   */
  onReady() {
    console.log('Guide cert page ready');
  },

  /**
   * 生命周期函数--监听页面显示
   */
  onShow() {
    console.log('Guide cert page shown');
  },

  /**
   * 生命周期函数--监听页面隐藏
   */
  onHide() {
    console.log('Guide cert page hidden');
  },

  /**
   * 生命周期函数--监听页面卸载
   */
  onUnload() {
    console.log('Guide cert page unloaded');
  },

  /**
   * 页面相关事件处理函数--监听用户下拉动作
   */
  onPullDownRefresh() {
    console.log('Guide cert page pull down refresh');
    // 模拟刷新数据
    setTimeout(() => {
      wx.stopPullDownRefresh();
    }, 1000);
  },

  /**
   * 页面上拉触底事件的处理函数
   */
  onReachBottom() {
    console.log('Guide cert page reach bottom');
  },

  /**
   * 用户点击右上角分享
   */
  onShareAppMessage() {
    return {
      title: '导游考证',
      path: '/pages/guide-cert/guide-cert'
    };
  },

  // 切换标签页
  switchTab(e) {
    const tab = e.currentTarget.dataset.tab;
    this.setData({
      currentTab: tab
    });
  },

  // 选择分类
  selectCategory(e) {
    const category = e.currentTarget.dataset.category;
    this.setData({
      selectedCategory: category
    });
    // 根据分类筛选课程
    this.filterCourses(category);
  },

  // 根据分类筛选课程
  filterCourses(category) {
    console.log('Filter courses by category:', category);
    // 实现课程筛选逻辑
  }
})