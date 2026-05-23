const { request } = require('../../../utils/api.js');

Page({
  data: {
    currentStatus: 'all',
    orders: [],
    loading: false
  },

  onLoad() {},

  onShow() {
    this.loadOrders();
  },

  onPullDownRefresh() {
    this.loadOrders(() => {
      wx.stopPullDownRefresh();
    });
  },

  onShareAppMessage() {
    return { title: '我的订单', path: '/pages/profile/orders/orders' };
  },

  async loadOrders(callback) {
    const { currentStatus } = this.data;
    let path = '/orders';
    if (currentStatus !== 'all') {
      path += `?status=${currentStatus}`;
    }

    this.setData({ loading: true });
    try {
      const res = await request(path);
      const formattedOrders = (res || []).map(order => {
        const isCourse = (order.order_type || 'product') === 'course';
        const products = (order.items || []).map(item => ({
          productId: item.product_id,
          name: isCourse ? '课程' : '商品',
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
          createTime: order.created_at,
          isCourse: isCourse
        };
      });
      this.setData({ orders: formattedOrders });
    } catch (err) {
      console.error('订单加载失败:', err);
      wx.showToast({ title: '加载失败', icon: 'none' });
    } finally {
      this.setData({ loading: false });
      if (callback) callback();
    }
  },

  switchStatus(e) {
    const status = e.currentTarget.dataset.status;
    this.setData({ currentStatus: status });
    this.loadOrders();
  },

  viewOrderDetail(e) {
    const orderId = e.currentTarget.dataset.id;
    wx.navigateTo({ url: `/pages/profile/orders/detail/detail?id=${orderId}` });
  },

  async payOrder(e) {
    const orderId = e.currentTarget.dataset.id;
    try {
      await request(`/orders/${orderId}`, { method: 'PUT', data: { status: 'paid' } });
      wx.showToast({ title: '支付成功', icon: 'success' });
      this.loadOrders();
    } catch (err) {
      console.error('支付失败:', err);
      wx.showToast({ title: '支付失败', icon: 'none' });
    }
  },

  async confirmReceipt(e) {
    const orderId = e.currentTarget.dataset.id;
    try {
      await request(`/orders/${orderId}`, { method: 'PUT', data: { status: 'completed' } });
      wx.showToast({ title: '确认收货成功', icon: 'success' });
      this.loadOrders();
    } catch (err) {
      console.error('确认收货失败:', err);
      wx.showToast({ title: '确认收货失败', icon: 'none' });
    }
  },

  goToStudy() {
    wx.navigateTo({ url: '/pages/profile/my-courses/my-courses' });
  }
});