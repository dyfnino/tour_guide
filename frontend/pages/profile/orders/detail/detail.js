const { request } = require('../../../../utils/api.js');

Page({
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

  onLoad(options) {
    const orderId = options.id;
    if (orderId) {
      this.getOrderDetail(orderId);
    }
  },

  async getOrderDetail(orderId) {
    wx.showLoading({ title: '加载中...' });
    try {
      const orderData = await request(`/orders/${orderId}`);
      const order = {
        id: orderData.id,
        orderNo: orderData.order_no,
        status: orderData.status,
        totalPrice: '¥' + orderData.total_amount,
        createTime: orderData.created_at,
        paymentMethod: '微信支付',
        recipient: orderData.name,
        address: orderData.address,
        phone: orderData.phone,
        shippingFee: '¥0',
        products: (orderData.items || []).map(item => ({
          productId: item.product_id,
          name: '商品',
          image: 'https://picsum.photos/300/300?random=' + item.product_id,
          price: '¥' + item.price,
          quantity: item.quantity
        }))
      };
      this.setData({ order });
    } catch (err) {
      console.error('订单详情加载失败:', err);
      wx.showToast({ title: '加载失败', icon: 'none' });
    } finally {
      wx.hideLoading();
    }
  },

  onShareAppMessage() {
    return {
      title: '订单详情',
      path: `/pages/profile/orders/detail/detail?id=${this.data.order.id}`
    };
  },

  // 去支付
  async payOrder() {
    const orderId = this.data.order.id;
    try {
      await request(`/orders/${orderId}`, { method: 'PUT', data: { status: 'paid' } });
      wx.showToast({ title: '支付成功', icon: 'success' });
      this.setData({ 'order.status': 'paid' });
    } catch (err) {
      console.error('支付失败:', err);
      wx.showToast({ title: '支付失败', icon: 'none' });
    }
  },

  // 确认收货
  confirmReceipt() {
    const orderId = this.data.order.id;
    wx.showModal({
      title: '确认收货',
      content: '确认收到商品吗？',
      success: async (res) => {
        if (res.confirm) {
          try {
            await request(`/orders/${orderId}`, { method: 'PUT', data: { status: 'completed' } });
            wx.showToast({ title: '确认收货成功', icon: 'success' });
            this.setData({ 'order.status': 'completed' });
          } catch (err) {
            console.error('确认收货失败:', err);
            wx.showToast({ title: '确认收货失败', icon: 'none' });
          }
        }
      }
    });
  },

  // 联系客服
  contactService() {
    wx.showToast({ title: '客服功能开发中', icon: 'none' });
  }
});