const { getReplay } = require('../../../utils/api.js');

Page({
  data: { replay: null },

  onLoad(options) {
    const id = options.id;
    if (id) {
      this.loadReplay(id);
    }
  },

  async loadReplay(id) {
    try {
      const res = await getReplay(id);
      this.setData({
        replay: {
          id: res.id,
          name: res.title,
          image: res.cover_image,
          videoUrl: res.replay_url,
          views: res.views,
          duration: res.duration
        }
      });
      wx.setNavigationBarTitle({ title: res.title });
    } catch (err) {
      console.error('回放加载失败:', err);
      wx.showToast({ title: '加载失败', icon: 'none' });
    }
  }
});