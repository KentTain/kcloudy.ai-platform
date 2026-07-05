import { describe, it, expect } from 'vitest'
import type {
  SourceUrlPart,
  SourceDocumentPart,
  FilePart,
  DataPart,
  UIMessagePart
} from '@/ai/types'

describe('Message Part Types', () => {
  it('SourceUrlPart has correct structure', () => {
    const part: SourceUrlPart = {
      type: 'source-url',
      sourceId: 'source-123',
      url: 'https://example.com',
      title: 'Example',
    }

    expect(part.type).toBe('source-url')
    expect(part.sourceId).toBe('source-123')
  })

  it('SourceDocumentPart has correct structure', () => {
    const part: SourceDocumentPart = {
      type: 'source-document',
      sourceId: 'source-456',
      mediaType: 'application/pdf',
      url: 'https://example.com/doc.pdf',
      title: 'Document',
    }

    expect(part.type).toBe('source-document')
    expect(part.mediaType).toBe('application/pdf')
  })

  it('FilePart has correct structure', () => {
    const part: FilePart = {
      type: 'file',
      mediaType: 'application/pdf',
      url: 'https://minio.example.com/doc.pdf',
      filename: 'document.pdf',
      size: 1048576,
    }

    expect(part.type).toBe('file')
    expect(part.filename).toBe('document.pdf')
  })

  it('DataPart has correct structure', () => {
    const part: DataPart = {
      type: 'table',
      id: 'data-789',
      content: {
        headers: ['Name', 'Age'],
        rows: [['Alice', 25]],
      },
    }

    expect(part.type).toBe('table')
    expect(part.id).toBe('data-789')
  })

  it('UIMessagePart includes new part types', () => {
    const sourceUrl: UIMessagePart = {
      type: 'source-url',
      sourceId: 'source-123',
      url: 'https://example.com',
    }

    const sourceDoc: UIMessagePart = {
      type: 'source-document',
      sourceId: 'source-456',
      mediaType: 'application/pdf',
      url: 'https://example.com/doc.pdf',
    }

    const file: UIMessagePart = {
      type: 'file',
      mediaType: 'application/pdf',
      url: 'https://minio.example.com/doc.pdf',
    }

    const data: UIMessagePart = {
      type: 'table',
      id: 'data-789',
      content: {},
    }

    expect(sourceUrl.type).toBe('source-url')
    expect(sourceDoc.type).toBe('source-document')
    expect(file.type).toBe('file')
    expect(data.type).toBe('table')
  })
})
