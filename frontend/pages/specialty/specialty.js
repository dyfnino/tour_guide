const { listProducts } = require('../../utils/api.js');

Page({
  data: {
    selectedCategory: 'all',
    allProducts: [],
    productList: [],
    cartCount: 0
  },

  onLoad() {
    this.loadProducts();
    this.updateCartCount();
  },

  onShow() {
    this.updateCartCount();
  },

  updateCartCount() {
    const cart = wx.getStorageSync('cart') || [];
    const count = cart.reduce((sum, item) => sum + item.quantity, 0);
    this.setData({ cartCount: count });
  },

  async loadProducts() {
    try {
      const res = await listProducts();
      const products = (res || []).map(p => ({
        id: p.id,
        name: p.name,
        image: p.image,
        price: '¥' + p.price,
        category: p.category
      }));
      this.setData({ allProducts: products, productList: products });
    } catch (err) {
      console.error('商品加载失败:', err);
    }
  },

  onPullDownRefresh() {
    this.loadProducts().then(() => wx.stopPullDownRefresh());
  },

  onShareAppMessage() {
    return { title: '特产商城', path: '/pages/specialty/specialty' };
  },

  // 选择分类
  selectCategory(e) {
    const category = e.currentTarget.dataset.category;
    this.setData({ selectedCategory: category });
    this.filterProducts(category);
  },

  // 根据分类筛选产品
  filterProducts(category) {
    const list = category === 'all'
      ? this.data.allProducts
      : this.data.allProducts.filter(p => p.category === category);
    this.setData({ productList: list });
  },

  // 产品点击事件
  onProductTap(e) {
    const productId = e.currentTarget.dataset.id;
    wx.navigateTo({
      url: `/pages/specialty/detail/detail?id=${productId}`
    });
  },

  // 添加到购物车
  onAddToCart(e) {
    e.stopPropagation();
    const productId = e.currentTarget.dataset.id;
    const product = this.data.allProducts.find(p => p.id === productId);
    
    if (!product) return;
    
    // 获取购物车
    let cart = wx.getStorageSync('cart') || [];
    
    // 检查是否已在购物车
    const existIndex = cart.findIndex(item => item.id === productId);
    if (existIndex >= 0) {
      cart[existIndex].quantity += 1;
    } else {
      cart.push({
        id: product.id,
        name: product.name,
        image: product.image,
        price: parseFloat(product.price.replace('¥', '')),
        quantity: 1
      });
    }

    wx.setStorageSync('cart', cart);
    wx.showToast({ title: '已加入购物车', icon: 'success' });
  },

  // 查看购物车
  goToCart() {
    wx.navigateTo({
      url: '/pages/specialty/cart/cart'
    });
  }
});