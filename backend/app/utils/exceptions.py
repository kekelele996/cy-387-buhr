class AppError(Exception):
    """业务异常：由 DRF 自定义异常处理器统一包装为标准响应。"""

    def __init__(self, code, message, status_code=400, extra=None):
        self.code = code
        self.message = message
        self.status_code = status_code
        self.extra = extra or {}
        super().__init__(message)
