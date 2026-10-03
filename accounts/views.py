"""功能说明：账号登录、注册、首页和个人中心视图。"""
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth import login as auth_login
from django.contrib.auth import logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.utils.http import url_has_allowed_host_and_scheme


def home_view(request: HttpRequest) -> HttpResponse:
    """功能说明：渲染登录后的系统首页，展示轮播图和推荐景点。"""
    if not request.user.is_authenticated:
        return redirect('accounts:login')

    from travel.models import Attraction
    from guides.models import TravelGuide

    carousel_attractions = Attraction.objects.filter(
        is_recommend=True, is_advertisement=False
    ).order_by('-heat_score', '-score')[:5]

    if carousel_attractions.count() < 3:
        extra_count = 3 - carousel_attractions.count()
        existing_ids = [a.id for a in carousel_attractions]
        extra_items = Attraction.objects.filter(
            is_advertisement=False
        ).exclude(pk__in=existing_ids).order_by('-heat_score', '-score')[:extra_count]
        carousel_attractions = list(carousel_attractions) + list(extra_items)

    recommended_attractions = list(
        Attraction.objects.filter(
            is_recommend=True, is_advertisement=False
        ).order_by('-score', '-comment_count')[:8]
    )

    if len(recommended_attractions) < 8:
        remaining = 8 - len(recommended_attractions)
        extra_ids = [a.id for a in recommended_attractions]
        extra_attractions = Attraction.objects.filter(
            is_advertisement=False
        ).exclude(pk__in=extra_ids).order_by('-score', '-comment_count')[:remaining]
        recommended_attractions = recommended_attractions + list(extra_attractions)

    recent_guides = TravelGuide.objects.select_related('author').order_by('-created_at')[:4]

    return render(
        request,
        'accounts/home.html',
        {
            'carousel_attractions': carousel_attractions,
            'recommended_attractions': recommended_attractions,
            'recent_guides': recent_guides,
        },
    )


def login_view(request: HttpRequest) -> HttpResponse:
    """功能说明：处理用户登录页面展示和登录提交。"""
    # 已登录用户直接进入首页。
    if request.user.is_authenticated:
        return redirect('accounts:home')

    # 准备模板上下文，保留安全的跳转地址。
    next_url = request.POST.get('next') or request.GET.get('next') or ''
    safe_next_url = ''
    if url_has_allowed_host_and_scheme(next_url, {request.get_host()}, request.is_secure()):
        safe_next_url = next_url
    context = {'error': '', 'username': '', 'next': safe_next_url}

    # GET 请求直接展示登录页面。
    if request.method != 'POST':
        return render(request, 'accounts/login.html', context)

    # 读取账号密码并执行基础校验。
    username = request.POST.get('username', '').strip()
    password = request.POST.get('password', '')
    context['username'] = username
    if not username or not password:
        context['error'] = '请输入用户名和密码。'
        return render(request, 'accounts/login.html', context)

    # 使用 Django 认证后端校验用户身份。
    user = authenticate(request, username=username, password=password)
    if user is None:
        context['error'] = '用户名或密码错误。'
        return render(request, 'accounts/login.html', context)

    # 写入登录会话并跳转到目标页面。
    auth_login(request, user)
    if safe_next_url:
        return redirect(safe_next_url)
    return redirect('accounts:home')


def register_view(request: HttpRequest) -> HttpResponse:
    """功能说明：处理用户注册页面展示和注册提交。"""
    # 已登录用户直接进入首页。
    if request.user.is_authenticated:
        return redirect('accounts:home')

    # 准备模板上下文，用于回显用户已输入的数据。
    context = {'errors': [], 'username': ''}
    if request.method != 'POST':
        return render(request, 'accounts/register.html', context)

    # 从 POST 中读取注册数据。
    user_model = get_user_model()
    username = request.POST.get('username', '').strip()
    password = request.POST.get('password', '')
    password_confirm = request.POST.get('password_confirm', '')
    errors = []
    context.update({'username': username})

    # 校验用户名和密码的基础规则。
    if not username:
        errors.append('请输入用户名。')
    elif user_model.objects.filter(username=username).exists():
        errors.append('用户名已存在。')
    if not password:
        errors.append('请输入密码。')
    if password != password_confirm:
        errors.append('两次输入的密码不一致。')

    # 调用 Django 密码校验器，只校验密码长度不少于 6 位。
    if password and password == password_confirm:
        temporary_user = user_model(username=username)
        try:
            validate_password(password, temporary_user)
        except ValidationError as exc:
            errors.extend(exc.messages)

    # 存在错误时返回注册页面并展示错误信息。
    if errors:
        context['errors'] = errors
        return render(request, 'accounts/register.html', context)

    # 创建用户账号。
    user = user_model.objects.create_user(username=username, password=password)

    # 注册成功后自动登录并进入首页。
    auth_login(request, user)
    return redirect('accounts:home')


def logout_view(request: HttpRequest) -> HttpResponse:
    """功能说明：退出当前登录用户并返回登录页。"""
    auth_logout(request)
    return redirect('accounts:login')


@login_required
def profile_view(request: HttpRequest) -> HttpResponse:
    """功能说明：展示和编辑当前用户的个人资料。"""
    user = request.user

    if request.method != 'POST':
        return render(request, 'accounts/profile.html', {'user': user})

    username = request.POST.get('username', '').strip()
    avatar = request.FILES.get('avatar')

    errors = []
    user_model = get_user_model()
    if username and username != user.username:
        if user_model.objects.filter(username=username).exclude(pk=user.pk).exists():
            errors.append('用户名已被其他用户使用。')
        else:
            user.username = username

    if avatar:
        user.avatar = avatar

    if errors:
        return render(request, 'accounts/profile.html', {'user': user, 'errors': errors})

    user.save()
    return render(request, 'accounts/profile.html', {'user': user, 'success': '资料更新成功。'})