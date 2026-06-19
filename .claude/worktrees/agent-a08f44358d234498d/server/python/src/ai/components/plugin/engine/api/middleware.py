# """
# API中间件模块
# 提供请求处理、错误处理、认证等中间件功能
# """

# import time
# from typing import Callable

# from fastapi import FastAPI, Request, HTTPException
# from fastapi.middleware.gzip import GZipMiddleware
# from fastapi.responses import JSONResponse
# from loguru import logger
# from starlette.middleware.base import BaseHTTPMiddleware

# from ai.components.plugin.engine.config.settings import settings
# from ai.components.plugin.engine.models.request import ErrorResponse


# class LoggingMiddleware(BaseHTTPMiddleware):
#     """请求日志中间件"""

#     async def dispatch(self, request: Request, call_next: Callable):
#         start_time = time.time()

#         # 记录请求开始
#         logger.info(f"请求开始: {request.method} {request.url}")

#         try:
#             response = await call_next(request)

#             # 记录请求完成
#             process_time = time.time() - start_time
#             logger.info(
#                 f"请求完成: {request.method} {request.url} 状态码: {response.status_code} 耗时: {process_time:.3f}s"
#             )

#             # 添加处理时间到响应头
#             response.headers["X-Process-Time"] = str(process_time)

#             return response

#         except Exception as e:
#             process_time = time.time() - start_time
#             logger.error(f"请求异常: {request.method} {request.url} 错误: {str(e)} 耗时: {process_time:.3f}s")
#             raise


# class ErrorHandlingMiddleware(BaseHTTPMiddleware):
#     """错误处理中间件"""

#     async def dispatch(self, request: Request, call_next: Callable):
#         try:
#             return await call_next(request)
#         except HTTPException:
#             # 让FastAPI处理HTTP异常
#             raise
#         except Exception as e:
#             logger.exception(f"未处理的异常: {e}")

#             # 返回标准化错误响应
#             error_response = ErrorResponse(
#                 error="内部服务器错误",
#                 error_code="INTERNAL_SERVER_ERROR",
#                 detail={"message": str(e)} if settings.debug else None,
#             )

#             return JSONResponse(status_code=500, content=error_response.model_dump())


# class SecurityMiddleware(BaseHTTPMiddleware):
#     """安全中间件"""

#     async def dispatch(self, request: Request, call_next: Callable):
#         # 添加安全头
#         response = await call_next(request)

#         # 安全头设置
#         response.headers["X-Content-Type-Options"] = "nosniff"
#         response.headers["X-Frame-Options"] = "DENY"
#         response.headers["X-XSS-Protection"] = "1; mode=block"
#         response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

#         if not settings.debug:
#             response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

#         return response


# class RateLimitMiddleware(BaseHTTPMiddleware):
#     """限流中间件（简单实现）"""

#     def __init__(self, app, calls: int = 100, period: int = 60):
#         super().__init__(app)
#         self.calls = calls
#         self.period = period
#         self.clients = {}

#     async def dispatch(self, request: Request, call_next: Callable):
#         # 在测试环境下跳过限流
#         if settings.testing or settings.debug:
#             return await call_next(request)

#         client_ip = request.client.host
#         current_time = time.time()

#         # 清理过期记录
#         for ip in list(self.clients.keys()):
#             # 过滤掉过期的时间戳
#             self.clients[ip] = [t for t in self.clients[ip] if current_time - t < self.period]
#             if not self.clients[ip]:
#                 del self.clients[ip]

#         # 检查限流
#         if client_ip in self.clients:
#             call_times = self.clients[client_ip]
#             if len(call_times) >= self.calls:
#                 return JSONResponse(status_code=429, content={"error": "请求过于频繁，请稍后再试"})
#             call_times.append(current_time)
#         else:
#             self.clients[client_ip] = [current_time]

#         return await call_next(request)


# def setup_middleware(app: FastAPI):
#     """设置所有中间件"""

#     # 压缩中间件
#     app.add_middleware(GZipMiddleware, minimum_size=1000)

#     # 安全中间件
#     app.add_middleware(SecurityMiddleware)

#     # 错误处理中间件
#     app.add_middleware(ErrorHandlingMiddleware)

#     # 请求日志中间件
#     app.add_middleware(LoggingMiddleware)

#     # 限流中间件（仅在生产环境且未禁用时启用）
#     if settings.is_production() and settings.enable_rate_limiting and not settings.testing and not settings.debug:
#         app.add_middleware(RateLimitMiddleware, calls=100, period=60)

#     logger.info("中间件设置完成")
