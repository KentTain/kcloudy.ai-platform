# """
# 模型相关API路由
# 支持LLM、文本嵌入、重排序、TTS、语音转文本、内容审核等模型类型
# 与PluginModelClient的调用路径和参数保持一致
# """

# from typing import Any, Dict, Optional

# from fastapi import APIRouter, Header, HTTPException
# from loguru import logger
# from pydantic import BaseModel

# from ai.components.plugin.engine.core.plugin_manager import PluginManager
# from alon.core.common.encoder import jsonable_encoder


# router = APIRouter()

# # 全局插件管理器实例
# _plugin_manager: Optional[PluginManager] = None


# def get_plugin_manager() -> PluginManager:
#     """获取插件管理器实例"""
#     global _plugin_manager
#     if not _plugin_manager:
#         _plugin_manager = PluginManager()
#     return _plugin_manager


# # 通用数据包装器
# class DispatchRequest(BaseModel):
#     """插件调度请求包装器"""

#     user_id: str
#     data: Dict[str, Any]


# # 模型管理相关请求
# class ModelSchemaRequest(BaseModel):
#     """获取模型配置结构请求"""

#     user_id: str
#     data: Dict[str, Any]  # 包含provider, model_type, model, credentials


# class ProviderCredentialsRequest(BaseModel):
#     """验证提供者凭证请求"""

#     user_id: str
#     data: Dict[str, Any]  # 包含provider, credentials


# class ModelCredentialsRequest(BaseModel):
#     """验证模型凭证请求"""

#     user_id: str
#     data: Dict[str, Any]  # 包含provider, model_type, model, credentials


# # LLM相关请求
# class LLMInvokeRequest(BaseModel):
#     """LLM调用请求"""

#     user_id: str
#     data: Dict[str, Any]  # 包含provider, model_type, model, credentials, prompt_messages等


# class LLMTokensRequest(BaseModel):
#     """LLM Token计数请求"""

#     user_id: str
#     data: Dict[str, Any]  # 包含provider, model_type, model, credentials, prompt_messages等


# # 文本嵌入相关请求
# class TextEmbeddingInvokeRequest(BaseModel):
#     """文本嵌入调用请求"""

#     user_id: str
#     data: Dict[str, Any]  # 包含provider, model_type, model, credentials, texts, input_type


# class TextEmbeddingTokensRequest(BaseModel):
#     """文本嵌入Token计数请求"""

#     user_id: str
#     data: Dict[str, Any]  # 包含provider, model_type, model, credentials, texts


# # 重排序相关请求
# class RerankInvokeRequest(BaseModel):
#     """重排序调用请求"""

#     user_id: str
#     data: Dict[str, Any]  # 包含provider, model_type, model, credentials, query, docs等


# # TTS相关请求
# class TTSInvokeRequest(BaseModel):
#     """TTS调用请求"""

#     user_id: str
#     data: Dict[str, Any]  # 包含provider, model_type, model, credentials, content_text, voice等


# class TTSVoicesRequest(BaseModel):
#     """TTS声音列表请求"""

#     user_id: str
#     data: Dict[str, Any]  # 包含provider, model_type, model, credentials, language


# # 语音转文本相关请求
# class Speech2TextInvokeRequest(BaseModel):
#     """语音转文本调用请求"""

#     user_id: str
#     data: Dict[str, Any]  # 包含provider, model_type, model, credentials, file


# # 内容审核相关请求
# class ModerationInvokeRequest(BaseModel):
#     """内容审核调用请求"""

#     user_id: str
#     data: Dict[str, Any]  # 包含provider, model_type, model, credentials, text


# # ===== API路由实现 =====


# # 模型提供者管理API
# @router.get("/{tenant_id}/management/models")
# async def fetch_model_providers(tenant_id: str, page: int = 1, page_size: int = 256):
#     """获取租户的模型提供者列表"""
#     try:
#         manager = get_plugin_manager()

#         # 模拟模型提供者数据
#         providers = []
#         for plugin_name, plugin_info in manager.plugins.items():
#             if plugin_info.status == "running":
#                 providers.append(
#                     {
#                         "provider": plugin_name,
#                         "label": plugin_info.name,
#                         "description": plugin_info.description,
#                         "icon_small": None,
#                         "icon_large": None,
#                         "supported_model_types": [
#                             "llm",
#                             "text-embedding",
#                             "rerank",
#                             "tts",
#                             "speech2text",
#                             "moderation",
#                         ],
#                     }
#                 )

#         return {"data": providers, "total": len(providers), "page": page, "page_size": page_size}

#     except Exception as e:
#         logger.error(f"获取模型提供者失败: {e}")
#         raise HTTPException(status_code=500, detail=str(e))


# @router.post("/{tenant_id}/dispatch/model/schema")
# async def get_model_schema(
#     tenant_id: str, request: ModelSchemaRequest, x_plugin_id: str = Header(..., alias="X-Plugin-ID")
# ):
#     """获取模型配置结构"""
#     try:
#         manager = get_plugin_manager()

#         result = await manager.invoke_plugin(x_plugin_id, "get_model_schema", request.data)

#         return {"model_schema": result}

#     except Exception as e:
#         logger.error(f"获取模型配置结构失败: {e}")
#         raise HTTPException(status_code=500, detail=str(e))


# @router.post("/{tenant_id}/dispatch/model/validate_provider_credentials")
# async def validate_provider_credentials(
#     tenant_id: str, request: ProviderCredentialsRequest, x_plugin_id: str = Header(..., alias="X-Plugin-ID")
# ):
#     """验证提供者凭证"""
#     try:
#         manager = get_plugin_manager()

#         result = await manager.invoke_plugin(x_plugin_id, "validate_provider_credentials", request.data)

#         return {"result": result.get("result", False)}

#     except Exception as e:
#         logger.error(f"验证提供者凭证失败: {e}")
#         raise HTTPException(status_code=500, detail=str(e))


# @router.post("/{tenant_id}/dispatch/model/validate_model_credentials")
# async def validate_model_credentials(
#     tenant_id: str, request: ModelCredentialsRequest, x_plugin_id: str = Header(..., alias="X-Plugin-ID")
# ):
#     """验证模型凭证"""
#     try:
#         manager = get_plugin_manager()

#         result = await manager.invoke_plugin(x_plugin_id, "validate_model_credentials", request.data)

#         return {"result": result.get("result", False)}

#     except Exception as e:
#         logger.error(f"验证模型凭证失败: {e}")
#         raise HTTPException(status_code=500, detail=str(e))


# # LLM相关API
# @router.post("/{tenant_id}/dispatch/llm/invoke")
# async def invoke_llm(tenant_id: str, request: LLMInvokeRequest, x_plugin_id: str = Header(..., alias="X-Plugin-ID")):
#     """调用大语言模型"""
#     try:
#         manager = get_plugin_manager()

#         # 调用插件的LLM服务
#         for chunk in manager.invoke_plugin_stream(x_plugin_id, "invoke_llm", jsonable_encoder(request.data)):
#             yield chunk

#     except Exception as e:
#         logger.error(f"LLM调用失败: {e}")
#         raise HTTPException(status_code=500, detail=str(e))


# @router.post("/{tenant_id}/dispatch/llm/num_tokens")
# async def get_llm_num_tokens(
#     tenant_id: str, request: LLMTokensRequest, x_plugin_id: str = Header(..., alias="X-Plugin-ID")
# ):
#     """获取LLM Token数量"""
#     try:
#         manager = get_plugin_manager()

#         result = await manager.invoke_plugin(x_plugin_id, "get_llm_num_tokens", jsonable_encoder(request.data))

#         return {"num_tokens": result.get("num_tokens", 0)}

#     except Exception as e:
#         logger.error(f"获取LLM Token数量失败: {e}")
#         raise HTTPException(status_code=500, detail=str(e))


# # 文本嵌入相关API
# @router.post("/{tenant_id}/dispatch/text_embedding/invoke")
# async def invoke_text_embedding(
#     tenant_id: str, request: TextEmbeddingInvokeRequest, x_plugin_id: str = Header(..., alias="X-Plugin-ID")
# ):
#     """调用文本嵌入模型"""
#     try:
#         manager = get_plugin_manager()

#         result = await manager.invoke_plugin(x_plugin_id, "invoke_text_embedding", jsonable_encoder(request.data))

#         return result

#     except Exception as e:
#         logger.error(f"文本嵌入调用失败: {e}")
#         raise HTTPException(status_code=500, detail=str(e))


# @router.post("/{tenant_id}/dispatch/text_embedding/num_tokens")
# async def get_text_embedding_num_tokens(
#     tenant_id: str, request: TextEmbeddingTokensRequest, x_plugin_id: str = Header(..., alias="X-Plugin-ID")
# ):
#     """获取文本嵌入Token数量"""
#     try:
#         manager = get_plugin_manager()

#         result = await manager.invoke_plugin(
#             x_plugin_id, "get_text_embedding_num_tokens", jsonable_encoder(request.data)
#         )

#         return {"num_tokens": result.get("num_tokens", [])}

#     except Exception as e:
#         logger.error(f"获取文本嵌入Token数量失败: {e}")
#         raise HTTPException(status_code=500, detail=str(e))


# # 重排序相关API
# @router.post("/{tenant_id}/dispatch/rerank/invoke")
# async def invoke_rerank(
#     tenant_id: str, request: RerankInvokeRequest, x_plugin_id: str = Header(..., alias="X-Plugin-ID")
# ):
#     """调用重排序模型"""
#     try:
#         manager = get_plugin_manager()

#         result = await manager.invoke_plugin(x_plugin_id, "invoke_rerank", jsonable_encoder(request.data))

#         return result

#     except Exception as e:
#         logger.error(f"重排序调用失败: {e}")
#         raise HTTPException(status_code=500, detail=str(e))


# # TTS相关API
# @router.post("/{tenant_id}/dispatch/tts/invoke")
# async def invoke_tts(tenant_id: str, request: TTSInvokeRequest, x_plugin_id: str = Header(..., alias="X-Plugin-ID")):
#     """调用文本转语音模型"""
#     try:
#         manager = get_plugin_manager()

#         for chunk in manager.invoke_plugin_stream(x_plugin_id, "invoke_tts", jsonable_encoder(request.data)):
#             yield {"result": chunk.get("result")}

#     except Exception as e:
#         logger.error(f"TTS调用失败: {e}")
#         raise HTTPException(status_code=500, detail=str(e))


# @router.post("/{tenant_id}/dispatch/tts/model/voices")
# async def get_tts_model_voices(
#     tenant_id: str, request: TTSVoicesRequest, x_plugin_id: str = Header(..., alias="X-Plugin-ID")
# ):
#     """获取TTS模型声音列表"""
#     try:
#         manager = get_plugin_manager()

#         result = await manager.invoke_plugin(x_plugin_id, "get_tts_model_voices", jsonable_encoder(request.data))

#         voices = []
#         for voice in result.get("voices", []):
#             voices.append({"name": voice.get("name"), "value": voice.get("value")})

#         return {"voices": voices}

#     except Exception as e:
#         logger.error(f"获取TTS声音列表失败: {e}")
#         raise HTTPException(status_code=500, detail=str(e))


# # 语音转文本相关API
# @router.post("/{tenant_id}/dispatch/speech2text/invoke")
# async def invoke_speech2text(
#     tenant_id: str, request: Speech2TextInvokeRequest, x_plugin_id: str = Header(..., alias="X-Plugin-ID")
# ):
#     """调用语音转文本模型"""
#     try:
#         manager = get_plugin_manager()

#         result = await manager.invoke_plugin(x_plugin_id, "invoke_speech_to_text", jsonable_encoder(request.data))

#         return {"result": result.get("result", "")}

#     except Exception as e:
#         logger.error(f"语音转文本调用失败: {e}")
#         raise HTTPException(status_code=500, detail=str(e))


# # 内容审核相关API
# @router.post("/{tenant_id}/dispatch/moderation/invoke")
# async def invoke_moderation(
#     tenant_id: str, request: ModerationInvokeRequest, x_plugin_id: str = Header(..., alias="X-Plugin-ID")
# ):
#     """调用内容审核模型"""
#     try:
#         manager = get_plugin_manager()

#         result = await manager.invoke_plugin(x_plugin_id, "invoke_moderation", jsonable_encoder(request.data))

#         return {"result": result.get("result", False)}

#     except Exception as e:
#         logger.error(f"内容审核调用失败: {e}")
#         raise HTTPException(status_code=500, detail=str(e))
