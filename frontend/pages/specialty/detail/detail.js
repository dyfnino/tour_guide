const { getProduct, createProductOrder, prepayOrder, mockPaidOrder, pollOrderPaid } = require('../../../../utils/api.js');

Page({
  data: {
    product: null,
    quantity: 1,
    loading: true
  },

  onLoad(options) {
    const productId = options.id;
    if (productId) {
      this.loadProduct(productId);
    }
  },

  async loadProduct(productId) {
    try {
      const product = await getProduct(productId);
      this.setData({
        product: {
          id: product.id,
          name: product.name,
          image: product.image,
          price: product.price,
          category: product.category,
          description: product.description || '暂无描述',
          stock: product.stock || 999
        },
        loading: false
      });
    } catch (err) {
      console.error('加载商品失败:', err);
      wx.showToast({ title: '加载失败', icon: 'none' });
      this.setData({ loading: false });
    }
  },

  // 减少数量
  decreaseQuantity() {
    if (this.data.quantity > 1) {
      this.setData({ quantity: this.data.quantity - 1 });
    }
  },

  // 增加数量
  increaseQuantity() {
    const max = this.data.product?.stock || 999;
    if (this.data.quantity < max) {
      this.setData({ quantity: this.data.quantity + 1 });
    }
  },

  // 输入数量
  onQuantityInput(e) {
    let value = parseInt(e.detail.value) || 1;
    const max = this.data.product?.stock || 999;
    if (value < 1) value = 1;
    if (value > max) value = max;
    this.setData({ quantity: value });
  },

  // 立即购买
  async buyNow() {
    const { product, quantity } = this.data;
    if (!product) return;

    // 保存商品信息到临时存储
    const checkoutItems = [{
      id: product.id,
      name: product.name,
      image: product.image,
      price: product.price,
      quantity: quantity
    }];
    wx.setStorageSync('checkoutItems', checkoutItems);

    // 跳转到订单确认页
    wx.navigateTo({
      url: `/pages/specialty/confirm/confirm?product_id=${product.id}&quantity=${quantity}`
    });
  },

  // 加入购物车
  addToCart() {
    const { product, quantity } = this.data;
    if (!product) return;

    // 获取购物车
    let cart = wx.getStorageSync('cart') || [];
    
    // 检查是否已在购物车
    const existIndex = cart.findIndex(item => item.id === product.id);
    if (existIndex >= 0) {
      cart[existIndex].quantity += quantity;
    } else {
      cart.push({
        id: product.id,
        name: product.name,
        image: product.image,
        price: product.price,
        quantity: quantity
      });
    }

    wx.setStorageSync('cart', cart);
    wx.showToast({ title: '已加入购物车', icon: 'success' });
  },

  // 分享
  onShareAppMessage() {
    const { product } = this.data;
    return {
      title: product?.name || '特产详情',
      path: `/pages/specialty/detail/detail?id=${product?.id}`
    };
  }
});