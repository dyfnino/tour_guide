Page({
  /**
   * 页面的初始数据
   */
  data: {
    selectedCategory: 'all',
    productList: [
      {
        id: 1,
        name: '地方特色腊肉礼盒',
        image: 'https://picsum.photos/300/300?random=8',
        price: '¥168',
        category: 'food'
      },
      {
        id: 2,
        name: '手工刺绣书签套装',
        image: 'https://picsum.photos/300/300?random=9',
        price: '¥89',
        category: 'cultural'
      },
      {
        id: 3,
        name: '传统工艺陶瓷茶具',
        image: 'https://picsum.photos/300/300?random=10',
        price: '¥299',
        category: 'craft'
      },
      {
        id: 4,
        name: '高山云雾茶礼盒装',
        image: 'https://picsum.photos/300/300?random=11',
        price: '¥198',
        category: 'local'
      }
    ]
  },

  /**
   * 生命周期函数--监听页面加载
   */
  onLoad(options) {
    console.log('Specialty page loaded');
  },

  /**
   * 生命周期函数--监听页面初次渲染完成
   */
  onReady() {
    console.log('Specialty page ready');
  },

  /**
   * 生命周期函数--监听页面显示
   */
  onShow() {
    console.log('Specialty page shown');
  },

  /**
   * 生命周期函数--监听页面隐藏
   */
  onHide() {
    console.log('Specialty page hidden');
  },

  /**
   * 生命周期函数--监听页面卸载
   */
  onUnload() {
    console.log('Specialty page unloaded');
  },

  /**
   * 页面相关事件处理函数--监听用户下拉动作
   */
  onPullDownRefresh() {
    console.log('Specialty page pull down refresh');
    // 模拟刷新数据
    setTimeout(() => {
      wx.stopPullDownRefresh();
    }, 1000);
  },

  /**
   * 页面上拉触底事件的处理函数
   */
  onReachBottom() {
    console.log('Specialty page reach bottom');
  },

  /**
   * 用户点击右上角分享
   */
  onShareAppMessage() {
    return {
      title: '特产商城',
      path: '/pages/specialty/specialty'
    };
  },

  // 选择分类
  selectCategory(e) {
    const category = e.currentTarget.dataset.category;
    this.setData({
      selectedCategory: category
    });
    // 根据分类筛选产品
    this.filterProducts(category);
  },

  // 根据分类筛选产品
  filterProducts(category) {
    console.log('Filter products by category:', category);
    // 实现产品筛选逻辑
  },

  // 产品点击事件
  onProductTap(e) {
    const productId = e.currentTarget.dataset.id;
    console.log('Product tapped:', productId);
    // 跳转到产品详情页面
  },

  // 添加到购物车
  onAddToCart(e) {
    e.stopPropagation(); // 阻止事件冒泡
    const productId = e.currentTarget.dataset.id;
    console.log('Add to cart:', productId);
    // 实现添加到购物车逻辑
  }
})