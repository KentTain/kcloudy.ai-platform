/**
 * 文档库管理模块类型定义
 */

// ── 文档库 ──────────────────────────────────────────────────────

export interface Library {
  id: string;
  type: string;
  code: string;
  name: string;
  description: string | null;
  icon: string | null;
  owner_id: string;
  enabled: boolean;
  allow_submit_to_kb: boolean;
  created_at: string;
}

// ── 文件夹 ──────────────────────────────────────────────────────

export interface Folder {
  id: string;
  library_id: string;
  name: string;
  parent_id: string | null;
  description: string | null;
  tree_level: number;
  tree_leaf: boolean;
  parent_ids: string;
  tree_sort: number;
  tree_sorts: string;
  tree_names: string;
  created_at: string;
}

// ── 文档 ────────────────────────────────────────────────────────

export interface Document {
  id: string;
  library_id: string;
  folder_id: string | null;
  owner_id: string;
  name: string;
  document_type: string;
  lifecycle_status: string;
  file_size: number;
  mime_type: string | null;
  processing_status: string;
  storage_key: string | null;
  created_at: string;
}

// ── 文档库成员 ──────────────────────────────────────────────────

export interface LibraryMember {
  id: string;
  library_id: string;
  user_id: string;
  user_name: string;
  role: string;
  status: string;
  remarks: string | null;
  created_at: string;
}

// ── 文档库角色 ──────────────────────────────────────────────────

export interface LibraryRole {
  id: string;
  library_id: string;
  role_kind: string;
  code: string;
  name: string;
  description: string | null;
  permissions: Record<string, unknown>;
  created_at: string;
}

// ── 资源 ACL ────────────────────────────────────────────────────

export interface ResourceAcl {
  id: string;
  library_id: string;
  resource_type: string;
  resource_id: string;
  subject_id: string;
  subject_type: string;
  action: string;
  effect: string;
  priority: number;
  inherited_from_resource_id: string | null;
  created_at: string;
}

// ── 标签 ────────────────────────────────────────────────────────

export interface Tag {
  id: string;
  name: string;
  group_id: string | null;
  color: string | null;
  description: string | null;
  persona_id: string | null;
  doc_count: number;
  created_at: string;
}

// ── 标签组 ──────────────────────────────────────────────────────

export interface TagGroup {
  id: string;
  name: string;
  sort_order: number;
  created_at: string;
}

// ── 人设 ────────────────────────────────────────────────────────

export interface Persona {
  id: string;
  name: string;
  instruction: string;
  role: string | null;
  description: string | null;
  created_at: string;
  updated_at: string | null;
}

// ── 回收站 ──────────────────────────────────────────────────────

export interface RecycleItem {
  id: string;
  library_id: string;
  resource_type: string;
  resource_id: string;
  original_parent_id: string | null;
  original_path: string | null;
  deleted_by: string | null;
  status: string;
  created_at: string;
}

// ── 元数据字段 ──────────────────────────────────────────────────

export interface MetadataField {
  id: string;
  library_id: string;
  name: string;
  field_type: string;
  is_required: boolean;
  enum_values: string[] | null;
  sort_order: number;
  created_at: string;
}

// ── 资源元数据 ──────────────────────────────────────────────────

export interface ResourceMetadata {
  id: string;
  library_id: string;
  resource_type: string;
  resource_id: string;
  field_id: string;
  field_name: string;
  value: string | null;
  created_at: string;
}

// ── 分页查询 ────────────────────────────────────────────────────

export interface PaginatedQuery {
  page?: number;
  page_size?: number;
  keyword?: string;
}
