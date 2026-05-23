const { replays, liveRoom } = require('../../utils/mock.js');

Page({
  data: {
    liveRoom,
    replayList: replays
  },

  onLoad() {},

  onPullDownRefresh() {
    setTimeout(() => wx.stopPullDownRefresh(), 600);
  },

  onShareAppMessage() {
    return { title: '直播课堂', path: '/pages/live/live' };
  },

  onLiveTap() {
    wx.navigateTo({ url: `/pages/live/live-room/live-room?id=${this.data.liveRoom.id}` });
  },

  onReplayMoreTap() {
    wx.showToast({ title: '已为您加载更多', icon: 'none' });
  },

  onReplayTap(e) {
    const id = e.currentTarget.dataset.id;
    wx.navigateTo({ url: `/pages/live/replay/replay?id=${id}` });
  }
});