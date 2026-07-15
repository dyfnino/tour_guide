const {
  getCart, updateCartItem, deleteCartItem, batchSelectCart
} = require('../../../../utils/api.js');

Page({
  data: {
    cart: [],
    selectedIds: [],
    totalPrice: 0
  },

  onShow() {
    this.loadCart();
  },

  // 从后端加载购物车
  async loadCart() {
    wx.showLoading({ title: '加载中...' });
    try {
      const res = await getCart();
      this._applyCart(res);
    } catch (err) {
      console.error('加载购物车失败:', err);
      wx.showToast({ title: '加载失败', icon: 'none' });
    } finally {
      wx.hideLoading();
    }
  },

  // 把后端返回的汇总数据渲染到页面
  _applyCart(res) {
    const items = (res && res.items) || [];
    this.setData({
      cart: items,
      selectedIds: items.filter(i => i.selected).map(i => i.id),
      totalPrice: (res && res.total_amount != null) ? Number(res.total_amount).toFixed(2) : '0.00'
    });
  },

  // 选择/取消选择单个商品
  async toggleSelect(e) {
    const itemId = e.currentTarget.dataset.id;
    const item = this.data.cart.find(i => i.id === itemId);
    if (!item) return;
    try {
      const res = await updateCartItem(itemId, { selected: !item.selected });
      this._applyCart(res);
    } catch (err) {
      wx.showToast({ title: '操作失败', icon: 'none' });
    }
  },

  // 全选/取消全选
  async toggleSelectAll() {
    const { cart, selectedIds } = this.data;
    const selectAll = selectedIds.length !== cart.length;
    try {
      const res = await batchSelectCart(selectAll);
      this._applyCart(res);
    } catch (err) {
      wx.showToast({ title: '操作失败', icon: 'none' });
    }
  },

  // 减少数量
  async decreaseQuantity(e) {
    const itemId = e.currentTarget.dataset.id;
    const item = this.data.cart.find(i => i.id === itemId);
    if (!item || item.quantity <= 1) return;
    try {
      const res = await updateCartItem(itemId, { quantity: item.quantity - 1 });
      this._applyCart(res);
    } catch (err) {
      wx.showToast({ title: '操作失败', icon: 'none' });
    }
  },

  // 增加数量
  async increaseQuantity(e) {
    const itemId = e.currentTarget.dataset.id;
    const item = this.data.cart.find(i => i.id === itemId);
    if (!item) return;
    try {
      const res = await updateCartItem(itemId, { quantity: item.quantity + 1 });
      this._applyCart(res);
    } catch (err) {
      wx.showToast({ title: '操作失败', icon: 'none' });
    }
  },

  // 删除商品
  deleteItem(e) {
    const itemId = e.currentTarget.dataset.id;
    wx.showModal({
      title: '删除商品',
      content: '确定从购物车移除该商品吗？',
      success: async (r) => {
        if (!r.confirm) return;
        try {
          const res = await deleteCartItem(itemId);
          this._applyCart(res);
        } catch (err) {
          wx.showToast({ title: '删除失败', icon: 'none' });
        }
      }
    });
  },

  // 去结算
  goCheckout() {
    const { cart, selectedIds } = this.data;
    const selectedItems = cart.filter(item => selectedIds.includes(item.id));

    if (selectedItems.length === 0) {
      wx.showToast({ title: '请选择商品', icon: 'none' });
      return;
    }

    // 传给确认页：使用商品 id 与数量（confirm 下单需要 product_id）
    const checkoutItems = selectedItems.map(i => ({
      id: i.product_id,
      product_id: i.product_id,
      name: i.name,
      image: i.image,
      price: i.price,
      quantity: i.quantity
    }));
    wx.setStorageSync('checkoutItems', checkoutItems);

    wx.navigateTo({
      url: '/pages/specialty/confirm/confirm'
  });
  }
});