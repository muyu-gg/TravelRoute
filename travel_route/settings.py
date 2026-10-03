"""功能说明：觅途行 - 旅游规划系统 Django 配置。"""
import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent


def load_local_env(env_path: Path) -> None:
    """功能说明：读取项目根目录 .env 文件并写入系统环境变量。"""
    # .env 文件不存在时直接跳过，保持原有环境变量读取方式。
    if not env_path.exists():
        return

    # 按行读取 .env 内容，忽略空行、注释和不合法配置。
    for raw_line in env_path.read_text(encoding='utf-8').splitlines():
        line = raw_line.strip()
        if not line or line.startswith('#') or '=' not in line:
            continue

        # 拆分键值并去除常见引号，避免覆盖系统中已经配置的环境变量。
        key, value = line.split('=', 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


load_local_env(BASE_DIR / '.env')

SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', 'django-insecure-travel-route-dev-key')
DEBUG = True
ALLOWED_HOSTS = os.getenv('DJANGO_ALLOWED_HOSTS', '127.0.0.1,localhost').split(',')

INSTALLED_APPS = [
    'simpleui',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'accounts',
    'travel',
    'guides',
    'planner',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'travel_route.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'travel_route.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': os.getenv('MYSQL_DATABASE', 'travel_route_base'),
        'USER': os.getenv('MYSQL_USER', 'root'),
        'PASSWORD': os.getenv('MYSQL_PASSWORD', '123456'),
        'HOST': os.getenv('MYSQL_HOST', '127.0.0.1'),
        'PORT': os.getenv('MYSQL_PORT', '3306'),
        'OPTIONS': {
            'charset': 'utf8mb4',
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
        },
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 6,
        },
    },
]

LANGUAGE_CODE = 'zh-hans'
TIME_ZONE = 'Asia/Shanghai'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'static']

MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
AUTH_USER_MODEL = 'accounts.User'
LOGIN_URL = 'accounts:login'
LOGIN_REDIRECT_URL = 'accounts:home'
LOGOUT_REDIRECT_URL = 'accounts:login'

# SimpleUI 后台界面配置。
SIMPLEUI_LOGO = '/static/img/admin-logo.svg'
SIMPLEUI_HOME_INFO = False
SIMPLEUI_ANALYSIS = False
SIMPLEUI_HOME_QUICK = True
SIMPLEUI_HOME_ACTION = True
SIMPLEUI_CONFIG = {
    'system_keep': False,
    'menu_display': ['景点数据', '攻略管理', 'AI路线规划', '账号权限'],
    'menus': [
        {
            'name': '景点数据',
            'icon': 'fas fa-map-marker-alt',
            'models': [
                {
                    'name': '旅游景点信息',
                    'icon': 'fas fa-mountain',
                    'url': '/admin/travel/attraction/',
                },
                {
                    'name': '景点收藏',
                    'icon': 'fas fa-heart',
                    'url': '/admin/travel/attractionfavorite/',
                },
                {
                    'name': '景点评论',
                    'icon': 'fas fa-comment',
                    'url': '/admin/travel/attractioncomment/',
                },
            ],
        },
        {
            'name': '攻略管理',
            'icon': 'fas fa-book-open',
            'models': [
                {
                    'name': '旅游攻略',
                    'icon': 'fas fa-file-alt',
                    'url': '/admin/guides/travelguide/',
                },
                {
                    'name': '攻略图片',
                    'icon': 'fas fa-image',
                    'url': '/admin/guides/travelguideimage/',
                },
                {
                    'name': '攻略关联景点',
                    'icon': 'fas fa-link',
                    'url': '/admin/guides/travelguideattraction/',
                },
            ],
        },
        {
            'name': 'AI路线规划',
            'icon': 'fas fa-route',
            'models': [
                {
                    'name': '路线规划结果',
                    'icon': 'fas fa-project-diagram',
                    'url': '/admin/planner/routeplan/',
                },
                {
                    'name': '路线规划站点',
                    'icon': 'fas fa-map-pin',
                    'url': '/admin/planner/routeplanstop/',
                },
            ],
        },
        {
            'name': '账号权限',
            'icon': 'fas fa-user-shield',
            'models': [
                {
                    'name': '用户信息',
                    'icon': 'far fa-user',
                    'url': '/admin/accounts/user/',
                },
                {
                    'name': '用户组',
                    'icon': 'fas fa-users-cog',
                    'url': '/admin/auth/group/',
                },
            ],
        },
    ],
}

DEEPSEEK_API_KEY = os.getenv('DEEPSEEK_API_KEY', '')
DEEPSEEK_BASE_URL = os.getenv('DEEPSEEK_BASE_URL', 'https://api.deepseek.com')
DEEPSEEK_MODEL = os.getenv('DEEPSEEK_MODEL', 'deepseek-chat')

AMAP_WEB_KEY = os.getenv('gaodeMap', '')

CSRF_TRUSTED_ORIGINS = ["http://127.0.0.1:8000", "http://localhost:8000"]

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'planner.agent.tools': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}