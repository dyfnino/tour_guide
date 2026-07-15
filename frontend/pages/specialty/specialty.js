const { listProducts, getCart, addToCart } = require('../../utils/api.js');

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

  async updateCartCount() {
    try {
      const res = await getCart();
      const count = res && res.total_quantity ? res.total_quantity : 0;
      this.setData({ cartCount: count });
    } catch (err) {
      this.setData({ cartCount: 0 });
    }
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
  async onAddToCart(e) {
    e.stopPropagation();
    const productId = e.currentTarget.dataset.id;
    const product = this.data.allProducts.find(p => p.id === productId);

    if (!product) return;

    try {
      const summary = await addToCart(productId, 1);
      const count = summary && summary.total_quantity ? summary.total_quantity : this.data.cartCount + 1;
      this.setData({ cartCount: count });
      wx.showToast({ title: '已加入购物车', icon: 'success' });
    } catch (err) {
      if (err && err.statusCode === 401) {
        wx.showToast({ title: '请先登录', icon: 'none' });
        return;
      }
      wx.showToast({ title: '加入失败', icon: 'none' });
    }
  },

  // 查看购物车
  goToCart() {
    wx.navigateTo({
      url: '/pages/specialty/cart/cart'
    });
  }
});