/**
 * 企业知识库管理模块 API 函数
 */

export const documentLibraryApi = {
  list: async () => ({ data: [] }),
  get: async (id: string) => ({ data: null }),
  create: async (data: unknown) => ({ data: null }),
  update: async (id: string, data: unknown) => ({ data: null }),
  delete: async (id: string) => {},
};

export const knowledgeBaseApi = {
  list: async () => ({ data: [] }),
  get: async (id: string) => ({ data: null }),
  create: async (data: unknown) => ({ data: null }),
  update: async (id: string, data: unknown) => ({ data: null }),
  delete: async (id: string) => {},
};

export const reviewApi = {
  list: async () => ({ data: [] }),
  get: async (id: string) => ({ data: null }),
  approve: async (id: string, comment?: string) => {},
  reject: async (id: string, comment: string) => {},
};
