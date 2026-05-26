const { listLives, listReplays } = require('../../utils/api.js');

const PAGE_SIZE = 10;

Page({
  data: {
    liveRoom: null,
    replayList: [],
    page: 0,
    hasMore: true,
    loadingMore: false
  },

  onLoad() {
    this.refresh();
  },

  onShow() {
    // 进入页面时，如果还没数据则加载
    if (this.data.replayList.length === 0 && this.data.liveRoom === null) {
      this.refresh();
    }
  },

  async refresh() {
    this.setData({ page: 0, hasMore: true, replayList: [] });
    await this.loadLive();
    await this.loadMoreReplays();
  },

  async loadLive() {
    try {
      const livesRes = await listLives({ status: 'live' });
      const lives = livesRes || [];
      const liveRoom = lives.length > 0 ? {
        id: lives[0].id,
        title: lives[0].title,
        lecturer: lives[0].lecturer,
        online: lives[0].viewers,
        image: lives[0].cover_image,
        videoUrl: lives[0].live_url
      } : null;
      this.setData({ liveRoom });
    } catch (err) {
      console.error('直播信息加载失败:', err);
    }
  },

  async loadMoreReplays() {
    if (this.data.loadingMore || !this.data.hasMore) return;
    this.setData({ loadingMore: true });
    try {
      const skip = this.data.page * PAGE_SIZE;
      const res = await listReplays({ skip, limit: PAGE_SIZE });
      const items = (res || []).map(r => ({
        id: r.id,
        name: r.title,
        image: r.cover_image,
        views: r.views || 0,
        duration: r.duration ? this.formatDuration(r.duration) : '',
        videoUrl: r.replay_url
      }));
      const hasMore = items.length === PAGE_SIZE;
      this.setData({
        replayList: [...this.data.replayList, ...items],
        page: this.data.page + 1,
        hasMore,
        loadingMore: false
      });
    } catch (err) {
      console.error('回放加载失败:', err);
      this.setData({ loadingMore: false });
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
    this.refresh().then(() => wx.stopPullDownRefresh());
  },

  onReachBottom() {
    this.loadMoreReplays();
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
    this.loadMoreReplays();
  },

  onReplayTap(e) {
    const id = e.currentTarget.dataset.id;
    wx.navigateTo({ url: `/pages/live/replay/replay?id=${id}` });
  }
});