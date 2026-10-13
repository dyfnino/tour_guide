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
    // 省市区选择器的选中值：['省', '市', '区']
    region: [],
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
        const province = item.province || '';
        const city = item.city || '';
        const district = item.district || '';
        // 只有三级都有值时才回填选择器，避免无效值导致选择器定位异常
        const region = (province && city && district) ? [province, city, district] : [];
        this.setData({
          form: {
            name: item.name || '',
            phone: item.phone || '',
            province,
            city,
            district,
            detail: item.detail || '',
            is_default: !!item.is_default
          },
          region
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

  // 省市区三级联动选择
  onRegionChange(e) {
    const value = e.detail.value || [];
    const province = value[0] || '';
    const city = value[1] || '';
    const district = value[2] || '';
    this.setData({
      'form.province': province,
      'form.city': city,
      'form.district': district,
      region: [province, city, district]
    });
  },

  onToggleDefault(e) {
    this.setData({ 'form.is_default': e.detail.value });
  },

  validate() {
    const f = this.data.form;
    if (!f.name.trim()) return '请填写收货人姓名';
    if (!/^1\d{10}$/.test(f.phone.trim())) return '请填写正确的手机号';
    if (!f.province || !f.city || !f.district) return '请选择所在地区';
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
      const payload = {
        name: this.data.form.name.trim(),
        phone: this.data.form.phone.trim(),
        province: this.data.form.province,
        city: this.data.form.city,
        district: this.data.form.district,
        detail: this.data.form.detail.trim(),
        is_default: this.data.form.is_default
      };
      if (this.data.id) {
        await updateAddress(this.data.id, payload);
      } else {
        await createAddress(payload);
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
