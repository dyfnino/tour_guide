const { liveRoom } = require('../../../utils/mock.js');

Page({
  data: {
    room: liveRoom,
    inputMsg: '',
    messages: [
      { id: 1, user: '小美', content: '老师讲得真清楚！' },
      { id: 2, user: '阿强', content: '请问导游证多久能拿到？' },
      { id: 3, user: '系统', content: '欢迎进入直播间，请文明发言。' }
    ],
    likeCount: 0
  },

  onLoad() {
    wx.setNavigationBarTitle({ title: liveRoom.title });
  },

  onMsgInput(e) {
    this.setData({ inputMsg: e.detail.value });
  },

  sendMsg() {
    const text = (this.data.inputMsg || '').trim();
    if (!text) return;
    const messages = [
      ...this.data.messages,
      { id: Date.now(), user: '我', content: text }
    ];
    this.setData({ messages, inputMsg: '' });
  },

  like() {
    this.setData({ likeCount: this.data.likeCount + 1 });
  },

  share() {
    wx.showShareMenu({ withShareTicket: true });
    wx.showToast({ title: '请点击右上角分享', icon: 'none' });
  },

  onShareAppMessage() {
    return {
      title: this.data.room.title,
      path: `/pages/live/live-room/live-room?id=${this.data.room.id}`
    };
  }
});