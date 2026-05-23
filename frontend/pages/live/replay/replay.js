const { replays } = require('../../../utils/mock.js');

Page({
  data: { replay: null },

  onLoad(options) {
    const id = parseInt(options.id, 10);
    const replay = replays.find(r => r.id === id) || replays[0];
    this.setData({ replay });
    wx.setNavigationBarTitle({ title: replay.name });
  }
});