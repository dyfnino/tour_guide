const { createProductOrder, prepayOrder, mockPaidOrder, pollOrderPaid } = require('../../../../utils/api.js');

Page({
  data: {
    items: [],
    totalPrice: 0,
    address: {
      name: '',
      phone: '',
      address: ''
    },
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

    // 加载收货地址
    const savedAddress = wx.getStorageSync('defaultAddress');
    if (savedAddress) {
      this.setData({ address: savedAddress });
    }
  },

  // 选择收货地址
  chooseAddress() {
    wx.chooseAddress({
      success: (res) => {
        const address = {
          name: res.userName,
          phone: res.telNumber,
          address: `${res.provinceName}${res.cityName}${res.countyName}${res.detailInfo}`
        };
        this.setData({ address });
        wx.setStorageSync('defaultAddress', address);
      },
      fail: () => {
        wx.showToast({ title: '选择地址失败', icon: 'none' });
      }
    });
  },

  // 提交订单
  async submitOrder() {
    const { address, items, submitting } = this.data;
    
    if (submitting) return;
    
    // 验证收货地址
    if (!address.name || !address.phone || !address.address) {
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
      const checkoutIds = this.data.items.map(i => i.id);
      let cart = wx.getStorageSync('cart') || [];
      cart = cart.filter(item => !checkoutIds.includes(item.id));
      wx.setStorageSync('cart', cart);
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