from dpkt.http import Request as DpktRequest
from werkzeug.test import EnvironBuilder
from werkzeug.wrappers import Request


def parse_raw_request(raw_data: bytes):
    """
    解析原始HTTP数据为Request对象

    将原始的HTTP字节数据解析成可用的Request对象，便于后续处理

    Args:
        raw_data: 原始HTTP数据（字节类型）

    Returns:
        Request: 解析后的请求对象
    """
    req = DpktRequest(raw_data)
    builder = EnvironBuilder(
        method=req.method,
        path=req.uri,
        headers=req.headers,
        data=req.body,
    )
    return Request(builder.get_environ())


def convert_request_to_raw_data(request: Request) -> bytes:
    """
    将Request对象转换为原始HTTP数据

    将Request对象序列化为原始的HTTP字节数据格式

    Args:
        request: 要转换的Request对象

    Returns:
        bytes: 原始HTTP数据（字节类型）
    """
    # 开始构建请求行
    method = request.method
    path = request.path
    protocol = request.headers.get("HTTP_VERSION", "HTTP/1.1")
    raw_data = f"{method} {path} {protocol}\r\n".encode()

    # 添加请求头
    for header_name, header_value in request.headers.items():
        raw_data += f"{header_name}: {header_value}\r\n".encode()

    # 添加空行分隔请求头和请求体
    raw_data += b"\r\n"

    # 如果存在请求体则添加
    body = request.get_data(as_text=False)
    if body:
        raw_data += body

    return raw_data
