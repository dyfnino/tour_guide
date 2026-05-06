Page({
  /**
   * 页面的初始数据
   */
  data: {
    replayList: [
      {
        id: 1,
        name: '导游基础知识精讲',
        image: 'https://picsum.photos/300/180?random=13',
        lecturer: '主讲：李老师',
        views: '5678'
      },
      {
        id: 2,
        name: '导游业务能力提升',
        image: 'https://picsum.photos/300/180?random=14',
        lecturer: '主讲：王老师',
        views: '3456'
      },
      {
        id: 3,
        name: '政策法规高频考点解析',
        image: 'https://picsum.photos/300/180?random=15',
        lecturer: '主讲：赵老师',
        views: '2345'
      }
    ]
  },

  /**
   * 生命周期函数--监听页面加载
   */
  onLoad(options) {
    console.log('Live page loaded');
  },

  /**
   * 生命周期函数--监听页面初次渲染完成
   */
  onReady() {
    console.log('Live page ready');
  },

  /**
   * 生命周期函数--监听页面显示
   */
  onShow() {
    console.log('Live page shown');
  },

  /**
   * 生命周期函数--监听页面隐藏
   */
  onHide() {
    console.log('Live page hidden');
  },

  /**
   * 生命周期函数--监听页面卸载
   */
  onUnload() {
    console.log('Live page unloaded');
  },

  /**
   * 页面相关事件处理函数--监听用户下拉动作
   */
  onPullDownRefresh() {
    console.log('Live page pull down refresh');
    // 模拟刷新数据
    setTimeout(() => {
      wx.stopPullDownRefresh();
    }, 1000);
  },

  /**
   * 页面上拉触底事件的处理函数
   */
  onReachBottom() {
    console.log('Live page reach bottom');
  },

  /**
   * 用户点击右上角分享
   */
  onShareAppMessage() {
    return {
      title: '直播课堂',
      path: '/pages/live/live'
    };
  },

  // 进入直播
  onLiveTap() {
    console.log('Live tapped');
    // 跳转到直播页面
  },

  // 回放更多
  onReplayMoreTap() {
    console.log('Replay more tapped');
    // 跳转到回放列表页面
  },

  // 进入回放
  onReplayTap(e) {
    const replayId = e.currentTarget.dataset.id;
    console.log('Replay tapped:', replayId);
    // 跳转到回放详情页面
  }
})