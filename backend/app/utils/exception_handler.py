from rest_framework.response import Response
from rest_framework.views import exception_handler

from app.constants.errors import ERROR_CODES
from app.utils.exceptions import AppError
from app.utils.logger import get_logger

logger = get_logger('request')


def _as_message(error):
    """把 DRF 校验错误（list/dict/str）折叠为一条可读消息。"""
    if isinstance(error, list) and error:
        return _as_message(error[0])
    if isinstance(error, dict) and error:
        return _as_message(next(iter(error.values())))
    return str(error)


def standard_exception_handler(exc, context):
    if isinstance(exc, AppError):
        logger.info('续租业务异常 code=%s message=%s', exc.code, exc.message)
        return Response(
            {
                'success': False,
                'code': ERROR_CODES.get(exc.code, exc.code),
                'message': exc.message,
                'data': None,
                **exc.extra,
            },
            status=exc.status_code,
        )

    response = exception_handler(exc, context)
    if response is None:
        return response
    message = _as_message(response.data)
    response.data = {'success': False, 'code': response.status_code, 'message': message, 'data': None}
    return response
