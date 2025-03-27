class APIError(Exception):
    """TikTok API固有のエラー"""
    def __init__(self, message, status_code=None, error_code=None):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        super().__init__(self.message) 