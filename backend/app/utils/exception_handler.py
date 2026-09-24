from rest_framework.response import Response
from rest_framework.views import exception_handler as drf_exception_handler
from app.constants.errors import ERROR_MESSAGES
from app.utils.logger import get_logger

logger = get_logger('exception')


class BusinessError(Exception):
    """业务异常：由自定义异常处理器转换为标准响应。"""

    def __init__(self, code: str, status_code: int = 400, data=None):
        self.code = code
        self.message = ERROR_MESSAGES.get(code, code)
        self.status_code = status_code
        self.data = data
        super().__init__(self.message)


def standard_exception_handler(exc, context):
    if isinstance(exc, BusinessError):
        logger.info('业务异常 %s: %s', exc.code, exc.message)
        return Response(
            {'success': False, 'code': exc.code, 'message': exc.message, 'data': exc.data},
            status=exc.status_code,
        )

    response = drf_exception_handler(exc, context)
    if response is None:
        return response
    response.data = {'success': False, 'code': response.status_code, 'data': None, 'error': response.data}
    return response
