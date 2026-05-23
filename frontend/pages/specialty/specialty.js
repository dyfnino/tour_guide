const { listProducts } = require('../../utils/api.js');

Page({
  data: {
    selectedCategory: 'all',
    allProducts: [],
    productList: []
  },

  onLoad() {
    this.loadProducts();
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
    console.log('Product tapped:', productId);
  },

  // 添加到购物车
  onAddToCart(e) {
    e.stopPropagation();
    const productId = e.currentTarget.dataset.id;
    console.log('Add to cart:', productId);
  }
});