# 测试运行报告

**运行环境**：

- Python: 3.12.6
- DB: SQLite 内存数据库（aiosqlite + StaticPool）
- 微信支付: WX_PAY_MOCK=1
- Qwen 多模态: QWEN_MOCK=1

**运行命令**：

```bash
cd backend
python tests/run_tests.py
```

## 最终结果

```
共 31 项，成功 31，失败 0
```

## 用例清单（按模块分组）

### 基础 & 鉴权

| #   | 用例                                     | 结果    |
| --- | ---------------------------------------- | ------- |
| 1   | 健康检查 GET /                           | ✅ PASS |
| 2   | 微信登录 POST /api/auth/wechat（开发态） | ✅ PASS |
| 3   | 未登录访问受保护接口 401                 | ✅ PASS |
| 4   | 获取当前用户 GET /api/auth/me            | ✅ PASS |
| 5   | 更新昵称 PUT /api/auth/me                | ✅ PASS |

### 内容（课程 / 商品 / 题库）

| #   | 用例                                              | 结果    |
| --- | ------------------------------------------------- | ------- |
| 6   | 创建课程 + 列表 + 详情                            | ✅ PASS |
| 7   | 课程不存在返回 404                                | ✅ PASS |
| 8   | 创建商品 + 列表 + 详情                            | ✅ PASS |
| 9   | 创建题目 + 按类型/分类筛选                        | ✅ PASS |
| 10  | 模拟考试：开始 + 答题 + 提交 + 评分（答案不下发） | ✅ PASS |

### 订单 & 支付

| #   | 用例                                                    | 结果    |
| --- | ------------------------------------------------------- | ------- |
| 11  | 创建商品订单（已登录）                                  | ✅ PASS |
| 12  | 创建付费课程订单（首次）                                | ✅ PASS |
| 13  | 课程订单幂等：再次下单返回已有未支付订单                | ✅ PASS |
| 14  | 免费课程订单：直接 completed + 自动 enroll              | ✅ PASS |
| 15  | 订单列表 + 按状态过滤                                   | ✅ PASS |
| 16  | 发起支付 POST /orders/{id}/pay 返回 mock=true           | ✅ PASS |
| 17  | Mock 支付完成：订单转 paid                              | ✅ PASS |
| 18  | 课程订单支付完成自动 enroll 到学习列表                  | ✅ PASS |
| 19  | update_order：禁止前端把 unpaid 直接置 paid（安全加固） | ✅ PASS |

### 我的课程

| #   | 用例                                       | 结果    |
| --- | ------------------------------------------ | ------- |
| 20  | 加入学习 POST /me/courses/{id}/enroll      | ✅ PASS |
| 21  | 更新学习进度 PUT /me/courses/{id}/progress | ✅ PASS |
| 22  | 我的课程详情 GET /me/courses/detail        | ✅ PASS |

### 直播 / 回放 / 弹幕

| #   | 用例                        | 结果    |
| --- | --------------------------- | ------- |
| 23  | 创建直播 + 列表 + 详情      | ✅ PASS |
| 24  | 直播状态改 ended 自动建回放 | ✅ PASS |
| 25  | 回放观看次数 +1             | ✅ PASS |
| 26  | 直播间发消息 + 拉历史       | ✅ PASS |

### AI 测评（Qwen mock）

| #   | 用例                                | 结果    |
| --- | ----------------------------------- | ------- |
| 27  | 创建 AI 测评类型 + 列表             | ✅ PASS |
| 28  | AI 自由对话（mock）                 | ✅ PASS |
| 29  | AI 评估打分（mock，理论/讲解/面试） | ✅ PASS |

### 后台管理（Streamlit）

| #   | 用例                                     | 结果                           |
| --- | ---------------------------------------- | ------------------------------ |
| 30  | 后台管理：admin 模块可导入               | ✅ PASS (streamlit 缺失时跳过) |
| 31  | 后台管理：登录校验逻辑（admin/admin123） | ✅ PASS (streamlit 缺失时跳过) |

## 关于修复

本次测试触发了 1 处真实 Bug 并已修复：

- [`backend/app/api/orders.py`](../app/api/orders.py:42)：商品订单创建时 `Decimal * int` 与 `float` 相加报 `TypeError`，且 commit 后返回未预加载 items 触发 SQLAlchemy 异步懒加载错误。已改为：
  - 价格统一转 `float` 后再运算
  - commit 后用 `selectinload(Order.items)` 二次查询返回
