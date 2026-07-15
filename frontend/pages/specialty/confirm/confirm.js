const { createProductOrder, prepayOrder, mockPaidOrder, pollOrderPaid, listAddresses, clearCart } = require('../../../../utils/api.js');

Page({
  data: {
    items: [],
    totalPrice: 0,
    address: null,
    submitting: false
  },

  onLoad(options) {
    // 从详情页直接购买
    if (options.product_id) {
      this.loadDirectBuy(options.product_id, parseInt(options.quantity) || 1);
    } else {
      // 从购物车结算
      this.loadFromCart();
    }
  },

  onShow() {
    // 从地址管理页返回时回填选中的地址
    const picked = wx.getStorageSync('selectedAddress');
    if (picked) {
      this.setData({ address: picked });
      wx.removeStorageSync('selectedAddress');
    } else if (!this.data.address) {
      this.loadDefaultAddress();
    }
  },

  loadDirectBuy(productId, quantity) {
    // 从商品详情跳转时，需要获取商品信息
    const checkoutItems = wx.getStorageSync('checkoutItems') || [];
    if (checkoutItems.length > 0) {
      this.initData(checkoutItems);
    } else {
      // 如果没有缓存，返回上一页
      wx.showToast({ title: '商品信息丢失', icon: 'none' });
      setTimeout(() => wx.navigateBack(), 1500);
    }
  },

  loadFromCart() {
    const checkoutItems = wx.getStorageSync('checkoutItems') || [];
    if (checkoutItems.length === 0) {
      wx.showToast({ title: '没有选中商品', icon: 'none' });
      setTimeout(() => wx.navigateBack(), 1500);
      return;
    }
    this.initData(checkoutItems);
  },

  initData(items) {
    const total = items.reduce((sum, item) => sum + item.price * item.quantity, 0);
    this.setData({
      items: items,
      totalPrice: total.toFixed(2)
    });

    // 加载默认收货地址
    this.loadDefaultAddress();
  },

  // 从后端加载默认收货地址
  async loadDefaultAddress() {
    try {
      const list = await listAddresses();
      if (list && list.length > 0) {
        const def = list.find(a => a.is_default) || list[0];
        this.setData({
          address: {
            id: def.id,
            name: def.name,
            phone: def.phone,
            address: `${def.province || ''}${def.city || ''}${def.district || ''}${def.detail || ''}`
          }
        });
      }
    } catch (err) {
      // 未登录或无地址时忽略
    }
  },

  // 选择收货地址：跳转到地址管理页（选择模式）
  chooseAddress() {
    wx.navigateTo({
      url: '/pages/profile/address/list/list?mode=select'
    });
  },

  // 提交订单
  async submitOrder() {
    const { address, items, submitting } = this.data;
    
    if (submitting) return;
    
    // 验证收货地址
    if (!address || !address.name || !address.phone || !address.address) {
      wx.showToast({ title: '请填写收货地址', icon: 'none' });
      return;
    }

    this.setData({ submitting: true });

    try {
      wx.showLoading({ title: '提交订单...' });

      // 构造订单数据
      const orderData = {
        items: items.map(item => ({
          product_id: item.id,
          quantity: item.quantity
        })),
        name: address.name,
        phone: address.phone,
        address: address.address
      };

      // 创建订单
      const order = await createProductOrder(orderData);
      wx.hideLoading();

      // 发起支付
      await this.doPayment(order.id);

    } catch (err) {
      wx.hideLoading();
      console.error('提交订单失败:', err);
      const msg = err?.data?.detail || '提交订单失败';
      wx.showToast({ title: msg, icon: 'none' });
      this.setData({ submitting: false });
    }
  },

  // 发起支付
  async doPayment(orderId) {
    try {
      wx.showLoading({ title: '调起支付...' });
      const prepay = await prepayOrder(orderId);
      wx.hideLoading();

      const params = prepay.pay_params || {};

      // Mock 模式：直接走模拟支付，避免用假 prepay_id 调起 wx.requestPayment
      // 导致微信报"缺少参数：total_fee"
      if (prepay.mock) {
        wx.showLoading({ title: '支付中...' });
        await mockPaidOrder(orderId);
      } else {
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
      }

      wx.hideLoading();
      wx.showToast({ title: '支付成功', icon: 'success' });

      // 清空购物车中已结算的商品
      try {
        await clearCart(true);
      } catch (e) {
        // 直接购买（非购物车）时后端无勾选项，忽略
      }
      wx.removeStorageSync('checkoutItems');

      // 轮询订单状态
      const fresh = await pollOrderPaid(orderId, 3, 1500);

      // 跳转到订单详情
      setTimeout(() => {
        wx.redirectTo({
          url: `/pages/profile/orders/detail/detail?id=${orderId}`
        });
      }, 1000);

    } catch (err) {
      wx.hideLoading();
      console.error('支付失败:', err);
      const msg = (err && err.errMsg && err.errMsg.indexOf('cancel') >= 0)
        ? '支付已取消' : '支付失败';
      wx.showToast({ title: msg, icon: 'none' });
      this.setData({ submitting: false });
      
      // 跳转到订单详情（未支付状态）
      setTimeout(() => {
        wx.redirectTo({
          url: `/pages/profile/orders/detail/detail?id=${orderId}`
        });
      }, 1500);
    }
  }
});