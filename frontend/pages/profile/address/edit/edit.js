const { listAddresses, createAddress, updateAddress } = require('../../../../utils/api.js');

Page({
  data: {
    id: null,
    form: {
      name: '',
      phone: '',
      province: '',
      city: '',
      district: '',
      detail: '',
      is_default: false
    },
    submitting: false
  },

  onLoad(options) {
    if (options.id) {
      this.setData({ id: parseInt(options.id) });
      wx.setNavigationBarTitle({ title: '编辑地址' });
      this.loadAddress(parseInt(options.id));
    } else {
      wx.setNavigationBarTitle({ title: '新增地址' });
    }
  },

  async loadAddress(id) {
    try {
      const list = await listAddresses();
      const item = (list || []).find(a => a.id === id);
      if (item) {
        this.setData({
          form: {
            name: item.name || '',
            phone: item.phone || '',
            province: item.province || '',
            city: item.city || '',
            district: item.district || '',
            detail: item.detail || '',
            is_default: !!item.is_default
          }
        });
      }
    } catch (err) {
      wx.showToast({ title: '加载失败', icon: 'none' });
    }
  },

  onInput(e) {
    const field = e.currentTarget.dataset.field;
    this.setData({ [`form.${field}`]: e.detail.value });
  },

  onToggleDefault(e) {
    this.setData({ 'form.is_default': e.detail.value });
  },

  validate() {
    const f = this.data.form;
    if (!f.name.trim()) return '请填写收货人姓名';
    if (!/^1\d{10}$/.test(f.phone.trim())) return '请填写正确的手机号';
    if (!f.detail.trim()) return '请填写详细地址';
    return null;
  },

  async onSubmit() {
    if (this.data.submitting) return;
    const err = this.validate();
    if (err) {
      wx.showToast({ title: err, icon: 'none' });
      return;
    }
    this.setData({ submitting: true });
    try {
      if (this.data.id) {
        await updateAddress(this.data.id, this.data.form);
      } else {
        await createAddress(this.data.form);
      }
      wx.showToast({ title: '保存成功', icon: 'success' });
      setTimeout(() => wx.navigateBack(), 800);
    } catch (e) {
      const msg = e?.data?.detail || '保存失败';
      wx.showToast({ title: msg, icon: 'none' });
      this.setData({ submitting: false });
    }
  }
});