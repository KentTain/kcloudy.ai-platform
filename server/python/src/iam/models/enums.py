"""
IAM 模块枚举定义
"""

from enum import Enum

from framework.common.enums import EnumBase


class UserStatus(str, EnumBase):
    """用户状态枚举"""

    ACTIVE = "active"
    INACTIVE = "inactive"
    LOCKED = "locked"

    @property
    def label(self) -> str:
        labels = {
            UserStatus.ACTIVE: "激活",
            UserStatus.INACTIVE: "停用",
            UserStatus.LOCKED: "锁定",
        }
        return labels.get(self, self.name)


class OAuthProvider(str, EnumBase):
    """OAuth 提供商枚举"""

    WECHAT = "wechat"
    WEWORK = "wework"

    @property
    def label(self) -> str:
        labels = {
            OAuthProvider.WECHAT: "微信",
            OAuthProvider.WEWORK: "企业微信",
        }
        return labels.get(self, self.name)


class RoleCode(str, EnumBase):
    """角色编码枚举"""

    ADMIN = "admin"
    VIEWER = "viewer"

    @property
    def label(self) -> str:
        labels = {
            RoleCode.ADMIN: "管理员",
            RoleCode.VIEWER: "查看者",
        }
        return labels.get(self, self.name)


class OrganizationStatus(str, EnumBase):
    """组织状态枚举"""

    ACTIVE = "active"
    INACTIVE = "inactive"

    @property
    def label(self) -> str:
        labels = {
            OrganizationStatus.ACTIVE: "启用",
            OrganizationStatus.INACTIVE: "停用",
        }
        return labels.get(self, self.name)


class TenantStatus(str, Enum):
    """租户状态常量"""

    ACTIVE = "active"
    INACTIVE = "inactive"


class UserTenantRole(str, EnumBase):
    """用户租户角色枚举"""

    ADMIN = "admin"
    MEMBER = "member"

    @property
    def label(self) -> str:
        labels = {
            UserTenantRole.ADMIN: "管理员",
            UserTenantRole.MEMBER: "成员",
        }
        return labels.get(self, self.name)


class AuditLogBusinessType(EnumBase):
    """审计日志业务类型枚举"""

    LIBRARY = "library"
    """文档库"""
    KNOWLEDGE_BASE = "knowledge_base"
    """知识库"""
    TAG = "tag"
    """标签"""
    ROLE = "role"
    """人设"""
    SYSTEM_ROLE = "system_role"
    """系统角色"""
    USER = "user"
    """用户"""
    DEPT = "dept"
    """组织"""
    PLATFORM_SETTING = "platform_setting"
    """平台设置"""


class AuditLogOperationType(EnumBase):
    """审计日志操作类型枚举"""

    LIBRARY_CREATE = "library.library_create"
    LIBRARY_UPDATE = "library.library_update"
    LIBRARY_DELETE = "library.library_delete"
    LIBRARY_TRANSFER_OWNER = "library.library_transfer_owner"
    FOLDER_CREATE = "library.folder_create"
    FOLDER_UPDATE = "library.folder_update"
    FOLDER_REMOVE_TO_TRASH = "library.folder_remove_to_trash"
    FOLDER_RESTORE = "library.folder_restore"
    FOLDER_PURGE = "library.folder_purge"
    FILE_UPLOAD = "library.file_upload"
    FILE_DOWNLOAD = "library.file_download"
    FILE_UPDATE = "library.file_update"
    FILE_CREATE = "library.file_create"
    FILE_REMOVE_TO_TRASH = "library.file_remove_to_trash"
    FILE_RESTORE = "library.file_restore"
    FILE_PURGE = "library.file_purge"
    FILE_SUBMIT = "library.file_submit"
    INDEX_TASK_CREATE = "library.index_task_create"
    INDEX_TASK_RETRY = "library.index_task_retry"
    LIBRARY_MEMBER_ADD = "library.member_add"
    LIBRARY_MEMBER_CHANGE_ROLE = "library.member_change_role"
    LIBRARY_MEMBER_ENABLE = "library.member_enable"
    LIBRARY_MEMBER_DISABLE = "library.member_disable"
    LIBRARY_MEMBER_DELETE = "library.member_delete"
    PERMISSION_GROUP_CREATE = "library.permission_group_create"
    PERMISSION_GROUP_UPDATE = "library.permission_group_update"
    PERMISSION_GROUP_ADD_MEMBER = "library.permission_group_add_member"
    PERMISSION_GROUP_DELETE = "library.permission_group_delete"
    POLICY_CREATE = "library.policy_create"
    POLICY_UPDATE = "library.policy_update"
    POLICY_DELETE = "library.policy_delete"
    PERMISSION_REQUEST_SUBMIT = "library.permission_request_submit"
    PERMISSION_REQUEST_APPROVE = "library.permission_request_approve"
    PERMISSION_REQUEST_REJECT = "library.permission_request_reject"
    KNOWLEDGE_BASE_CREATE = "knowledge_base.knowledge_base_create"
    KNOWLEDGE_BASE_UPDATE = "knowledge_base.knowledge_base_update"
    KNOWLEDGE_BASE_ENABLE = "knowledge_base.knowledge_base_enable"
    KNOWLEDGE_BASE_DISABLE = "knowledge_base.knowledge_base_disable"
    KNOWLEDGE_BASE_DELETE = "knowledge_base.knowledge_base_delete"
    KNOWLEDGE_DOCUMENT_ENABLE = "knowledge_base.knowledge_document_enable"
    KNOWLEDGE_DOCUMENT_DISABLE = "knowledge_base.knowledge_document_disable"
    KNOWLEDGE_DOCUMENT_DELETE = "knowledge_base.knowledge_document_delete"
    REVIEW_SUBMIT = "knowledge_base.review_submit"
    REVIEW_APPROVE = "knowledge_base.review_approve"
    REVIEW_REJECT = "knowledge_base.review_reject"
    REVIEW_REQUIRE_SUPPLEMENT = "knowledge_base.review_require_supplement"
    KNOWLEDGE_BASE_MEMBER_ADD = "knowledge_base.member_add"
    KNOWLEDGE_BASE_MEMBER_CHANGE_ROLE = "knowledge_base.member_change_role"
    KNOWLEDGE_BASE_MEMBER_UPDATE = "knowledge_base.member_update"
    KNOWLEDGE_BASE_MEMBER_DELETE = "knowledge_base.member_delete"
    RETRIEVAL_TEST_CREATE = "knowledge_base.retrieval_test_create"
    TAG_CREATE = "tag.tag_create"
    TAG_UPDATE = "tag.tag_update"
    TAG_ENABLE = "tag.tag_enable"
    TAG_DISABLE = "tag.tag_disable"
    TAG_DELETE = "tag.tag_delete"
    SYSTEM_ROLE_CREATE = "system_role.system_role_create"
    SYSTEM_ROLE_UPDATE = "system_role.system_role_update"
    SYSTEM_ROLE_DELETE = "system_role.system_role_delete"
    ROLE_CREATE = "role.role_create"
    ROLE_UPDATE = "role.role_update"
    ROLE_DELETE = "role.role_delete"
    USER_CREATE = "user.user_create"
    USER_UPDATE = "user.user_update"
    USER_ENABLE = "user.user_enable"
    USER_DISABLE = "user.user_disable"
    USER_DELETE = "user.user_delete"
    USER_RESET_PASSWORD = "user.user_reset_password"
    DEPT_CREATE = "dept.dept_create"
    DEPT_UPDATE = "dept.dept_update"
    DEPT_DELETE = "dept.dept_delete"
    DEPT_MEMBER_ADD = "dept.member_add"
    DEPT_MEMBER_DELETE = "dept.member_delete"
    DEPT_USER_ENABLE = "dept.user_enable"
    DEPT_USER_DISABLE = "dept.user_disable"
    PLATFORM_SETTING_UPDATE = "platform_setting.platform_setting_update"

    __labels__ = {
        "library.library_create": "文档库创建",
        "library.library_update": "文档库基础信息修改",
        "library.library_delete": "文档库删除",
        "library.library_transfer_owner": "文档库拥有者移交",
        "library.folder_create": "文件夹创建",
        "library.folder_update": "文件夹更新",
        "library.folder_remove_to_trash": "文件夹移动到回收站",
        "library.folder_restore": "文件夹从回收站恢复",
        "library.folder_purge": "文件夹永久删除",
        "library.file_upload": "文件上传",
        "library.file_download": "文件预览或下载",
        "library.file_update": "文件更新",
        "library.file_create": "文件创建",
        "library.file_remove_to_trash": "文件移动到回收站",
        "library.file_restore": "文件从回收站恢复",
        "library.file_purge": "文件永久删除",
        "library.file_submit": "文件提交入库",
        "library.index_task_create": "文档索引任务创建",
        "library.index_task_retry": "失败索引任务人工重试",
        "library.member_add": "文档库成员添加",
        "library.member_change_role": "文档库成员角色调整",
        "library.member_enable": "文档库成员启用",
        "library.member_disable": "文档库成员禁用",
        "library.member_delete": "文档库成员移除",
        "library.permission_group_create": "文档库权限组创建",
        "library.permission_group_update": "文档库权限组或资源权限配置更新",
        "library.permission_group_add_member": "文档库权限组添加成员",
        "library.permission_group_delete": "文档库权限组删除",
        "library.policy_create": "企业策略创建",
        "library.policy_update": "企业策略更新",
        "library.policy_delete": "企业策略删除",
        "library.permission_request_submit": "权限申请提交",
        "library.permission_request_approve": "权限申请审批通过",
        "library.permission_request_reject": "权限申请审批驳回",
        "knowledge_base.knowledge_base_create": "知识库创建",
        "knowledge_base.knowledge_base_update": "知识库基础信息或配置更新",
        "knowledge_base.knowledge_base_enable": "知识库启用",
        "knowledge_base.knowledge_base_disable": "知识库禁用",
        "knowledge_base.knowledge_base_delete": "知识库删除",
        "knowledge_base.knowledge_document_enable": "知识库文档引用启用",
        "knowledge_base.knowledge_document_disable": "知识库文档引用禁用",
        "knowledge_base.knowledge_document_delete": "知识库文档引用移除",
        "knowledge_base.review_submit": "入库申请提交",
        "knowledge_base.review_approve": "入库审核通过",
        "knowledge_base.review_reject": "入库审核驳回",
        "knowledge_base.review_require_supplement": "入库审核要求补充",
        "knowledge_base.member_add": "知识库成员添加",
        "knowledge_base.member_change_role": "知识库成员身份调整",
        "knowledge_base.member_update": "知识库成员状态或配置调整",
        "knowledge_base.member_delete": "知识库成员移除",
        "knowledge_base.retrieval_test_create": "保存知识库检索测试记录",
        "tag.tag_create": "标签创建",
        "tag.tag_update": "标签编辑",
        "tag.tag_enable": "标签启用",
        "tag.tag_disable": "标签禁用",
        "tag.tag_delete": "标签删除",
        "system_role.system_role_create": "系统角色创建",
        "system_role.system_role_update": "系统角色编辑和成员覆盖维护",
        "system_role.system_role_delete": "系统角色删除",
        "role.role_create": "人设创建",
        "role.role_update": "人设编辑",
        "role.role_delete": "人设删除",
        "user.user_create": "用户创建",
        "user.user_update": "用户资料、角色或部门调整",
        "user.user_enable": "用户启用",
        "user.user_disable": "用户禁用",
        "user.user_delete": "用户删除",
        "user.user_reset_password": "管理员重置用户密码",
        "dept.dept_create": "组织创建",
        "dept.dept_update": "组织编辑",
        "dept.dept_delete": "组织删除",
        "dept.member_add": "组织直属成员添加",
        "dept.member_delete": "组织直属成员移除",
        "dept.user_enable": "组织直属成员账号启用",
        "dept.user_disable": "组织直属成员账号禁用",
        "platform_setting.platform_setting_update": "企业知识库平台设置更新",
    }


class AuditLogResourceType(EnumBase):
    """审计日志资源类型枚举。"""

    USER = "user"
    """用户"""
    DEPT = "dept"
    """组织"""
    ROLE = "role"
    """人设"""
    SYSTEM_ROLE = "system_role"
    """系统角色"""
    TAG = "tag"
    """标签"""
    LIBRARY = "library"
    """文档库"""
    FOLDER = "folder"
    """文件夹"""
    FILE = "file"
    """文件"""
    MEMBER = "member"
    """成员"""
    PERMISSION_GROUP = "permission_group"
    """权限组"""
    POLICY = "policy"
    """企业策略"""
    PERMISSION_REQUEST = "permission_request"
    """权限申请"""
    KNOWLEDGE_BASE = "knowledge_base"
    """知识库"""
    KNOWLEDGE_DOCUMENT = "knowledge_document"
    """知识库文档"""
    REVIEW = "review"
    """入库审核"""
    INDEX_TASK = "index_task"
    """索引任务"""
    RETRIEVAL_TEST = "retrieval_test"
    """检索测试"""
    PLATFORM_SETTING = "platform_setting"
    """平台设置"""

    __labels__ = {
        "user": "用户",
        "dept": "组织",
        "role": "人设",
        "system_role": "系统角色",
        "tag": "标签",
        "library": "文档库",
        "folder": "文件夹",
        "file": "文件",
        "member": "成员",
        "permission_group": "权限组",
        "policy": "企业策略",
        "permission_request": "权限申请",
        "knowledge_base": "知识库",
        "knowledge_document": "知识库文档",
        "review": "入库审核",
        "index_task": "索引任务",
        "retrieval_test": "检索测试",
        "graph_task": "图谱任务",
        "platform_setting": "平台设置",
    }
