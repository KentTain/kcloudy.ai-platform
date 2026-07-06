"""Skill 运行时错误异常体系

定义 Skill 执行过程中可能出现的各类错误，支持结构化错误处理。
"""


class SkillError(Exception):
    """Skill 错误基类"""

    def __init__(self, message: str = ""):
        self.message = message
        super().__init__(message)


class SkillNotFoundError(SkillError):
    """Skill 不存在"""

    def __init__(self, skill_id: str):
        self.skill_id = skill_id
        super().__init__(f"Skill 不存在: {skill_id}")


class SkillPreparationError(SkillError):
    """Skill 准备失败"""

    def __init__(self, skill_id: str, reason: str):
        self.skill_id = skill_id
        self.reason = reason
        super().__init__(f"Skill 准备失败 [{skill_id}]: {reason}")


class SkillInvocationError(SkillError):
    """Skill 调用失败"""

    def __init__(self, skill_id: str, reason: str):
        self.skill_id = skill_id
        self.reason = reason
        super().__init__(f"Skill 调用失败 [{skill_id}]: {reason}")


class SkillSecurityError(SkillError):
    """Skill 安全验证失败"""

    def __init__(self, skill_id: str, violations: list[str]):
        self.skill_id = skill_id
        self.violations = violations
        super().__init__(
            f"Skill 安全验证失败 [{skill_id}]: {', '.join(violations)}"
        )


class SkillTimeoutError(SkillError):
    """Skill 执行超时"""

    def __init__(self, skill_id: str, timeout: int):
        self.skill_id = skill_id
        self.timeout = timeout
        super().__init__(f"Skill 执行超时 [{skill_id}]: {timeout}s")
