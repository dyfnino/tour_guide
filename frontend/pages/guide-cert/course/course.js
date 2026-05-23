const { getCourse, createCourseOrder, payOrder } = require('../../../utils/api.js');

Page({
  data: {
    course: null,
    orderStatus: '' // 订单状态：unpaid / paid / completed
  },

  onLoad(options) {
    const id = options.id;
    if (id) {
      this.loadCourse(id);
    }
  },

  async loadCourse(id) {
    try {
      const res = await getCourse(id);
      this.setData({
        course: {
          id: res.id,
          name: res.name,
          image: res.image,
          desc: res.description || '',
          price: res.is_free ? '免费' : ('¥' + res.price),
          priceNum: parseFloat(res.price) || 0,
          isFree: res.is_free || false,
          lecturer: res.level || '',
          category: res.category
        }
      });
      wx.setNavigationBarTitle({ title: res.name });
    } catch (err) {
      console.error('课程详情加载失败:', err);
      wx.showToast({ title: '加载失败', icon: 'none' });
    }
  },

  async onEnroll() {
    const course = this.data.course;
    if (!course) return;

    // 检查是否登录
    const token = wx.getStorageSync('token');
    if (!token) {
      wx.showModal({
        title: '请先登录',
        content: '登录后才能学习课程',
        confirmText: '去登录',
        success: (res) => {
          if (res.confirm) {
            wx.navigateTo({ url: '/pages/login/login' });
          }
        }
      });
      return;
    }

    wx.showLoading({ title: '处理中...' });
    try {
      const orderRes = await createCourseOrder(course.id);

      if (orderRes.status === 'completed') {
        // 免费课程，已直接enroll
        wx.hideLoading();
        wx.showToast({ title: '已加入学习', icon: 'success' });
        setTimeout(() => {
          wx.navigateTo({ url: '/pages/profile/my-courses/my-courses' });
        }, 1200);
      } else if (orderRes.status === 'unpaid') {
        // 付费课程，已创建订单，提醒去支付
        wx.hideLoading();
        wx.showModal({
          title: '订单已创建',
          content: `课程费用 ${course.price}，请前往订单完成支付后开始学习`,
          confirmText: '去支付',
          cancelText: '稍后再说',
          success: (res) => {
            if (res.confirm) {
              wx.navigateTo({ url: `/pages/profile/orders/detail/detail?id=${orderRes.id}` });
            }
          }
        });
      } else if (orderRes.status === 'paid') {
        // 已支付
        wx.hideLoading();
        wx.showToast({ title: '已购买，开始学习', icon: 'success' });
        setTimeout(() => {
          wx.navigateTo({ url: '/pages/profile/my-courses/my-courses' });
        }, 1200);
      }
    } catch (err) {
      wx.hideLoading();
      console.error('创建课程订单失败:', err);
      if (err.statusCode === 401) {
        wx.showModal({
          title: '请先登录',
          content: '登录后才能学习课程',
          confirmText: '去登录',
          success: (res) => {
            if (res.confirm) {
              wx.navigateTo({ url: '/pages/login/login' });
            }
          }
        });
      } else {
        wx.showToast({ title: '操作失败，请重试', icon: 'none' });
      }
    }
  }
});