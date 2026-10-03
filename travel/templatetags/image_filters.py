import re

from django import template

register = template.Library()

_CTRIP_SIZE_RE = re.compile(r'(_[CRW])_(\d+)_(\d+)(\.\w+)')


@register.filter(name='hd')
def ctrip_hd(url, size='800_600'):
    """将携程 CDN 图片 URL 中的缩略图尺寸替换为高清尺寸。

    用法：
        {{ attraction.image|hd }}              → 800×600
        {{ attraction.image|hd:"600_400" }}    → 600×400
        {{ attraction.image|hd:"1200_800" }}   → 1200×800

    携程 CDN 尺寸前缀说明：
        _C  = 居中裁剪 (Crop)
        _R  = 等比缩放 (Resize)
        _W  = 带水印 (Watermark)

    默认使用 _R（等比缩放），避免裁剪导致画面不完整。
    """
    if not url:
        return url

    w, h = size.split('_')

    match = _CTRIP_SIZE_RE.search(url)
    if match:
        url = url[:match.start()] + f'_R_{w}_{h}{match.group(4)}' + url[match.end():]
    else:
        if '_C_' not in url and '_R_' not in url and '_W_' not in url:
            name_dot = url.rfind('.')
            if name_dot > 0:
                qmark = url.find('?', name_dot)
                if qmark > 0:
                    url = url[:name_dot] + f'_R_{w}_{h}' + url[name_dot:]
                else:
                    url = url[:name_dot] + f'_R_{w}_{h}' + url[name_dot:]

    return url


@register.filter(name='banner_hd')
def ctrip_banner_hd(url, size='1200_800'):
    """banner 专用高清滤镜，默认 1200×800 宽幅。

    携程 CDN 支持的尺寸：220_140, 300_200, 400_300, 600_400,
    800_600, 960_540, 1200_800 等。不支持 1200_600、1000_700。
    """
    return ctrip_hd(url, size)