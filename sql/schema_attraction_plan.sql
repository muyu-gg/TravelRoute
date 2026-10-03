-- 景点信息表
CREATE TABLE IF NOT EXISTS `attraction` (
  `id` int NOT NULL AUTO_INCREMENT,
  `poi_id` bigint NOT NULL COMMENT '景点唯一标识',
  `area` varchar(100) DEFAULT NULL COMMENT '所在区域',
  `name` varchar(120) NOT NULL COMMENT '景点名称',
  `comment_count` double DEFAULT NULL COMMENT '评论数量',
  `score` double NOT NULL DEFAULT 0 COMMENT '评分',
  `is_advertisement` tinyint(1) NOT NULL DEFAULT 0 COMMENT '是否为广告内容',
  `is_recommend` tinyint(1) NOT NULL DEFAULT 0 COMMENT '是否被推荐',
  `city_name` varchar(50) NOT NULL COMMENT '城市名称',
  `image` varchar(500) DEFAULT NULL COMMENT '图片',
  `distance` varchar(50) DEFAULT NULL COMMENT '与市中心的距离',
  `tags` varchar(120) DEFAULT NULL COMMENT '标签',
  `detail_url` varchar(500) NOT NULL COMMENT '详情页链接',
  `market_price` double DEFAULT NULL COMMENT '市场票价',
  `preferential_price` double DEFAULT NULL COMMENT '优惠价格',
  `preferential_desc` varchar(50) DEFAULT NULL COMMENT '优惠描述',
  `actual_price` varchar(50) NOT NULL COMMENT '实际票价',
  `price_type` int DEFAULT NULL COMMENT '价格类型',
  `price_type_desc` varchar(50) DEFAULT NULL COMMENT '价格类型描述',
  `is_free` tinyint(1) NOT NULL DEFAULT 0 COMMENT '是否免费',
  `longitude` double NOT NULL COMMENT '经度',
  `latitude` double NOT NULL COMMENT '纬度',
  `heat_score` double DEFAULT NULL COMMENT '热度评分',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uniq_poi_id` (`poi_id`),
  KEY `idx_attraction_city` (`city_name`),
  KEY `idx_attraction_name` (`name`),
  KEY `idx_attraction_score` (`score`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='旅游景点信息';

-- 景点收藏表
CREATE TABLE IF NOT EXISTS `attraction_favorite` (
  `id` int NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL COMMENT '收藏用户',
  `attraction_id` int NOT NULL COMMENT '收藏景点',
  `created_at` datetime(6) NOT NULL COMMENT '收藏时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uniq_user_attraction_favorite` (`user_id`, `attraction_id`),
  KEY `idx_favorite_user` (`user_id`),
  KEY `idx_favorite_attraction` (`attraction_id`),
  CONSTRAINT `fk_favorite_user` FOREIGN KEY (`user_id`) REFERENCES `accounts_user` (`id`),
  CONSTRAINT `fk_favorite_attraction` FOREIGN KEY (`attraction_id`) REFERENCES `attraction` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='景点收藏';

-- 景点评论表
CREATE TABLE IF NOT EXISTS `attraction_comment` (
  `id` int NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL COMMENT '评论用户',
  `attraction_id` int NOT NULL COMMENT '评论景点',
  `content` longtext NOT NULL COMMENT '评论内容',
  `created_at` datetime(6) NOT NULL COMMENT '评论时间',
  PRIMARY KEY (`id`),
  KEY `idx_comment_user` (`user_id`),
  KEY `idx_comment_attraction` (`attraction_id`),
  CONSTRAINT `fk_comment_user` FOREIGN KEY (`user_id`) REFERENCES `accounts_user` (`id`),
  CONSTRAINT `fk_comment_attraction` FOREIGN KEY (`attraction_id`) REFERENCES `attraction` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='景点评论';

-- AI路线规划结果表
CREATE TABLE IF NOT EXISTS `route_plan` (
  `id` int NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL COMMENT '提交规划的用户',
  `city` varchar(50) NOT NULL COMMENT '目的地城市',
  `budget` varchar(80) NOT NULL COMMENT '用户输入的旅行预算',
  `travel_time` varchar(80) NOT NULL COMMENT '用户输入的出行时间',
  `preferences` varchar(300) NOT NULL COMMENT '用户输入的旅行偏好',
  `intent_data` json DEFAULT NULL COMMENT 'AI 识别出的结构化意图',
  `process_steps` json DEFAULT NULL COMMENT 'LangGraph 规划过程步骤',
  `final_plan` longtext NOT NULL COMMENT 'AI 生成的最终路线说明',
  `status` varchar(20) NOT NULL DEFAULT 'running' COMMENT '规划任务状态',
  `error_message` varchar(300) NOT NULL DEFAULT '' COMMENT '规划失败原因',
  `created_at` datetime(6) NOT NULL COMMENT '创建时间',
  PRIMARY KEY (`id`),
  KEY `idx_route_plan_user_time` (`user_id`, `created_at` DESC),
  KEY `idx_route_plan_city` (`city`),
  CONSTRAINT `fk_route_plan_user` FOREIGN KEY (`user_id`) REFERENCES `accounts_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='AI 路线规划结果';

-- AI路线规划站点表
CREATE TABLE IF NOT EXISTS `route_plan_stop` (
  `id` int NOT NULL AUTO_INCREMENT,
  `plan_id` int NOT NULL COMMENT '所属路线规划',
  `attraction_idE_id` int DEFAULT NULL COMMENT '关联景点',
  `day_index` smallint unsigned NOT NULL COMMENT '第几天',
  `sequence` smallint unsigned NOT NULL COMMENT '当天第几个',
  `name` varchar(120) NOT NULL COMMENT '景点名称',
  `city_name` varchar(50) NOT NULL COMMENT '城市名称',
  `longitude` double NOT NULL COMMENT '经度',
  `latitude` double NOT NULL COMMENT '纬度',
  `intro` longtext NOT NULL COMMENT '站点介绍',
  `created_at` datetime(6) NOT NULL COMMENT '创建时间',
  PRIMARY KEY (`id`),
  KEY `idx_route_stop_plan_day_seq` (`plan_id`, `day_index`, `sequence`),
  KEY `idx_route_stop_attraction` (`attractionE_id`),
  CONSTRAINT `fk_route_stop_plan` FOREIGN KEY (`plan_id`) REFERENCES `route_plan` (`id`),
  CONSTRAINT `fk_route_stop_attraction` FOREIGN KEY (`attractionE_id`) REFERENCES `attraction` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='AI 路线规划站点';