const { request, prepayOrder, mockPaidOrder, getOrder, confirmReceipt, pollOrderPaid, getCourse } = require('../../../../utils/api.js');

Page({
  data: {
    order: {
      id: '',
      orderNo: '',
      status: '',
      totalPrice: '',
      createTime: '',
      paymentMethod: '',
      recipient: '',
      address: '',
      phone: '',
      shippingFee: '',
      products: [],
      orderType: 'product',
      isCourse: false,
      firstCourseId: null
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
      const orderType = orderData.order_type || 'product';
      const isCourse = orderType === 'course';

      const products = await Promise.all((orderData.items || []).map(async item => {
        let name = isCourse ? '课程' : '商品';
        let image = 'https://picsum.photos/300/300?random=' + item.product_id;
        if (isCourse) {
          try {
            const c = await getCourse(item.product_id);
            if (c) {
              name = c.name || c.title || name;
              if (c.image || c.cover_image) image = c.image || c.cover_image;
            }
          } catch (e) { /* ignore */ }
        }
        return {
          productId: item.product_id,
          name,
          image,
          price: '¥' + item.price,
          quantity: item.quantity
        };
      }));

      const firstCourseId = isCourse && products.length > 0 ? products[0].productId : null;

      const order = {
        id: orderData.id,
        orderNo: orderData.order_no,
        status: orderData.status,
        totalPrice: '¥' + orderData.total_amount,
        createTime: orderData.created_at,
        paymentMethod: orderData.status === 'unpaid' ? '未支付' : '微信支付',
        recipient: orderData.name || '',
        address: orderData.address || '',
        phone: orderData.phone || '',
        shippingFee: isCourse ? '' : '¥0',
        products: products,
        orderType: orderType,
        isCourse: isCourse,
        firstCourseId: firstCourseId
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
      wx.showLoading({ title: '调起支付...' });
      const prepay = await prepayOrder(orderId);
      wx.hideLoading();
      const params = prepay.pay_params || {};

      try {
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
      } catch (e) {
        // Mock 模式下 wx.requestPayment 必失败：自动走模拟支付
        if (prepay.mock) {
          await mockPaidOrder(orderId);
        } else {
          throw e;
        }
      }

      wx.showToast({ title: '支付成功', icon: 'success' });
      // 轮询订单状态：真实支付下回调可能稍有延时
      const fresh = await pollOrderPaid(orderId, 3, 1500);
      if (fresh) {
        this.setData({
          'order.status': fresh.status,
          'order.paymentMethod': fresh.status === 'unpaid' ? '未支付' : '微信支付'
        });
      }
    } catch (err) {
      wx.hideLoading && wx.hideLoading();
      console.error('支付失败:', err);
      const msg = (err && err.errMsg && err.errMsg.indexOf('cancel') >= 0)
        ? '支付已取消' : '支付失败';
      wx.showToast({ title: msg, icon: 'none' });
    }
  },

  // 确认收货（商品订单）
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

  // 去学习（课程订单支付后）
  goToStudy() {
    const courseId = this.data.order.firstCourseId;
    if (courseId) {
      wx.navigateTo({ url: `/pages/guide-cert/course/course?id=${courseId}&enrolled=1` });
    } else {
      wx.navigateTo({ url: '/pages/profile/my-courses/my-courses' });
    }
  },

  // 联系客服
  contactService() {
    wx.showToast({ title: '客服功能开发中', icon: 'none' });
  }
});