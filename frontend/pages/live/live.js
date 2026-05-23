const { listLives, listReplays } = require('../../utils/api.js');

Page({
  data: {
    liveRoom: null,
    replayList: []
  },

  onLoad() {
    this.loadData();
  },

  async loadData() {
    try {
      const [livesRes, replaysRes] = await Promise.all([
        listLives({ status: 'live' }),
        listReplays()
      ]);
      const lives = livesRes || [];
      const liveRoom = lives.length > 0 ? {
        id: lives[0].id,
        title: lives[0].title,
        lecturer: lives[0].lecturer,
        online: lives[0].viewers,
        image: lives[0].cover_image,
        videoUrl: lives[0].live_url
      } : null;

      const replays = (replaysRes || []).map(r => ({
        id: r.id,
        name: r.title,
        image: r.cover_image,
        lecturer: '',
        views: r.views,
        duration: r.duration ? this.formatDuration(r.duration) : '',
        videoUrl: r.replay_url
      }));

      this.setData({ liveRoom, replayList: replays });
    } catch (err) {
      console.error('直播数据加载失败:', err);
    }
  },

  formatDuration(seconds) {
    const h = Math.floor(seconds / 3600);
    const m = Math.floor((seconds % 3600) / 60);
    const s = seconds % 60;
    if (h > 0) {
      return `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;
    }
    return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;
  },

  onPullDownRefresh() {
    this.loadData().then(() => wx.stopPullDownRefresh());
  },

  onShareAppMessage() {
    return { title: '直播课堂', path: '/pages/live/live' };
  },

  onLiveTap() {
    const room = this.data.liveRoom;
    if (room) {
      wx.navigateTo({ url: `/pages/live/live-room/live-room?id=${room.id}` });
    } else {
      wx.showToast({ title: '暂无直播', icon: 'none' });
    }
  },

  onReplayMoreTap() {
    wx.showToast({ title: '已为您加载更多', icon: 'none' });
  },

  onReplayTap(e) {
    const id = e.currentTarget.dataset.id;
    wx.navigateTo({ url: `/pages/live/replay/replay?id=${id}` });
  }
});