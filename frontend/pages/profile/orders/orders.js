const { request, prepayOrder, mockPaidOrder, pollOrderPaid, getCourse } = require('../../../utils/api.js');

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
      const formattedOrders = await Promise.all((res || []).map(async order => {
        const isCourse = (order.order_type || 'product') === 'course';
        const products = await Promise.all((order.items || []).map(async item => {
          let name = isCourse ? '课程' : '商品';
          let image = 'https://picsum.photos/300/300?random=' + item.product_id;
          if (isCourse) {
            try {
              const c = await getCourse(item.product_id);
              if (c) {
                name = c.name || c.title || name;
                if (c.image || c.cover_image) image = c.image || c.cover_image;
              }
            } catch (e) { /* ignore: 用占位图 */ }
          }
          return {
            productId: item.product_id,
            name,
            image,
            price: '¥' + item.price,
            quantity: item.quantity
          };
        }));
        // 取首个课程作为"开始学习"跳转目标
        const firstCourseId = isCourse && products.length > 0 ? products[0].productId : null;
        return {
          id: order.id,
          orderNo: order.order_no,
          status: order.status,
          totalPrice: '¥' + order.total_amount,
          products: products,
          createTime: order.created_at,
          isCourse: isCourse,
          firstCourseId: firstCourseId
        };
      }));
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
      wx.showLoading({ title: '调起支付...' });
      const prepay = await prepayOrder(orderId);
      wx.hideLoading();
      const params = prepay.pay_params || {};

      // 真实调起微信支付
      await new Promise((resolve, reject) => {
        wx.requestPayment({
          timeStamp: params.timeStamp,
          nonceStr: params.nonceStr,
          package: params.package,
          signType: params.signType || 'RSA',
          paySign: params.paySign,
          success: resolve,
          fail: reject
        });
      });

      // Mock 模式下 wx.requestPayment 会失败，这里捕获后由下方 catch 走 mock-paid
      // 真实支付成功：等待回调把订单置 paid，刷新一下列表
      wx.showToast({ title: '支付成功', icon: 'success' });
      this.loadOrders();
    } catch (err) {
      wx.hideLoading && wx.hideLoading();
      // Mock 联调：识别 mock 标记或本地无法支付时，转走模拟接口
      try {
        const isMock = err && (err.mock || (err.errMsg && err.errMsg.indexOf('fail') >= 0));
        if (isMock) {
          await mockPaidOrder(orderId);
          wx.showToast({ title: '已模拟支付', icon: 'success' });
          this.loadOrders();
          return;
        }
      } catch (e2) { /* ignore */ }
      console.error('支付失败:', err);
      wx.showToast({ title: '支付已取消', icon: 'none' });
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

  goToStudy(e) {
    const courseId = e && e.currentTarget && e.currentTarget.dataset && e.currentTarget.dataset.courseId;
    if (courseId) {
      wx.navigateTo({ url: `/pages/guide-cert/course/course?id=${courseId}&enrolled=1` });
    } else {
      wx.navigateTo({ url: '/pages/profile/my-courses/my-courses' });
    }
  }
});