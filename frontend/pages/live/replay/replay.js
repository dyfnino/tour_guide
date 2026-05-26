const { getReplay, incrementReplayView } = require('../../../utils/api.js');

function formatDuration(seconds) {
  if (!seconds || seconds <= 0) return '';
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  const s = seconds % 60;
  if (h > 0) {
    return `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;
  }
  return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;
}

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
          views: res.views || 0,
          duration: formatDuration(res.duration),
          description: res.description || ''
        }
      });
      wx.setNavigationBarTitle({ title: res.title });

      // 上报一次观看（失败不影响主流程）
      try {
        const updated = await incrementReplayView(id);
        if (updated && updated.views != null) {
          this.setData({ 'replay.views': updated.views });
        }
      } catch (e) { /* ignore */ }
    } catch (err) {
      console.error('回放加载失败:', err);
      wx.showToast({ title: '加载失败', icon: 'none' });
    }
  }
});