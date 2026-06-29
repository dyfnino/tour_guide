Page({
  data: {
    cart: [],
    selectedIds: [],
    totalPrice: 0
  },

  onLoad() {
    this.loadCart();
  },

  onShow() {
    this.loadCart();
  },

  loadCart() {
    const cart = wx.getStorageSync('cart') || [];
    this.setData({ 
      cart: cart,
      selectedIds: cart.map(item => item.id)
    });
    this.calculateTotal();
  },

  // 选择/取消选择商品
  toggleSelect(e) {
    const productId = e.currentTarget.dataset.id;
    let selectedIds = [...this.data.selectedIds];
    const index = selectedIds.indexOf(productId);
    
    if (index >= 0) {
      selectedIds.splice(index, 1);
    } else {
      selectedIds.push(productId);
    }
    
    this.setData({ selectedIds });
    this.calculateTotal();
  },

  // 全选/取消全选
  toggleSelectAll() {
    const { cart, selectedIds } = this.data;
    if (selectedIds.length === cart.length) {
      this.setData({ selectedIds: [] });
    } else {
      this.setData({ selectedIds: cart.map(item => item.id) });
    }
    this.calculateTotal();
  },

  // 减少数量
  decreaseQuantity(e) {
    const productId = e.currentTarget.dataset.id;
    const cart = [...this.data.cart];
    const item = cart.find(i => i.id === productId);
    
    if (item && item.quantity > 1) {
      item.quantity -= 1;
      this.setData({ cart });
      wx.setStorageSync('cart', cart);
      this.calculateTotal();
    }
  },

  // 增加数量
  increaseQuantity(e) {
    const productId = e.currentTarget.dataset.id;
    const cart = [...this.data.cart];
    const item = cart.find(i => i.id === productId);
    
    if (item) {
      item.quantity += 1;
      this.setData({ cart });
      wx.setStorageSync('cart', cart);
      this.calculateTotal();
    }
  },

  // 删除商品
  deleteItem(e) {
    const productId = e.currentTarget.dataset.id;
    const cart = this.data.cart.filter(i => i.id !== productId);
    
    this.setData({ cart });
    wx.setStorageSync('cart', cart);
    
    // 更新选中状态
    const selectedIds = this.data.selectedIds.filter(id => id !== productId);
    this.setData({ selectedIds });
    this.calculateTotal();
  },

  // 计算总价
  calculateTotal() {
    const { cart, selectedIds } = this.data;
    const total = cart
      .filter(item => selectedIds.includes(item.id))
      .reduce((sum, item) => sum + item.price * item.quantity, 0);
    this.setData({ totalPrice: total.toFixed(2) });
  },

  // 去结算
  goCheckout() {
    const { cart, selectedIds } = this.data;
    const selectedItems = cart.filter(item => selectedIds.includes(item.id));
    
    if (selectedItems.length === 0) {
      wx.showToast({ title: '请选择商品', icon: 'none' });
      return;
    }
    
    // 保存选中商品到临时存储
    wx.setStorageSync('checkoutItems', selectedItems);
    
    wx.navigateTo({
      url: '/pages/specialty/confirm/confirm'
    });
  }
});