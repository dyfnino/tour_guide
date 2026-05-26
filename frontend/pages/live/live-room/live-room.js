const { request, listLives, listLiveMessages, sendLiveMessage } = require('../../../utils/api.js');

Page({
  data: {
    room: null,
    inputMsg: '',
    messages: [],
    likeCount: 0,
    lastMsgId: ''
  },

  onLoad(options) {
    const id = options.id;
    if (id) {
      this.loadRoom(id);
    }
  },

  async loadRoom(id) {
    try {
      // 加载直播信息
      const liveRes = await request(`/live/lives/${id}`);
      const room = {
        id: liveRes.id,
        title: liveRes.title,
        lecturer: liveRes.lecturer,
        online: liveRes.viewers,
        image: liveRes.cover_image,
        videoUrl: liveRes.live_url
      };
      this.setData({ room });
      wx.setNavigationBarTitle({ title: room.title });

      // 加载聊天消息
      const msgsRes = await listLiveMessages(id);
      const messages = (msgsRes || []).map(m => ({
        id: m.id,
        user: m.nickname,
        content: m.content
      }));
      const lastMsgId = messages.length ? messages[messages.length - 1].id : '';
      this.setData({ messages, lastMsgId });
    } catch (err) {
      console.error('直播间加载失败:', err);
      wx.showToast({ title: '加载失败', icon: 'none' });
    }
  },

  onMsgInput(e) {
    this.setData({ inputMsg: e.detail.value });
  },

  async sendMsg() {
    const text = (this.data.inputMsg || '').trim();
    if (!text) return;
    if (!this.data.room) return;
    const roomId = this.data.room.id;

    // 先本地追加用户消息
    const tempMsg = { id: 'tmp-' + Date.now(), user: '我', content: text };
    this.setData({
      messages: [...this.data.messages, tempMsg],
      inputMsg: '',
      lastMsgId: tempMsg.id
    });

    try {
      // 发送到服务端
      const res = await sendLiveMessage(roomId, text);
      // 用服务端返回的消息替换临时消息
      const messages = this.data.messages.map(m =>
        m.id === tempMsg.id ? { id: res.id, user: res.nickname, content: res.content } : m
      );
      this.setData({ messages, lastMsgId: res.id });
    } catch (err) {
      console.error('发送消息失败:', err);
      // 移除临时消息并提示
      const messages = this.data.messages.filter(m => m.id !== tempMsg.id);
      this.setData({ messages });
      wx.showToast({ title: '发送失败', icon: 'none' });
    }
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
      title: this.data.room ? this.data.room.title : '直播间',
      path: `/pages/live/live-room/live-room?id=${this.data.room ? this.data.room.id : ''}`
    };
  }
});