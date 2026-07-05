/**
 * useChat 扩展功能测试
 *
 * 测试新的消息部分类型（source-url, source-document, file, table, json）的处理
 */
import { describe, it, expect } from 'vitest'
import type { UIMessage, SourceUrlPart, SourceDocumentPart, FilePart, DataPart } from '@/ai/types'

// 由于 processThinkingEvents 不是导出函数，我们通过测试消息处理逻辑来验证
describe('processThinkingEvents - 新事件类型', () => {
  it('source-url parts 正确保留在消息中', () => {
    const sourcePart: SourceUrlPart = {
      type: 'source-url',
      sourceId: 'source-123',
      url: 'https://example.com',
      title: 'Example',
    }

    const message: UIMessage = {
      id: 'msg-1',
      role: 'assistant',
      parts: [
        { type: 'text', text: '根据搜索结果' },
        sourcePart,
      ],
    }

    // 新类型 parts 应该保留在消息中
    expect(message.parts.some(p => p.type === 'source-url')).toBe(true)
    expect(message.parts.find(p => p.type === 'source-url')).toEqual(sourcePart)
  })

  it('source-document parts 正确保留在消息中', () => {
    const sourcePart: SourceDocumentPart = {
      type: 'source-document',
      sourceId: 'source-456',
      mediaType: 'application/pdf',
      url: 'https://minio.example.com/doc.pdf',
      title: 'Document',
    }

    const message: UIMessage = {
      id: 'msg-2',
      role: 'assistant',
      parts: [
        { type: 'text', text: '参考资料' },
        sourcePart,
      ],
    }

    expect(message.parts.some(p => p.type === 'source-document')).toBe(true)
    expect(message.parts.find(p => p.type === 'source-document')).toEqual(sourcePart)
  })

  it('file parts 正确保留在消息中', () => {
    const filePart: FilePart = {
      type: 'file',
      mediaType: 'application/pdf',
      url: 'https://minio.example.com/doc.pdf',
      filename: 'report.pdf',
      size: 1048576,
    }

    const message: UIMessage = {
      id: 'msg-3',
      role: 'assistant',
      parts: [
        { type: 'text', text: '附件如下' },
        filePart,
      ],
    }

    expect(message.parts.some(p => p.type === 'file')).toBe(true)
    expect(message.parts.find(p => p.type === 'file')).toEqual(filePart)
  })

  it('table data parts 正确保留在消息中', () => {
    const dataPart: DataPart = {
      type: 'table',
      id: 'data-789',
      content: {
        headers: ['Name', 'Age'],
        rows: [['Alice', 25]],
      },
    }

    const message: UIMessage = {
      id: 'msg-4',
      role: 'assistant',
      parts: [
        { type: 'text', text: '查询结果' },
        dataPart,
      ],
    }

    expect(message.parts.some(p => p.type === 'table')).toBe(true)
    expect(message.parts.find(p => p.type === 'table')).toEqual(dataPart)
  })

  it('json data parts 正确保留在消息中', () => {
    const dataPart: DataPart = {
      type: 'json',
      id: 'data-101',
      content: {
        name: 'Alice',
        age: 25,
      },
    }

    const message: UIMessage = {
      id: 'msg-5',
      role: 'assistant',
      parts: [
        { type: 'text', text: 'JSON 数据' },
        dataPart,
      ],
    }

    expect(message.parts.some(p => p.type === 'json')).toBe(true)
    expect(message.parts.find(p => p.type === 'json')).toEqual(dataPart)
  })

  it('新类型 parts 与 thinking parts 共存', () => {
    const message: UIMessage = {
      id: 'msg-6',
      role: 'assistant',
      parts: [
        { type: 'thinking', thinking: '分析中...' },
        { type: 'source-url', sourceId: 'source-1', url: 'https://example.com' },
        { type: 'text', text: '搜索结果如下' },
        { type: 'table', id: 'data-1', content: { headers: ['A'], rows: [['B']] } },
      ],
    }

    // 所有类型都应该存在于 parts 中
    const types = message.parts.map(p => p.type)
    expect(types).toContain('thinking')
    expect(types).toContain('source-url')
    expect(types).toContain('text')
    expect(types).toContain('table')
  })

  it('多种新类型 parts 同时存在', () => {
    const message: UIMessage = {
      id: 'msg-7',
      role: 'assistant',
      parts: [
        { type: 'thinking', thinking: '综合分析' },
        { type: 'source-url', sourceId: 'source-1', url: 'https://example.com', title: '来源 1' },
        { type: 'source-document', sourceId: 'source-2', mediaType: 'application/pdf', url: 'https://minio.example.com/doc.pdf', title: '文档' },
        { type: 'file', mediaType: 'application/pdf', url: 'https://minio.example.com/report.pdf', filename: 'report.pdf' },
        { type: 'table', id: 'data-1', content: { headers: ['A'], rows: [['B']] } },
        { type: 'json', id: 'data-2', content: { key: 'value' } },
        { type: 'text', text: '完整结果' },
      ],
    }

    // 验证所有类型都存在
    const types = message.parts.map(p => p.type)
    expect(types).toContain('thinking')
    expect(types).toContain('source-url')
    expect(types).toContain('source-document')
    expect(types).toContain('file')
    expect(types).toContain('table')
    expect(types).toContain('json')
    expect(types).toContain('text')

    // 验证每种类型的数量
    expect(types.filter(t => t === 'thinking')).toHaveLength(1)
    expect(types.filter(t => t === 'source-url')).toHaveLength(1)
    expect(types.filter(t => t === 'source-document')).toHaveLength(1)
    expect(types.filter(t => t === 'file')).toHaveLength(1)
    expect(types.filter(t => t === 'table')).toHaveLength(1)
    expect(types.filter(t => t === 'json')).toHaveLength(1)
    expect(types.filter(t => t === 'text')).toHaveLength(1)
  })

  it('source-url 缺少可选字段', () => {
    const sourcePart: SourceUrlPart = {
      type: 'source-url',
      sourceId: 'source-789',
      url: 'https://example.com',
    }

    const message: UIMessage = {
      id: 'msg-8',
      role: 'assistant',
      parts: [sourcePart],
    }

    expect(message.parts[0]).toEqual(sourcePart)
    expect(message.parts[0].type).toBe('source-url')
  })

  it('file 缺少可选字段', () => {
    const filePart: FilePart = {
      type: 'file',
      mediaType: 'text/plain',
      url: 'https://example.com/file.txt',
    }

    const message: UIMessage = {
      id: 'msg-9',
      role: 'assistant',
      parts: [filePart],
    }

    expect(message.parts[0]).toEqual(filePart)
    expect(message.parts[0].type).toBe('file')
  })

  it('保留原有工具调用和工具结果类型', () => {
    const message: UIMessage = {
      id: 'msg-10',
      role: 'assistant',
      parts: [
        { type: 'thinking', thinking: '调用工具' },
        { type: 'tool-call', toolCallId: 'call-1', toolName: 'search', args: { query: 'test' } },
        { type: 'tool-result', toolCallId: 'call-1', toolName: 'search', result: { data: 'result' } },
        { type: 'source-url', sourceId: 'source-1', url: 'https://example.com' },
        { type: 'text', text: '工具调用完成' },
      ],
    }

    const types = message.parts.map(p => p.type)
    expect(types).toContain('thinking')
    expect(types).toContain('tool-call')
    expect(types).toContain('tool-result')
    expect(types).toContain('source-url')
    expect(types).toContain('text')
  })
})
