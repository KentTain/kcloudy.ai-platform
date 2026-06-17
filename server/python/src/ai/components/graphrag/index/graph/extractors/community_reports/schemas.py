"""社区报告的通用字段名称定义."""

# 预处理后的节点表模式
NODE_ID = "human_readable_id"
NODE_NAME = "title"
NODE_DESCRIPTION = "description"
NODE_DEGREE = "degree"
NODE_DETAILS = "node_details"
NODE_COMMUNITY = "community"
NODE_LEVEL = "level"

# 预处理后的边表模式
EDGE_ID = "human_readable_id"
EDGE_SOURCE = "source"
EDGE_TARGET = "target"
EDGE_DESCRIPTION = "description"
EDGE_DEGREE = "rank"
EDGE_DETAILS = "edge_details"
EDGE_WEIGHT = "weight"

# 预处理后的声明表模式
CLAIM_ID = "human_readable_id"
CLAIM_SUBJECT = "subject_id"
CLAIM_TYPE = "type"
CLAIM_STATUS = "status"
CLAIM_DESCRIPTION = "description"
CLAIM_DETAILS = "claim_details"

# 社区层次结构表模式
SUB_COMMUNITY = "sub_communitty"
SUB_COMMUNITY_SIZE = "sub_community_size"
COMMUNITY_LEVEL = "level"

# 社区上下文表模式
ALL_CONTEXT = "all_context"
CONTEXT_STRING = "context_string"
CONTEXT_SIZE = "context_size"
CONTEXT_EXCEED_FLAG = "context_exceed_limit"

# 社区报告表模式
REPORT_ID = "id"
COMMUNITY_ID = "id"
COMMUNITY_LEVEL = "level"
TITLE = "title"
SUMMARY = "summary"
FINDINGS = "findings"
RATING = "rank"
EXPLANATION = "rating_explanation"
FULL_CONTENT = "full_content"
FULL_CONTENT_JSON = "full_content_json"
