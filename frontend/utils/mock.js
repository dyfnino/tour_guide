// Mock 数据中心，供各页面引用
const courses = [
  {
    id: 1,
    name: '导游基础知识精讲',
    image: 'https://picsum.photos/300/180?random=1',
    desc: '36课时 | 适合零基础',
    price: '免费',
    rating: '98%好评',
    students: '2000+人已学',
    lecturer: '李老师',
    category: 'basic'
  },
  {
    id: 2,
    name: '导游业务能力提升',
    image: 'https://picsum.photos/300/180?random=2',
    desc: '24课时 | 进阶提升',
    price: '¥99',
    rating: '96%好评',
    students: '1500+人已学',
    lecturer: '王老师',
    category: 'business'
  },
  {
    id: 3,
    name: '政策法规高频考点解析',
    image: 'https://picsum.photos/300/180?random=7',
    desc: '12课时 | 考点精讲',
    price: '¥69',
    rating: '99%好评',
    students: '888人已学',
    lecturer: '赵老师',
    category: 'policy'
  },
  {
    id: 4,
    name: '地方导游基础知识',
    image: 'https://picsum.photos/300/180?random=8',
    desc: '20课时 | 实操讲解',
    price: '¥129',
    rating: '95%好评',
    students: '512人已学',
    lecturer: '钱老师',
    category: 'local'
  }
];

const questionBank = [
  {
    id: 1,
    type: 'single',
    title: '中国第一部以"旅游"命名的法律是？',
    options: ['《旅游法》', '《消费者权益保护法》', '《合同法》', '《民法典》'],
    answer: 0,
    analysis: '《中华人民共和国旅游法》于2013年10月1日起施行，是我国第一部以"旅游"命名的法律。'
  },
  {
    id: 2,
    type: 'single',
    title: '导游人员的从业资格证是？',
    options: ['导游证', '导游资格证', '从业资格证', '上岗证'],
    answer: 1,
    analysis: '导游资格证是从事导游职业的资格凭证。'
  },
  {
    id: 3,
    type: 'multi',
    title: '以下属于世界文化遗产的有？（多选）',
    options: ['秦始皇陵兵马俑', '黄山', '布达拉宫', '九寨沟'],
    answer: [0, 2],
    analysis: '秦始皇陵兵马俑和布达拉宫属于世界文化遗产，黄山为文化与自然双遗产，九寨沟为自然遗产。'
  },
  {
    id: 4,
    type: 'judge',
    title: '导游人员在带团过程中可以擅自变更行程。',
    options: ['正确', '错误'],
    answer: 1,
    analysis: '导游人员不得擅自变更接待计划，应当按照旅行社确定的行程开展接待工作。'
  },
  {
    id: 5,
    type: 'single',
    title: '大雁塔位于哪座城市？',
    options: ['北京', '洛阳', '西安', '南京'],
    answer: 2,
    analysis: '大雁塔位于陕西省西安市，是唐代建筑的代表作。'
  }
];

const replays = [
  {
    id: 1,
    name: '导游基础知识精讲',
    image: 'https://picsum.photos/300/180?random=13',
    lecturer: '李老师',
    views: '5678',
    duration: '01:25:30',
    videoUrl: 'https://www.w3schools.com/html/mov_bbb.mp4'
  },
  {
    id: 2,
    name: '导游业务能力提升',
    image: 'https://picsum.photos/300/180?random=14',
    lecturer: '王老师',
    views: '3456',
    duration: '00:58:12',
    videoUrl: 'https://www.w3schools.com/html/mov_bbb.mp4'
  },
  {
    id: 3,
    name: '政策法规高频考点解析',
    image: 'https://picsum.photos/300/180?random=15',
    lecturer: '赵老师',
    views: '2345',
    duration: '01:12:00',
    videoUrl: 'https://www.w3schools.com/html/mov_bbb.mp4'
  }
];

const liveRoom = {
  id: 100,
  title: '导游资格证考试备考攻略',
  lecturer: '张老师',
  online: 1234,
  image: 'https://picsum.photos/800/400?random=12',
  // 公开的测试 m3u8 直播流，无可用时可换成 mp4
  videoUrl: 'https://www.w3schools.com/html/mov_bbb.mp4'
};

module.exports = {
  courses,
  questionBank,
  replays,
  liveRoom
};