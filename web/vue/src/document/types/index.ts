/**
 * 企业知识库管理模块类型定义
 */

export interface DocumentLibrary {
  id: string;
  name: string;
  [key: string]: unknown;
}

export interface KnowledgeBase {
  id: string;
  name: string;
  [key: string]: unknown;
}

export interface ReviewTask {
  id: string;
  title: string;
  [key: string]: unknown;
}
