const { listAddresses, deleteAddress, setDefaultAddress } = require('../../../../utils/api.js');

Page({
  data: {
    addresses: [],
    mode: 'manage', // manage: 管理; select: 选择回填
    loading: false
  },

  onLoad(options) {
    this.setData({ mode: options.mode === 'select' ? 'select' : 'manage' });
  },

  onShow() {
    this.loadAddresses();
  },

  noop() {},

  async loadAddresses() {
    this.setData({ loading: true });
    try {
      const list = await listAddresses();
      this.setData({ addresses: list || [] });
    } catch (err) {
      if (err && err.statusCode === 401) {
        wx.showToast({ title: '请先登录', icon: 'none' });
      } else {
        wx.showToast({ title: '加载失败', icon: 'none' });
      }
    } finally {
      this.setData({ loading: false });
    }
  },

  // 选择模式下点击回填
  onSelect(e) {
    if (this.data.mode !== 'select') return;
    const id = e.currentTarget.dataset.id;
    const item = this.data.addresses.find(a => a.id === id);
    if (!item) return;
    wx.setStorageSync('selectedAddress', {
      id: item.id,
      name: item.name,
      phone: item.phone,
      address: `${item.province || ''}${item.city || ''}${item.district || ''}${item.detail || ''}`
    });
    wx.navigateBack();
  },

  // 新增地址
  goAdd() {
    wx.navigateTo({ url: '/pages/profile/address/edit/edit' });
  },

  // 编辑地址
  goEdit(e) {
    const id = e.currentTarget.dataset.id;
    wx.navigateTo({ url: `/pages/profile/address/edit/edit?id=${id}` });
  },

  // 设为默认
  async onSetDefault(e) {
    const id = e.currentTarget.dataset.id;
    try {
      await setDefaultAddress(id);
      this.loadAddresses();
    } catch (err) {
      wx.showToast({ title: '操作失败', icon: 'none' });
    }
  },

  // 删除地址
  onDelete(e) {
    const id = e.currentTarget.dataset.id;
    wx.showModal({
      title: '提示',
      content: '确定删除该地址吗？',
      success: async (res) => {
        if (!res.confirm) return;
        try {
          await deleteAddress(id);
          wx.showToast({ title: '已删除', icon: 'success' });
          this.loadAddresses();
        } catch (err) {
          wx.showToast({ title: '删除失败', icon: 'none' });
        }
      }
    });
  }
});