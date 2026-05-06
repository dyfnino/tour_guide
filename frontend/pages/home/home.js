Page({
  /**
   * 页面的初始数据
   */
  data: {
    // 轮播图数据
    swiperList: [
      {
        id: 1,
        image: 'https://picsum.photos/id/1036/800/400',
        text: '西安兵马俑 - 世界文化遗产'
      },
      {
        id: 2,
        image: 'https://picsum.photos/id/1039/800/400',
        text: '大雁塔 - 唐代建筑瑰宝'
      },
      {
        id: 3,
        image: 'https://picsum.photos/id/1018/800/400',
        text: '西安城墙 - 明代古城墙'
      },
      {
        id: 4,
        image: 'https://picsum.photos/id/292/800/400',
        text: '西安特产 - 肉夹馍 泡馍 凉皮'
      },
      {
        id: 5,
        image: 'https://picsum.photos/id/401/800/400',
        text: '西安文创 - 兵马俑纪念品'
      }
    ],
    // 推荐课程数据
    courseList: [
      {
        id: 1,
        name: '导游基础知识精讲',
        image: 'https://picsum.photos/300/180?random=1',
        price: '免费',
        students: '2000+人已学'
      },
      {
        id: 2,
        name: '导游业务能力提升',
        image: 'https://picsum.photos/300/180?random=2',
        price: '¥99',
        students: '1500+人已学'
      }
    ],
    // 热门特产数据
    specialtyList: [
      {
        id: 1,
        name: '手工特色糕点礼盒',
        image: 'https://picsum.photos/300/180?random=3',
        price: '¥88',
        tag: '热销'
      },
      {
        id: 2,
        name: '地方特色文创书签',
        image: 'https://picsum.photos/300/180?random=4',
        price: '¥39',
        tag: '新品'
      }
    ]
  },

  /**
   * 生命周期函数--监听页面加载
   */
  onLoad(options) {
    console.log('Home page loaded');
  },

  /**
   * 生命周期函数--监听页面初次渲染完成
   */
  onReady() {
    console.log('Home page ready');
  },

  /**
   * 生命周期函数--监听页面显示
   */
  onShow() {
    console.log('Home page shown');
  },

  /**
   * 生命周期函数--监听页面隐藏
   */
  onHide() {
    console.log('Home page hidden');
  },

  /**
   * 生命周期函数--监听页面卸载
   */
  onUnload() {
    console.log('Home page unloaded');
  },

  /**
   * 页面相关事件处理函数--监听用户下拉动作
   */
  onPullDownRefresh() {
    console.log('Home page pull down refresh');
    // 模拟刷新数据
    setTimeout(() => {
      wx.stopPullDownRefresh();
    }, 1000);
  },

  /**
   * 页面上拉触底事件的处理函数
   */
  onReachBottom() {
    console.log('Home page reach bottom');
  },

  /**
   * 用户点击右上角分享
   */
  onShareAppMessage() {
    return {
      title: '导游服务平台',
      path: '/pages/home/home'
    };
  },

  // 搜索按钮点击事件
  onSearchTap() {
    console.log('Search button tapped');
    // 实现搜索功能
  },

  // 购物车按钮点击事件
  onCartTap() {
    console.log('Cart button tapped');
    // 跳转到购物车页面
  },

  // 导航到导游考证页面
  navigateToGuideCert() {
    wx.navigateTo({
      url: '/pages/guide-cert/guide-cert'
    });
  },

  // 导航到特产商城页面
  navigateToSpecialty() {
    wx.navigateTo({
      url: '/pages/specialty/specialty'
    });
  },

  // 导航到直播课堂页面
  navigateToLive() {
    wx.navigateTo({
      url: '/pages/live/live'
    });
  },

  // 导航到AI测评页面
  navigateToAiTest() {
    wx.navigateTo({
      url: '/pages/ai-test/ai-test'
    });
  },

  // 课程更多点击事件
  onCourseMoreTap() {
    console.log('Course more tapped');
    // 跳转到课程列表页面
  },

  // 特产更多点击事件
  onSpecialtyMoreTap() {
    console.log('Specialty more tapped');
    // 跳转到特产列表页面
  },

  // 课程点击事件
  onCourseTap() {
    console.log('Course tapped');
    // 跳转到课程详情页面
  },

  // 特产点击事件
  onSpecialtyTap() {
    console.log('Specialty tapped');
    // 跳转到特产详情页面
  }
})