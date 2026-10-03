-- 觅途行（MiTuXing）景点详情页 V2 升级脚本
-- 功能：为 attraction 表添加 V2 版本所需的新字段

-- 添加宣传图URL字段
ALTER TABLE attraction ADD COLUMN banner_url VARCHAR(500) DEFAULT NULL COMMENT '宣传图URL' AFTER heat_score;

-- 添加活动名称字段
ALTER TABLE attraction ADD COLUMN activity_name VARCHAR(100) DEFAULT NULL COMMENT '活动名称' AFTER banner_url;

-- 添加活动时间字段
ALTER TABLE attraction ADD COLUMN activity_time VARCHAR(100) DEFAULT NULL COMMENT '活动时间' AFTER activity_name;

-- 添加数据来源字段
ALTER TABLE attraction ADD COLUMN data_source VARCHAR(100) DEFAULT '本站MySQL' COMMENT '数据来源' AFTER activity_time;

-- 添加距市中心距离字段（精确到小数点后2位）
ALTER TABLE attraction ADD COLUMN distance_center DECIMAL(10,2) DEFAULT 0 COMMENT '距市中心(km)' AFTER data_source;

-- 添加价格说明字段
ALTER TABLE attraction ADD COLUMN price_desc VARCHAR(100) DEFAULT NULL COMMENT '价格说明' AFTER distance_center;


-- 可选：为已有数据填充示例值（根据实际情况调整）
-- UPDATE attraction SET data_source = '本站MySQL' WHERE data_source IS NULL;
-- UPDATE attraction SET price_desc = '门票' WHERE price_desc IS NULL AND price_type IS NOT NULL;
-- UPDATE attraction SET distance_center = 0 WHERE distance_center IS NULL;