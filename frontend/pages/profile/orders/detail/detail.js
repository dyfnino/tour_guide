Page({
  /**
   * 页面的初始数据
   */
  data: {
    order: {
      id: '',
      status: '',
      totalPrice: '',
      createTime: '',
      paymentMethod: '',
      recipient: '',
      address: '',
      phone: '',
      shippingFee: '',
      products: []
    }
  },

  /**
   * 生命周期函数--监听页面加载
   */
  onLoad(options) {
    console.log('Order detail page loaded', options);
    const orderId = options.id;
    if (orderId) {
      this.getOrderDetail(orderId);
    }
  },

  /**
   * 生命周期函数--监听页面初次渲染完成
   */
  onReady() {
    console.log('Order detail page ready');
  },

  /**
   * 生命周期函数--监听页面显示
   */
  onShow() {
    console.log('Order detail page shown');
  },

  /**
   * 生命周期函数--监听页面隐藏
   */
  onHide() {
    console.log('Order detail page hidden');
  },

  /**
   * 生命周期函数--监听页面卸载
   */
  onUnload() {
    console.log('Order detail page unloaded');
  },

  /**
   * 页面相关事件处理函数--监听用户下拉动作
   */
  onPullDownRefresh() {
    console.log('Order detail page pull down refresh');
    // 模拟刷新数据
    setTimeout(() => {
      wx.stopPullDownRefresh();
    }, 1000);
  },

  /**
   * 用户点击右上角分享
   */
  onShareAppMessage() {
    return {
      title: '订单详情',
      path: `/pages/profile/orders/detail/detail?id=${this.data.order.id}`
    };
  },

  // 获取订单详情
  getOrderDetail(orderId) {
    console.log('Getting order detail:', orderId);
    
    wx.showLoading({ title: '加载中...' });
    
    // 调用后端API获取订单详情
    wx.request({
      url: `http://localhost:8000/api/orders/${orderId}`,
      method: 'GET',
      success: (res) => {
        console.log('Get order detail success:', res.data);
        if (res.statusCode === 200) {
          const orderData = res.data;
          // 转换数据格式以适应前端显示
          const order = {
            id: orderData.id,
            orderNo: orderData.order_no,
            status: orderData.status,
            totalPrice: '¥' + orderData.total_amount,
            createTime: orderData.created_at,
            paymentMethod: '微信支付', // 实际项目中应该从订单数据获取
            recipient: orderData.name,
            address: orderData.address,
            phone: orderData.phone,
            shippingFee: '¥0', // 实际项目中应该从订单数据获取
            products: orderData.items.map(item => ({
              productId: item.product_id,
              name: '商品', // 实际项目中应该从商品详情获取
              image: 'https://picsum.photos/300/300?random=' + item.product_id,
              price: '¥' + item.price,
              quantity: item.quantity
            }))
          };
          
          this.setData({ order });
        }
      },
      fail: (err) => {
        console.error('Get order detail fail:', err);
        // 使用模拟数据作为 fallback
        this.useMockData(orderId);
      },
      complete: () => {
        wx.hideLoading();
      }
    });
  },

  // 使用模拟数据
  useMockData(orderId) {
    const mockOrder = {
      id: orderId,
      orderNo: orderId,
      status: 'unpaid',
      totalPrice: '¥467',
      createTime: '2026-02-01 10:30:00',
      paymentMethod: '微信支付',
      recipient: '张三',
      address: '陕西省西安市雁塔区大雁塔街道123号',
      phone: '13800138000',
      shippingFee: '¥0',
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
      ]
    };

    // 根据订单ID模拟不同状态的订单
    if (orderId === '202602010002') {
      mockOrder.status = 'paid';
      mockOrder.totalPrice = '¥89';
      mockOrder.products = [
        {
          productId: '2',
          name: '手工刺绣书签套装',
          image: 'https://picsum.photos/300/300?random=9',
          price: '¥89',
          quantity: 1
        }
      ];
    } else if (orderId === '202601310001') {
      mockOrder.status = 'completed';
      mockOrder.totalPrice = '¥198';
      mockOrder.products = [
        {
          productId: '4',
          name: '高山云雾茶礼盒装',
          image: 'https://picsum.photos/300/300?random=11',
          price: '¥198',
          quantity: 1
        }
      ];
    }

    this.setData({ order: mockOrder });
  },

  // 获取状态图标
  getStatusIcon(status) {
    const iconMap = {
      unpaid: '💳',
      paid: '📦',
      completed: '✅'
    };
    return iconMap[status] || '';
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

  // 去支付
  payOrder() {
    const orderId = this.data.order.id;
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
          // 更新订单状态
          this.setData({
            'order.status': 'paid'
          });
        }
      },
      fail: (err) => {
        console.error('Pay order fail:', err);
        wx.showToast({ title: '支付失败', icon: 'none' });
      }
    });
  },

  // 确认收货
  confirmReceipt() {
    const orderId = this.data.order.id;
    console.log('Confirm receipt:', orderId);
    
    wx.showModal({
      title: '确认收货',
      content: '确认收到商品吗？',
      success: (res) => {
        if (res.confirm) {
          // 调用后端API更新订单状态为已完成
          wx.request({
            url: `http://localhost:8000/api/orders/${orderId}`,
            method: 'PUT',
            data: { status: 'completed' },
            success: (res) => {
              console.log('Confirm receipt success:', res.data);
              if (res.statusCode === 200) {
                wx.showToast({ title: '确认收货成功', icon: 'success' });
                // 更新订单状态
                this.setData({
                  'order.status': 'completed'
                });
              }
            },
            fail: (err) => {
              console.error('Confirm receipt fail:', err);
              wx.showToast({ title: '确认收货失败', icon: 'none' });
            }
          });
        }
      }
    });
  },

  // 联系客服
  contactService() {
    console.log('Contact service');
    // 跳转到客服页面
    wx.showToast({
      title: '客服功能开发中',
      icon: 'none'
    });
  }
})