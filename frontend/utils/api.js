// 后端 API 调用封装
// 使用方式：const { listCourses } = require('../../utils/api.js');

const BASE_URL = 'http://localhost:8000/api';

function request(path, options = {}) {
  const token = wx.getStorageSync('token');
  const header = {
    'Content-Type': 'application/json',
    ...(options.header || {})
  };
  if (token && !String(token).startsWith('mock-')) {
    header['Authorization'] = `Bearer ${token}`;
  }
  return new Promise((resolve, reject) => {
    wx.request({
      url: BASE_URL + path,
      method: options.method || 'GET',
      data: options.data,
      header,
      timeout: 10000,
      success: (res) => {
        if (res.statusCode >= 200 && res.statusCode < 300) {
          resolve(res.data);
        } else {
          reject({ statusCode: res.statusCode, data: res.data });
        }
      },
      fail: reject
    });
  });
}

// ---- 鉴权 ----
const wechatLogin = (code) => request('/auth/wechat', { method: 'POST', data: { code } });
const getMe = () => request('/auth/me');
const updateProfile = (data) => request('/auth/me', { method: 'PUT', data });

// ---- 课程 ----
const listCourses = (params = {}) => {
  const qs = Object.keys(params).map(k => `${k}=${encodeURIComponent(params[k])}`).join('&');
  return request('/courses' + (qs ? `?${qs}` : ''));
};
const getCourse = (id) => request(`/courses/${id}`);

// ---- 题库与考试 ----
const listQuestions = (params = {}) => {
  const qs = Object.keys(params).map(k => `${k}=${encodeURIComponent(params[k])}`).join('&');
  return request('/questions' + (qs ? `?${qs}` : ''));
};
const startExam = (data = {}) => request('/exams/start', { method: 'POST', data });
const submitExam = (examId, answers) =>
  request(`/exams/${examId}/submit`, { method: 'POST', data: { answers } });

// ---- 直播 ----
const listLives = (params = {}) => {
  const qs = Object.keys(params).map(k => `${k}=${encodeURIComponent(params[k])}`).join('&');
  return request('/live/lives' + (qs ? `?${qs}` : ''));
};
const listReplays = (params = {}) => {
  const qs = Object.keys(params).map(k => `${k}=${encodeURIComponent(params[k])}`).join('&');
  return request('/live/replays' + (qs ? `?${qs}` : ''));
};
const getReplay = (id) => request(`/live/replays/${id}`);
const incrementReplayView = (id) =>
  request(`/live/replays/${id}/view`, { method: 'POST' });
const listLiveMessages = (liveId) => request(`/live/lives/${liveId}/messages`);
const sendLiveMessage = (liveId, content) =>
  request(`/live/lives/${liveId}/messages`, { method: 'POST', data: { content } });

// ---- 商品 ----
const listProducts = (params = {}) => {
  const qs = Object.keys(params).map(k => `${k}=${encodeURIComponent(params[k])}`).join('&');
  return request('/products' + (qs ? `?${qs}` : ''));
};

// ---- 订单 ----
const createCourseOrder = (courseId) =>
  request('/orders/course', { method: 'POST', data: { course_id: courseId } });
const payOrder = (orderId) =>
  request(`/orders/${orderId}`, { method: 'PUT', data: { status: 'paid' } });
// 真实支付：发起 JSAPI 下单，拿到 wx.requestPayment 所需参数
const prepayOrder = (orderId) =>
  request(`/orders/${orderId}/pay`, { method: 'POST' });
// Mock 模式下的"模拟支付成功"接口（仅 WX_PAY_MOCK=1 可用）
const mockPaidOrder = (orderId) =>
  request(`/orders/${orderId}/mock-paid`, { method: 'POST' });
const getOrder = (orderId) => request(`/orders/${orderId}`);
// 轮询订单状态：3次每1.5秒，命中 paid 即返回；都没命中返回最后一次的状态
const pollOrderPaid = async (orderId, times = 3, interval = 1500) => {
  for (let i = 0; i < times; i++) {
    try {
      const o = await getOrder(orderId);
      if (o && (o.status === 'paid' || o.status === 'completed')) return o;
    } catch (e) { /* ignore */ }
    if (i < times - 1) {
      await new Promise(r => setTimeout(r, interval));
    }
  }
  try { return await getOrder(orderId); } catch (e) { return null; }
};
const confirmReceipt = (orderId) =>
  request(`/orders/${orderId}`, { method: 'PUT', data: { status: 'completed' } });

// ---- 我的（学习进度） ----
const myCoursesDetail = () => request('/me/courses/detail');
const enrollCourse = (courseId) =>
  request(`/me/courses/${courseId}/enroll`, { method: 'POST' });
const updateProgress = (courseId, progress) =>
  request(`/me/courses/${courseId}/progress`, { method: 'PUT', data: { progress } });

module.exports = {
  BASE_URL,
  request,
  wechatLogin, getMe, updateProfile,
  listCourses, getCourse,
  listQuestions, startExam, submitExam,
  listLives, listReplays, getReplay, listLiveMessages, sendLiveMessage,
  incrementReplayView,
  listProducts,
  myCoursesDetail, enrollCourse, updateProgress,
  createCourseOrder, payOrder, prepayOrder, mockPaidOrder, getOrder, confirmReceipt, pollOrderPaid,
};