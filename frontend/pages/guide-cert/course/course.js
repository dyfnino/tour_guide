const {
  getCourse, createCourseOrder, payOrder,
  myCoursesDetail, updateProgress
} = require('../../../utils/api.js');

// 默认演示媒体（后端未返回 media_url 时兜底）
const DEFAULT_VIDEO_URL = 'https://www.w3schools.com/html/mov_bbb.mp4';
const DEFAULT_AUDIO_URL = 'https://www.w3schools.com/html/horse.mp3';

Page({
  data: {
    course: null,
    enrolled: false,
    isPlaying: false,
    mediaType: 'video',
    mediaUrl: '',
    audioPlaying: false,
    progress: 0,                  // 学习进度 0-100
    duration: 0,                  // 媒体总时长
    currentTime: 0                // 媒体当前时间
  },

  onLoad(options) {
    const id = options.id;
    if (options.enrolled === '1') {
      this.setData({ enrolled: true });
    }
    this._lastReportedProgress = -1;
    if (id) {
      this.courseId = parseInt(id, 10);
      this.loadCourse(id);
      this.checkEnrolled(id);
    }
  },

  // 校验已购状态并同步进度
  async checkEnrolled(id) {
    try {
      const list = await myCoursesDetail();
      const found = (list || []).find(c => String(c.id) === String(id));
      if (found) {
        this.setData({ enrolled: true, progress: found.progress || 0 });
      }
    } catch (err) {
      // 忽略
    }
  },

  async loadCourse(id) {
    try {
      const res = await getCourse(id);
      const category = (res.category || '') + '';
      // 优先后端字段，否则按分类兜底
      const mediaType = res.media_type || (category.indexOf('audio') >= 0 ? 'audio' : 'video');
      const mediaUrl = res.media_url ||
        (mediaType === 'audio' ? DEFAULT_AUDIO_URL : DEFAULT_VIDEO_URL);

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
        },
        mediaType,
        mediaUrl
      });
      wx.setNavigationBarTitle({ title: res.name });

      if (mediaType === 'audio') {
        this.initAudio(mediaUrl);
      }
    } catch (err) {
      console.error('课程详情加载失败:', err);
      wx.showToast({ title: '加载失败', icon: 'none' });
    }
  },

  initAudio(url) {
    const ctx = wx.createInnerAudioContext();
    ctx.src = url;
    ctx.onPlay(() => this.setData({ audioPlaying: true }));
    ctx.onPause(() => this.setData({ audioPlaying: false }));
    ctx.onStop(() => this.setData({ audioPlaying: false }));
    ctx.onEnded(() => {
      this.setData({ audioPlaying: false });
      this.handleMediaEnded();
    });
    ctx.onTimeUpdate(() => {
      const dur = ctx.duration || 0;
      const cur = ctx.currentTime || 0;
      if (dur > 0) {
        const pct = Math.min(100, Math.floor((cur / dur) * 100));
        this.setData({ duration: dur, currentTime: cur });
        this.maybeReportProgress(pct);
      }
    });
    ctx.onError((err) => {
      console.error('音频播放错误', err);
      wx.showToast({ title: '音频播放失败', icon: 'none' });
    });
    this.audioCtx = ctx;
  },

  onUnload() {
    // 离开页面时上报最终进度
    this.flushProgress();
    if (this.audioCtx) {
      this.audioCtx.stop();
      this.audioCtx.destroy && this.audioCtx.destroy();
      this.audioCtx = null;
    }
  },

  // 立即学习
  async onEnroll() {
    const course = this.data.course;
    if (!course) return;

    if (this.data.enrolled) {
      this.startPlay();
      return;
    }

    const token = wx.getStorageSync('token');
    if (!token) {
      this.promptLogin();
      return;
    }

    wx.showLoading({ title: '处理中...' });
    try {
      const orderRes = await createCourseOrder(course.id);

      if (orderRes.status === 'completed') {
        wx.hideLoading();
        this.setData({ enrolled: true });
        wx.showToast({ title: '已加入学习', icon: 'success' });
        setTimeout(() => this.startPlay(), 600);
      } else if (orderRes.status === 'unpaid') {
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
        wx.hideLoading();
        this.setData({ enrolled: true });
        wx.showToast({ title: '已购买，开始学习', icon: 'success' });
        setTimeout(() => this.startPlay(), 600);
      }
    } catch (err) {
      wx.hideLoading();
      console.error('创建课程订单失败:', err);
      if (err.statusCode === 401) {
        this.promptLogin();
      } else {
        wx.showToast({ title: '操作失败，请重试', icon: 'none' });
      }
    }
  },

  promptLogin() {
    wx.showModal({
      title: '请先登录',
      content: '登录后才能学习课程',
      confirmText: '去登录',
      success: (res) => {
        if (res.confirm) wx.navigateTo({ url: '/pages/login/login' });
      }
    });
  },

  startPlay() {
    this.setData({ isPlaying: true });
    if (this.data.mediaType === 'video') {
      setTimeout(() => {
        if (!this.videoCtx) {
          this.videoCtx = wx.createVideoContext('courseVideo', this);
        }
        this.videoCtx && this.videoCtx.play();
      }, 100);
    } else if (this.data.mediaType === 'audio') {
      this.audioCtx && this.audioCtx.play();
    }
  },

  onAudioToggle() {
    if (!this.audioCtx) return;
    if (this.data.audioPlaying) this.audioCtx.pause();
    else this.audioCtx.play();
  },

  // 视频时间更新
  onVideoTimeUpdate(e) {
    const { currentTime, duration } = e.detail || {};
    if (!duration || duration <= 0) return;
    const pct = Math.min(100, Math.floor((currentTime / duration) * 100));
    this.setData({ duration, currentTime });
    this.maybeReportProgress(pct);
  },

  onVideoEnded() {
    this.handleMediaEnded();
  },

  onVideoError(e) {
    console.error('视频播放错误', e.detail);
    wx.showToast({ title: '视频播放失败', icon: 'none' });
  },

  // 媒体播放完成：进度强制为 100
  handleMediaEnded() {
    this.setData({ progress: 100 });
    this.reportProgress(100, true);
    wx.showToast({ title: '本节学习完成', icon: 'success' });
  },

  // 进度变化时按阈值上报，避免请求过多
  maybeReportProgress(pct) {
    if (!this.data.enrolled || !this.courseId) return;
    if (pct <= this.data.progress) return; // 进度只往上走
    this.setData({ progress: pct });
    if (pct - this._lastReportedProgress >= 5 || pct === 100) {
      this.reportProgress(pct);
    }
  },

  // 离开时强制上报最新进度
  flushProgress() {
    if (this.data.enrolled && this.courseId &&
        this.data.progress > 0 &&
        this.data.progress !== this._lastReportedProgress) {
      this.reportProgress(this.data.progress);
    }
  },

  async reportProgress(pct, finalCall) {
    try {
      await updateProgress(this.courseId, pct);
      this._lastReportedProgress = pct;
    } catch (err) {
      if (!finalCall) console.warn('上报进度失败', err);
    }
  }
});