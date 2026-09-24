"""从请求头解析当前操作人的角色和姓名。

HTTP 头只能携带 Latin-1 字符，故角色用 ASCII 编码（tenant/landlord），
姓名用百分号编码（encodeURIComponent）。本系统 JWT 鉴权未接入前端演示，
用这两个请求头模拟登录身份。
"""

from urllib.parse import unquote

from app.constants.enums import ROLE_LANDLORD, ROLE_TENANT
from app.utils.exception_handler import BusinessError

ROLE_HEADER_CODES = {
    'tenant': ROLE_TENANT,
    'landlord': ROLE_LANDLORD,
}


def get_actor(request):
    code = request.headers.get('X-User-Role', '').strip().lower()
    raw_name = request.headers.get('X-User-Name', '').strip()
    role = ROLE_HEADER_CODES.get(code)
    name = unquote(raw_name) if raw_name else ''
    if role is None or not name:
        raise BusinessError('RENEWAL_FORBIDDEN', data={'reason': '缺少 X-User-Role / X-User-Name 请求头'})
    return role, name
