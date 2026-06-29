-- 为 orders 表添加退款相关字段
-- 执行时间: 2026-06-29
-- 说明: 模型中已定义 refunded_amount 和 refunded_at 字段，但数据库表缺少这些列

USE guide;

-- 添加 refunded_amount 字段（已退款总额）
ALTER TABLE orders 
ADD COLUMN refunded_amount FLOAT NOT NULL DEFAULT 0.0 COMMENT '已成功退款总额';

-- 添加 refunded_at 字段（最近一次退款成功时间）
ALTER TABLE orders 
ADD COLUMN refunded_at DATETIME NULL COMMENT '最近一次退款成功时间';

-- 验证字段已添加
SELECT COLUMN_NAME, COLUMN_TYPE, IS_NULLABLE, COLUMN_DEFAULT, COLUMN_COMMENT 
FROM INFORMATION_SCHEMA.COLUMNS 
WHERE TABLE_SCHEMA = 'guide' 
AND TABLE_NAME = 'orders'
AND COLUMN_NAME IN ('refunded_amount', 'refunded_at');