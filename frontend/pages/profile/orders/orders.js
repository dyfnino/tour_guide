Page({
  /**
   * 页面的初始数据
   */
  data: {
    currentStatus: 'all',
    orders: [],
    loading: false
  },

  /**
   * 生命周期函数--监听页面加载
   */
  onLoad(options) {
    console.log('Orders page loaded');
  },

  /**
   * 生命周期函数--监听页面初次渲染完成
   */
  onReady() {
    console.log('Orders page ready');
  },

  /**
   * 生命周期函数--监听页面显示
   */
  onShow() {
    console.log('Orders page shown');
    this.loadOrders();
  },

  /**
   * 生命周期函数--监听页面隐藏
   */
  onHide() {
    console.log('Orders page hidden');
  },

  /**
   * 生命周期函数--监听页面卸载
   */
  onUnload() {
    console.log('Orders page unloaded');
  },

  /**
   * 页面相关事件处理函数--监听用户下拉动作
   */
  onPullDownRefresh() {
    console.log('Orders page pull down refresh');
    this.loadOrders(() => {
      wx.stopPullDownRefresh();
    });
  },

  /**
   * 页面上拉触底事件的处理函数
   */
  onReachBottom() {
    console.log('Orders page reach bottom');
  },

  /**
   * 用户点击右上角分享
   */
  onShareAppMessage() {
    return {
      title: '我的订单',
      path: '/pages/profile/orders/orders'
    };
  },

  // 加载订单数据
  loadOrders(callback) {
    const { currentStatus } = this.data;
    let statusParam = '';
    
    if (currentStatus !== 'all') {
      statusParam = `?status=${currentStatus}`;
    }
    
    this.setData({ loading: true });
    
    wx.request({
      url: `http://localhost:8000/api/orders${statusParam}`,
      method: 'GET',
      success: (res) => {
        console.log('Load orders success:', res.data);
        if (res.statusCode === 200) {
          // 转换订单数据格式以适应前端显示
          const formattedOrders = res.data.map(order => {
            // 转换items为products格式
            const products = order.items.map(item => ({
              productId: item.product_id,
              name: '商品', // 实际项目中应该从商品详情获取
              image: 'https://picsum.photos/300/300?random=' + item.product_id,
              price: '¥' + item.price,
              quantity: item.quantity
            }));
            
            return {
              id: order.id,
              orderNo: order.order_no,
              status: order.status,
              totalPrice: '¥' + order.total_amount,
              products: products,
              createTime: order.created_at
            };
          });
          
          this.setData({ orders: formattedOrders });
        }
      },
      fail: (err) => {
        console.error('Load orders fail:', err);
        // 使用模拟数据作为 fallback
        this.useMockData();
      },
      complete: () => {
        this.setData({ loading: false });
        if (callback) callback();
      }
    });
  },

  // 使用模拟数据
  useMockData() {
    const mockOrders = [
      {
        id: '202602010001',
        orderNo: '202602010001',
        status: 'unpaid',
        totalPrice: '¥467',
        products: [
          {
            productId: '1',
            name: '地方特色腊肉礼盒',
            image: 'https://picsum.photos/300/300?random=8',
            price: '¥168',
            quantity: 1
          },
          {
            productId: '3',
            name: '传统工艺陶瓷茶具',
            image: 'https://picsum.photos/300/300?random=10',
            price: '¥299',
            quantity: 1
          }
        ],
        createTime: '2026-02-01 10:30:00'
      },
      {
        id: '202602010002',
        orderNo: '202602010002',
        status: 'paid',
        totalPrice: '¥89',
        products: [
          {
            productId: '2',
            name: '手工刺绣书签套装',
            image: 'https://picsum.photos/300/300?random=9',
            price: '¥89',
            quantity: 1
          }
        ],
        createTime: '2026-02-01 09:15:00'
      },
      {
        id: '202601310001',
        orderNo: '202601310001',
        status: 'completed',
        totalPrice: '¥198',
        products: [
          {
            productId: '4',
            name: '高山云雾茶礼盒装',
            image: 'https://picsum.photos/300/300?random=11',
            price: '¥198',
            quantity: 1
          }
        ],
        createTime: '2026-01-31 16:45:00'
      }
    ];
    
    this.setData({ orders: mockOrders });
  },

  // 切换订单状态
  switchStatus(e) {
    const status = e.currentTarget.dataset.status;
    this.setData({
      currentStatus: status
    });
    // 重新加载对应状态的订单
    this.loadOrders();
  },

  // 获取状态文本
  getStatusText(status) {
    const statusMap = {
      unpaid: '未支付',
      paid: '已支付',
      completed: '已完成'
    };
    return statusMap[status] || '';
  },

  // 获取订单商品总数
  getTotalProducts(products) {
    return products.reduce((total, product) => total + product.quantity, 0);
  },

  // 查看订单详情
  viewOrderDetail(e) {
    const orderId = e.currentTarget.dataset.id;
    console.log('View order detail:', orderId);
    // 跳转到订单详情页面
    wx.navigateTo({
      url: `/pages/profile/orders/detail/detail?id=${orderId}`
    });
  },

  // 去支付
  payOrder(e) {
    e.stopPropagation();
    const orderId = e.currentTarget.dataset.id;
    console.log('Pay order:', orderId);
    
    // 调用后端API更新订单状态为已支付
    wx.request({
      url: `http://localhost:8000/api/orders/${orderId}`,
      method: 'PUT',
      data: { status: 'paid' },
      success: (res) => {
        console.log('Pay order success:', res.data);
        if (res.statusCode === 200) {
          wx.showToast({ title: '支付成功', icon: 'success' });
          // 重新加载订单数据
          this.loadOrders();
        }
      },
      fail: (err) => {
        console.error('Pay order fail:', err);
        wx.showToast({ title: '支付失败', icon: 'none' });
      }
    });
  },

  // 确认收货
  confirmReceipt(e) {
    e.stopPropagation();
    const orderId = e.currentTarget.dataset.id;
    console.log('Confirm receipt:', orderId);
    
    // 调用后端API更新订单状态为已完成
    wx.request({
      url: `http://localhost:8000/api/orders/${orderId}`,
      method: 'PUT',
      data: { status: 'completed' },
      success: (res) => {
        console.log('Confirm receipt success:', res.data);
        if (res.statusCode === 200) {
          wx.showToast({ title: '确认收货成功', icon: 'success' });
          // 重新加载订单数据
          this.loadOrders();
        }
      },
      fail: (err) => {
        console.error('Confirm receipt fail:', err);
        wx.showToast({ title: '确认收货失败', icon: 'none' });
      }
    });
  }
})