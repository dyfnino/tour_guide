-- 新增收货地址簿(addresses)与购物车(carts)表
-- 执行时间: 2026-07-15
-- 说明: 后端启动 init_db 会自动 create_all 建表；本脚本供已有生产库手动迁移使用。

USE guide;

-- 收货地址簿
CREATE TABLE IF NOT EXISTS addresses (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    user_id     INT NOT NULL COMMENT '所属用户',
    name        VARCHAR(50) NOT NULL COMMENT '收货人姓名',
    phone       VARCHAR(20) NOT NULL COMMENT '联系电话',
    province    VARCHAR(50) DEFAULT '' COMMENT '省',
    city        VARCHAR(50) DEFAULT '' COMMENT '市',
    district    VARCHAR(50) DEFAULT '' COMMENT '区/县',
    detail      VARCHAR(255) NOT NULL COMMENT '详细地址',
    is_default  TINYINT(1) DEFAULT 0 COMMENT '是否默认地址',
    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at  DATETIME NULL ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_addresses_user (user_id),
    CONSTRAINT fk_addresses_user FOREIGN KEY (user_id) REFERENCES users (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='收货地址簿';

-- 购物车
CREATE TABLE IF NOT EXISTS carts (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    user_id     INT NOT NULL COMMENT '所属用户',
    product_id  INT NOT NULL COMMENT '商品',
    quantity    INT NOT NULL DEFAULT 1 COMMENT '数',
    selected    TINYINT(1) DEFAULT 1 COMMENT '结算勾选状态',
    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at  DATETIME NULL ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_carts_user (user_id),
    INDEX idx_carts_product (product_id),
    UNIQUE KEY uq_cart_user_product (user_id, product_id),
    CONSTRAINT fk_carts_user FOREIGN KEY (user_id) REFERENCES users (id),
    CONSTRAINT fk_carts_product FOREIGN KEY (product_id) REFERENCES products (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='购物车';

-- 验证
SHOW TABLES LIKE 'addresses';
SHOW TABLES LIKE 'carts';