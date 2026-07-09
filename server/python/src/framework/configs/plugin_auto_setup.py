"""插件自动设置配置模型"""

from __future__ import annotations

from pydantic import Field, field_validator

from framework.schemas import BaseModel


class VerificationConfig(BaseModel):
    """验证配置"""

    enabled: bool = Field(True, description="是否启用验证")
    timeout: int = Field(10, ge=1, le=60, description="验证超时时间(秒)")
    on_failure: str = Field("warn", description="失败策略: warn/degrade/fail")

    @field_validator("on_failure")
    @classmethod
    def validate_on_failure(cls, v: str) -> str:
        """验证失败策略"""
        if v not in ("warn", "degrade", "fail"):
            raise ValueError("失败策略必须是 warn/degrade/fail 之一")
        return v


class PluginAutoSetupItem(BaseModel):
    """单个插件自动设置配置"""

    plugin_id: str = Field(..., description="插件ID")
    auto_install: bool = Field(True, description="是否自动安装")
    auto_start: bool = Field(True, description="是否自动启动")
    credentials: dict[str, str] = Field(
        default_factory=dict, description="凭证配置"
    )


class PluginAutoSetupConfig(BaseModel):
    """插件自动设置总配置"""

    enabled: bool = Field(False, description="是否启用自动设置")
    plugins: list[PluginAutoSetupItem] = Field(
        default_factory=list, description="插件列表"
    )
    verification: VerificationConfig = Field(
        default_factory=VerificationConfig, description="验证配置"
    )
