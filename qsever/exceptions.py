class QseverError(Exception):
    """Qsever 基础异常"""
    pass


class APIError(QseverError):
    """API 调用错误"""
    pass


class ModelNotAvailable(QseverError):
    """模型不可用"""
    pass


class ImageNotFound(QseverError):
    """图片文件未找到"""
    pass


class ConfigError(QseverError):
    """配置错误"""
    pass
