    @staticmethod
    def _get_jwt_secret() -> str:
        """获取 JWT 密钥"""
        try:
            from demo.configs import settings
        except ImportError:
            from configs import settings
        return settings.iam.jwt.secret_key
