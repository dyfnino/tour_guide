Page({
  /**
   * 页面的初始数据
   */
  data: {
    chatMessages: [],
    inputValue: '',
    // 模拟deepseek API配置
    aiConfig: {
      apiKey: 'your_deepseek_api_key',
      apiUrl: 'https://api.deepseek.com/v1/chat/completions'
    }
  },

  /**
   * 生命周期函数--监听页面加载
   */
  onLoad(options) {
    console.log('AI test page loaded');
  },

  /**
   * 生命周期函数--监听页面初次渲染完成
   */
  onReady() {
    console.log('AI test page ready');
  },

  /**
   * 生命周期函数--监听页面显示
   */
  onShow() {
    console.log('AI test page shown');
  },

  /**
   * 生命周期函数--监听页面隐藏
   */
  onHide() {
    console.log('AI test page hidden');
  },

  /**
   * 生命周期函数--监听页面卸载
   */
  onUnload() {
    console.log('AI test page unloaded');
  },

  /**
   * 页面相关事件处理函数--监听用户下拉动作
   */
  onPullDownRefresh() {
    console.log('AI test page pull down refresh');
    // 模拟刷新数据
    setTimeout(() => {
      wx.stopPullDownRefresh();
    }, 1000);
  },

  /**
   * 页面上拉触底事件的处理函数
   */
  onReachBottom() {
    console.log('AI test page reach bottom');
  },

  /**
   * 用户点击右上角分享
   */
  onShareAppMessage() {
    return {
      title: 'AI测评',
      path: '/pages/ai-test/ai-test'
    };
  },

  // 选择测评类型
  onTestTypeTap(e) {
    console.log('Test type tapped');
    // 跳转到对应测评页面
  },

  // 输入框内容变化
  onInputChange(e) {
    this.setData({
      inputValue: e.detail.value
    });
  },

  // 发送消息
  onSendMessage() {
    const inputValue = this.data.inputValue;
    if (!inputValue.trim()) return;

    // 添加用户消息
    const newMessage = {
      content: inputValue,
      type: 'user'
    };
    const updatedMessages = [...this.data.chatMessages, newMessage];
    this.setData({
      chatMessages: updatedMessages,
      inputValue: ''
    });

    // 模拟AI回复
    this.getAIResponse(inputValue);
  },

  // 获取AI回复
  getAIResponse(userInput) {
    console.log('Getting AI response for:', userInput);
    
    // 模拟AI回复
    setTimeout(() => {
      const aiResponse = {
        content: `我收到了你的消息：${userInput}\n\n这是一条模拟的AI回复。在实际应用中，这里会调用真实的AI API（如deepseek）来生成回复。`,
        type: 'ai'
      };
      const updatedMessages = [...this.data.chatMessages, aiResponse];
      this.setData({
        chatMessages: updatedMessages
      });
    }, 1000);

    // 实际调用AI API的代码（需要配置apiKey）
    /*
    wx.request({
      url: this.data.aiConfig.apiUrl,
      method: 'POST',
      header: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${this.data.aiConfig.apiKey}`
      },
      data: {
        model: 'deepseek-chat',
        messages: [
          {
            role: 'system',
            content: '你是一个专业的导游培训助手，帮助用户提升导游技能和备考导游资格证。'
          },
          {
            role: 'user',
            content: userInput
          }
        ],
        temperature: 0.7
      },
      success: (res) => {
        if (res.data && res.data.choices && res.data.choices.length > 0) {
          const aiResponse = {
            content: res.data.choices[0].message.content,
            type: 'ai'
          };
          const updatedMessages = [...this.data.chatMessages, aiResponse];
          this.setData({
            chatMessages: updatedMessages
          });
        }
      },
      fail: (err) => {
        console.error('AI API request failed:', err);
        const errorResponse = {
          content: '抱歉，AI服务暂时不可用，请稍后再试。',
          type: 'ai'
        };
        const updatedMessages = [...this.data.chatMessages, errorResponse];
        this.setData({
          chatMessages: updatedMessages
        });
      }
    });
    */
  }
})