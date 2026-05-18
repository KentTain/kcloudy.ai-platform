//! 错误处理单元测试

use demo::common::error::{Error, ApiResponse};

#[test]
fn test_error_display() {
    let err = Error::NotFound("测试资源".to_string());
    assert_eq!(format!("{}", err), "资源未找到: 测试资源");

    let err = Error::Validation("名称不能为空".to_string());
    assert_eq!(format!("{}", err), "验证错误: 名称不能为空");
}

#[test]
fn test_api_response_success() {
    let response = ApiResponse::success("test data");
    assert_eq!(response.code, 200);
    assert_eq!(response.msg, "success");
    assert_eq!(response.data, Some("test data"));
}

#[test]
fn test_api_response_error() {
    let response: ApiResponse<()> = ApiResponse::error(404, "未找到".to_string());
    assert_eq!(response.code, 404);
    assert_eq!(response.msg, "未找到");
    assert!(response.data.is_none());
}
