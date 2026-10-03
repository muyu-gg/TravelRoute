-- ============================================================
-- 旅游规划系统 - 完整数据库初始化脚本
-- 使用方式: mysql -u root -p123456 < init_database.sql
-- ============================================================

SET FOREIGN_KEY_CHECKS = 0;

DROP DATABASE IF EXISTS `travel_route_base`;
CREATE DATABASE `travel_route_base` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE `travel_route_base`;

-- ============================================================
-- 1. Django 内置基础表
-- ============================================================

CREATE TABLE `django_content_type` (
    `id` int AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `app_label` varchar(100) NOT NULL,
    `model` varchar(100) NOT NULL
);

CREATE TABLE `auth_permission` (
    `id` int AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `name` varchar(255) NOT NULL,
    `content_type_id` int NOT NULL,
    `codename` varchar(100) NOT NULL
);

CREATE TABLE `auth_group` (
    `id` int AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `name` varchar(150) NOT NULL UNIQUE
);

CREATE TABLE `auth_group_permissions` (
    `id` bigint AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `group_id` int NOT NULL,
    `permission_id` int NOT NULL
);

CREATE TABLE `django_session` (
    `session_key` varchar(40) NOT NULL PRIMARY KEY,
    `session_data` longtext NOT NULL,
    `expire_date` datetime(6) NOT NULL
);

CREATE TABLE `django_migrations` (
    `id` bigint AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `app` varchar(255) NOT NULL,
    `name` varchar(255) NOT NULL,
    `applied` datetime(6) NOT NULL
);

-- ============================================================
-- 2. 用户表 (accounts)
-- ============================================================

CREATE TABLE `user` (
    `id` bigint AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `password` varchar(128) COMMENT '密码哈希' NOT NULL,
    `last_login` datetime(6) COMMENT '最后登录时间' NULL,
    `is_superuser` bool COMMENT '是否为超级管理员' NOT NULL,
    `username` varchar(150) COMMENT '用户名' NOT NULL UNIQUE,
    `first_name` varchar(150) COMMENT '名' NOT NULL,
    `last_name` varchar(150) COMMENT '姓' NOT NULL,
    `email` varchar(254) COMMENT '邮箱' NOT NULL,
    `is_staff` bool COMMENT '是否可以登录后台' NOT NULL,
    `is_active` bool COMMENT '是否启用' NOT NULL,
    `date_joined` datetime(6) COMMENT '注册时间' NOT NULL,
    `avatar` varchar(100) COMMENT '用户头像' NULL
);
ALTER TABLE `user` COMMENT = '用户信息';

CREATE TABLE `user_groups` (
    `id` bigint AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `user_id` bigint NOT NULL,
    `group_id` integer NOT NULL
);

CREATE TABLE `user_user_permissions` (
    `id` bigint AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `user_id` bigint NOT NULL,
    `permission_id` integer NOT NULL
);

-- ============================================================
-- 3. 景点表 (travel)
-- ============================================================

CREATE TABLE `attraction` (
    `id` bigint AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `poi_id` bigint COMMENT '景点唯一标识' NOT NULL UNIQUE,
    `area` varchar(100) COMMENT '所在区域' NULL,
    `name` varchar(120) COMMENT '景点名称' NOT NULL,
    `comment_count` double precision COMMENT '评论数量' NULL,
    `score` double precision COMMENT '评分' NOT NULL,
    `is_advertisement` bool COMMENT '是否为广告内容' NOT NULL,
    `is_recommend` bool COMMENT '是否被推荐' NOT NULL,
    `city_name` varchar(50) COMMENT '城市名称' NOT NULL,
    `image` varchar(500) COMMENT '图片' NULL,
    `distance` varchar(50) COMMENT '与市中心的距离' NULL,
    `tags` varchar(120) COMMENT '标签' NULL,
    `detail_url` varchar(500) COMMENT '详情页链接' NOT NULL,
    `market_price` double precision COMMENT '市场票价' NULL,
    `preferential_price` double precision COMMENT '优惠价格' NULL,
    `preferential_desc` varchar(50) COMMENT '优惠描述' NULL,
    `actual_price` varchar(50) COMMENT '实际票价' NOT NULL,
    `price_type` integer COMMENT '价格类型' NULL,
    `price_type_desc` varchar(50) COMMENT '价格类型描述' NULL,
    `is_free` bool COMMENT '是否免费' NOT NULL,
    `longitude` double precision COMMENT '经度' NOT NULL,
    `latitude` double precision COMMENT '纬度' NOT NULL,
    `heat_score` double precision COMMENT '热度评分' NULL
);
ALTER TABLE `attraction` COMMENT = '旅游景点信息';
CREATE INDEX `idx_attraction_city` ON `attraction` (`city_name`);
CREATE INDEX `idx_attraction_name` ON `attraction` (`name`);
CREATE INDEX `idx_attraction_score` ON `attraction` (`score`);

CREATE TABLE `attraction_favorite` (
    `id` bigint AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `created_at` datetime(6) COMMENT '收藏时间' NOT NULL,
    `attraction_id` bigint COMMENT '收藏景点' NOT NULL,
    `user_id` bigint COMMENT '收藏用户' NOT NULL
);
ALTER TABLE `attraction_favorite` COMMENT = '景点收藏';

CREATE TABLE `attraction_comment` (
    `id` bigint AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `content` longtext COMMENT '评论内容' NOT NULL,
    `created_at` datetime(6) COMMENT '评论时间' NOT NULL,
    `attraction_id` bigint COMMENT '评论景点' NOT NULL,
    `user_id` bigint COMMENT '评论用户' NOT NULL
);
ALTER TABLE `attraction_comment` COMMENT = '景点评论';

-- ============================================================
-- 4. 旅游攻略表 (guides)
-- ============================================================

CREATE TABLE `travel_guide` (
    `id` bigint AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `title` varchar(120) COMMENT '攻略标题' NOT NULL,
    `city` varchar(50) COMMENT '目的地城市' NOT NULL,
    `summary` varchar(240) COMMENT '攻略摘要' NOT NULL,
    `content` longtext COMMENT '攻略正文' NOT NULL,
    `view_count` integer UNSIGNED COMMENT '浏览量' NOT NULL CHECK (`view_count` >= 0),
    `created_at` datetime(6) COMMENT '发布时间' NOT NULL,
    `updated_at` datetime(6) COMMENT '更新时间' NOT NULL,
    `author_id` bigint COMMENT '攻略作者' NOT NULL
);
ALTER TABLE `travel_guide` COMMENT = '旅游攻略';
CREATE INDEX `idx_guide_city_time` ON `travel_guide` (`city`, `created_at` DESC);
CREATE INDEX `idx_guide_author_time` ON `travel_guide` (`author_id`, `created_at` DESC);
CREATE INDEX `idx_guide_created_time` ON `travel_guide` (`created_at` DESC);

CREATE TABLE `travel_guide_image` (
    `id` bigint AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `image` varchar(255) COMMENT '攻略图片' NOT NULL,
    `sort_order` smallint UNSIGNED COMMENT '排序序号' NOT NULL CHECK (`sort_order` >= 0),
    `created_at` datetime(6) COMMENT '上传时间' NOT NULL,
    `guide_id` bigint COMMENT '所属攻略' NOT NULL
);
ALTER TABLE `travel_guide_image` COMMENT = '旅游攻略图片';
CREATE INDEX `idx_guide_image_order` ON `travel_guide_image` (`guide_id`, `sort_order`);

CREATE TABLE `travel_guide_attraction` (
    `id` bigint AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `created_at` datetime(6) COMMENT '关联时间' NOT NULL,
    `attraction_id` bigint COMMENT '关联景点' NOT NULL,
    `guide_id` bigint COMMENT '所属攻略' NOT NULL
);
ALTER TABLE `travel_guide_attraction` COMMENT = '旅游攻略关联景点';
CREATE INDEX `idx_guide_attr_guide` ON `travel_guide_attraction` (`guide_id`);
CREATE INDEX `idx_guide_attr_spot` ON `travel_guide_attraction` (`attraction_id`);

-- ============================================================
-- 5. AI路线规划表 (planner)
-- ============================================================

CREATE TABLE `route_plan` (
    `id` bigint AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `city` varchar(50) COMMENT '目的地城市' NOT NULL,
    `budget` varchar(80) COMMENT '用户输入的旅行预算' NOT NULL,
    `travel_time` varchar(80) COMMENT '用户输入的出行时间' NOT NULL,
    `preferences` varchar(300) COMMENT '用户输入的旅行偏好' NOT NULL,
    `intent_data` json COMMENT 'AI 识别出的结构化意图' NOT NULL,
    `process_steps` json COMMENT 'LangGraph 规划过程步骤' NOT NULL,
    `final_plan` longtext COMMENT 'AI 生成的最终路线说明' NOT NULL,
    `status` varchar(20) COMMENT '规划任务状态' NOT NULL,
    `error_message` varchar(300) COMMENT '规划失败原因' NOT NULL,
    `created_at` datetime(6) COMMENT '创建时间' NOT NULL,
    `user_id` bigint COMMENT '提交规划的用户' NOT NULL
);
ALTER TABLE `route_plan` COMMENT = 'AI 路线规划结果';
CREATE INDEX `idx_route_plan_user_time` ON `route_plan` (`user_id`, `created_at` DESC);
CREATE INDEX `idx_route_plan_city` ON `route_plan` (`city`);

CREATE TABLE `route_plan_stop` (
    `id` bigint AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `day_index` smallint UNSIGNED COMMENT '第几天' NOT NULL CHECK (`day_index` >= 0),
    `sequence` smallint UNSIGNED COMMENT '当天第几个' NOT NULL CHECK (`sequence` >= 0),
    `name` varchar(120) COMMENT '景点名称' NOT NULL,
    `city_name` varchar(50) COMMENT '城市名称' NOT NULL,
    `longitude` double precision COMMENT '经度' NOT NULL,
    `latitude` double precision COMMENT '纬度' NOT NULL,
    `intro` longtext COMMENT '站点介绍' NOT NULL,
    `created_at` datetime(6) COMMENT '创建时间' NOT NULL,
    `attraction_id` bigint COMMENT '关联景点' NULL,
    `plan_id` bigint COMMENT '所属路线规划' NOT NULL
);
ALTER TABLE `route_plan_stop` COMMENT = 'AI 路线规划站点';
CREATE INDEX `idx_route_stop_plan_day_seq` ON `route_plan_stop` (`plan_id`, `day_index`, `sequence`);

-- ============================================================
-- 6. django_admin_log (依赖 user 表)
-- ============================================================

CREATE TABLE `django_admin_log` (
    `id` int AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `action_time` datetime(6) NOT NULL,
    `object_id` longtext NULL,
    `object_repr` varchar(200) NOT NULL,
    `action_flag` smallint UNSIGNED NOT NULL CHECK (`action_flag` >= 0),
    `change_message` longtext NOT NULL,
    `content_type_id` int NULL,
    `user_id` bigint NOT NULL
);

-- ============================================================
-- 7. 所有外键约束
-- ============================================================

ALTER TABLE `django_content_type` ADD CONSTRAINT `django_content_type_app_label_model` UNIQUE (`app_label`, `model`);
ALTER TABLE `auth_permission` ADD CONSTRAINT `auth_permission_content_type_id_codename` UNIQUE (`content_type_id`, `codename`);
ALTER TABLE `auth_permission` ADD CONSTRAINT `auth_permission_content_type_fk` FOREIGN KEY (`content_type_id`) REFERENCES `django_content_type` (`id`);
ALTER TABLE `auth_group_permissions` ADD CONSTRAINT `auth_group_permissions_group_id_permission_id` UNIQUE (`group_id`, `permission_id`);
ALTER TABLE `auth_group_permissions` ADD CONSTRAINT `auth_group_permissions_group_fk` FOREIGN KEY (`group_id`) REFERENCES `auth_group` (`id`);
ALTER TABLE `auth_group_permissions` ADD CONSTRAINT `auth_group_permissions_permission_fk` FOREIGN KEY (`permission_id`) REFERENCES `auth_permission` (`id`);

ALTER TABLE `user_groups` ADD CONSTRAINT `user_groups_user_id_group_id_40beef00_uniq` UNIQUE (`user_id`, `group_id`);
ALTER TABLE `user_groups` ADD CONSTRAINT `user_groups_user_id_abaea130_fk_user_id` FOREIGN KEY (`user_id`) REFERENCES `user` (`id`);
ALTER TABLE `user_groups` ADD CONSTRAINT `user_groups_group_id_b76f8aba_fk_auth_group_id` FOREIGN KEY (`group_id`) REFERENCES `auth_group` (`id`);
ALTER TABLE `user_user_permissions` ADD CONSTRAINT `user_user_permissions_user_id_permission_id_7dc6e2e0_uniq` UNIQUE (`user_id`, `permission_id`);
ALTER TABLE `user_user_permissions` ADD CONSTRAINT `user_user_permissions_user_id_ed4a47ea_fk_user_id` FOREIGN KEY (`user_id`) REFERENCES `user` (`id`);
ALTER TABLE `user_user_permissions` ADD CONSTRAINT `user_user_permission_permission_id_9deb68a3_fk_auth_perm` FOREIGN KEY (`permission_id`) REFERENCES `auth_permission` (`id`);

ALTER TABLE `attraction_favorite` ADD CONSTRAINT `uniq_user_attraction_favorite` UNIQUE (`user_id`, `attraction_id`);
ALTER TABLE `attraction_favorite` ADD CONSTRAINT `attraction_favorite_attraction_id_1c3f933f_fk_attraction_id` FOREIGN KEY (`attraction_id`) REFERENCES `attraction` (`id`);
ALTER TABLE `attraction_favorite` ADD CONSTRAINT `attraction_favorite_user_id_1c3f933f_fk_user_id` FOREIGN KEY (`user_id`) REFERENCES `user` (`id`);
ALTER TABLE `attraction_comment` ADD CONSTRAINT `attraction_comment_attraction_id_fk` FOREIGN KEY (`attraction_id`) REFERENCES `attraction` (`id`);
ALTER TABLE `attraction_comment` ADD CONSTRAINT `attraction_comment_user_id_fk` FOREIGN KEY (`user_id`) REFERENCES `user` (`id`);

ALTER TABLE `travel_guide` ADD CONSTRAINT `travel_guide_author_id_3dd1590f_fk_user_id` FOREIGN KEY (`author_id`) REFERENCES `user` (`id`);
ALTER TABLE `travel_guide_image` ADD CONSTRAINT `travel_guide_image_guide_id_db6b3d1a_fk_travel_guide_id` FOREIGN KEY (`guide_id`) REFERENCES `travel_guide` (`id`);
ALTER TABLE `travel_guide_attraction` ADD CONSTRAINT `uniq_guide_attraction` UNIQUE (`guide_id`, `attraction_id`);
ALTER TABLE `travel_guide_attraction` ADD CONSTRAINT `travel_guide_attraction_attraction_id_dabea788_fk_attraction_id` FOREIGN KEY (`attraction_id`) REFERENCES `attraction` (`id`);
ALTER TABLE `travel_guide_attraction` ADD CONSTRAINT `travel_guide_attraction_guide_id_5ebf50bc_fk_travel_guide_id` FOREIGN KEY (`guide_id`) REFERENCES `travel_guide` (`id`);

ALTER TABLE `route_plan` ADD CONSTRAINT `route_plan_user_id_21c346c9_fk_user_id` FOREIGN KEY (`user_id`) REFERENCES `user` (`id`);
ALTER TABLE `route_plan_stop` ADD CONSTRAINT `route_plan_stop_attraction_id_91500280_fk_attraction_id` FOREIGN KEY (`attraction_id`) REFERENCES `attraction` (`id`);
ALTER TABLE `route_plan_stop` ADD CONSTRAINT `route_plan_stop_plan_id_92134d50_fk_route_plan_id` FOREIGN KEY (`plan_id`) REFERENCES `route_plan` (`id`);

ALTER TABLE `django_admin_log` ADD CONSTRAINT `django_admin_log_content_type_fk` FOREIGN KEY (`content_type_id`) REFERENCES `django_content_type` (`id`);
ALTER TABLE `django_admin_log` ADD CONSTRAINT `django_admin_log_user_fk` FOREIGN KEY (`user_id`) REFERENCES `user` (`id`);
CREATE INDEX `django_session_expire_date` ON `django_session` (`expire_date`);

SET FOREIGN_KEY_CHECKS = 1;

-- ============================================================
-- 8. Django 迁移记录（标记所有迁移已执行）
-- ============================================================

INSERT INTO `django_migrations` (`app`, `name`, `applied`) VALUES
    ('contenttypes', '0001_initial', NOW()),
    ('contenttypes', '0002_remove_content_type_name', NOW()),
    ('auth', '0001_initial', NOW()),
    ('auth', '0002_alter_permission_name_max_length', NOW()),
    ('auth', '0003_alter_user_email_max_length', NOW()),
    ('auth', '0004_alter_user_username_opts', NOW()),
    ('auth', '0005_alter_user_username_max_length', NOW()),
    ('auth', '0006_require_contenttypes_0002', NOW()),
    ('auth', '0007_alter_validators_add_alter_javascript', NOW()),
    ('auth', '0008_alter_user_username_max_length', NOW()),
    ('auth', '0009_alter_user_last_name_max_length', NOW()),
    ('auth', '0010_alter_group_name_max_length', NOW()),
    ('auth', '0011_update_proxy_permissions', NOW()),
    ('auth', '0012_alter_user_first_name_max_length', NOW()),
    ('admin', '0001_initial', NOW()),
    ('admin', '0002_logentry_remove_auto_add', NOW()),
    ('admin', '0003_logentry_add_action_flag_choices', NOW()),
    ('sessions', '0001_initial', NOW()),
    ('accounts', '0001_initial', NOW()),
    ('travel', '0001_initial', NOW()),
    ('guides', '0001_initial', NOW()),
    ('planner', '0001_initial', NOW());

-- ============================================================
-- 完成! 数据库已初始化。
-- 超级管理员请通过 Django 命令创建:
--   python manage.py createsuperuser
-- ============================================================