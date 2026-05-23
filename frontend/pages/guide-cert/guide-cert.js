const { courses } = require('../../utils/mock.js');

Page({
  data: {
    currentTab: 'online',
    selectedCategory: 'all',
    allCourses: courses,
    courseList: courses,
    tabs: [
      { key: 'online', name: '网课点播' },
      { key: 'practice', name: '考试刷题' },
      { key: 'mock', name: '模拟考试' },
      { key: 'live', name: '直播网课' },
      { key: 'ai', name: 'AI测评' }
    ],
    categories: [
      { key: 'all', name: '全部' },
      { key: 'basic', name: '基础知识' },
      { key: 'business', name: '导游业务' },
      { key: 'policy', name: '政策法规' },
      { key: 'local', name: '地方导游' }
    ]
  },

  onLoad() {},

  onPullDownRefresh() {
    setTimeout(() => wx.stopPullDownRefresh(), 800);
  },

  onShareAppMessage() {
    return { title: '导游考证', path: '/pages/guide-cert/guide-cert' };
  },

  // 切换 Tab
  switchTab(e) {
    const tab = e.currentTarget.dataset.tab;
    this.setData({ currentTab: tab });

    // 直接跳转的 Tab
    if (tab === 'practice') {
      this.setData({ currentTab: 'online' });
      wx.navigateTo({ url: '/pages/guide-cert/practice/practice' });
    } else if (tab === 'mock') {
      this.setData({ currentTab: 'online' });
      wx.navigateTo({ url: '/pages/guide-cert/mock-exam/mock-exam' });
    } else if (tab === 'live') {
      this.setData({ currentTab: 'online' });
      wx.navigateTo({ url: '/pages/live/live' });
    } else if (tab === 'ai') {
      this.setData({ currentTab: 'online' });
      wx.navigateTo({ url: '/pages/ai-test/ai-test' });
    }
  },

  // 选择分类
  selectCategory(e) {
    const category = e.currentTarget.dataset.category;
    this.setData({ selectedCategory: category });
    this.filterCourses(category);
  },

  filterCourses(category) {
    const list = category === 'all'
      ? this.data.allCourses
      : this.data.allCourses.filter(c => c.category === category);
    this.setData({ courseList: list });
  },

  // 课程详情
  onCourseTap(e) {
    const id = e.currentTarget.dataset.id;
    wx.navigateTo({ url: `/pages/guide-cert/course/course?id=${id}` });
  }
});