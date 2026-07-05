import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import TableRenderer from '@/components/ai-elements/data/TableRenderer.vue'
import JsonRenderer from '@/components/ai-elements/data/JsonRenderer.vue'
import DataRenderer from '@/components/ai-elements/data/DataRenderer.vue'
import type { DataPart } from '@/ai/types'

describe('TableRenderer', () => {
  it('renders table with correct headers and rows', () => {
    const wrapper = mount(TableRenderer, {
      props: {
        content: {
          headers: ['Name', 'Age'],
          rows: [['Alice', 25], ['Bob', 30]],
        }
      }
    })

    expect(wrapper.find('table').exists()).toBe(true)
    expect(wrapper.findAll('th')).toHaveLength(2)
    expect(wrapper.findAll('tbody tr')).toHaveLength(2)
  })

  it('renders headers with correct text', () => {
    const wrapper = mount(TableRenderer, {
      props: {
        content: {
          headers: ['Name', 'Age', 'City'],
          rows: [],
        }
      }
    })

    const headers = wrapper.findAll('th')
    expect(headers[0].text()).toBe('Name')
    expect(headers[1].text()).toBe('Age')
    expect(headers[2].text()).toBe('City')
  })

  it('renders rows with correct cell data', () => {
    const wrapper = mount(TableRenderer, {
      props: {
        content: {
          headers: ['Name', 'Age'],
          rows: [['Alice', 25], ['Bob', 30]],
        }
      }
    })

    const rows = wrapper.findAll('tbody tr')
    const firstRowCells = rows[0].findAll('td')
    expect(firstRowCells[0].text()).toBe('Alice')
    expect(firstRowCells[1].text()).toBe('25')

    const secondRowCells = rows[1].findAll('td')
    expect(secondRowCells[0].text()).toBe('Bob')
    expect(secondRowCells[1].text()).toBe('30')
  })

  it('renders empty table when no rows', () => {
    const wrapper = mount(TableRenderer, {
      props: {
        content: {
          headers: ['Name', 'Age'],
          rows: [],
        }
      }
    })

    expect(wrapper.find('table').exists()).toBe(true)
    expect(wrapper.findAll('tbody tr')).toHaveLength(0)
  })
})

describe('JsonRenderer', () => {
  it('renders JSON with formatting', () => {
    const wrapper = mount(JsonRenderer, {
      props: {
        content: {
          key: 'value',
          nested: { field: 123 }
        }
      }
    })

    expect(wrapper.find('pre').exists()).toBe(true)
    expect(wrapper.text()).toContain('key')
    expect(wrapper.text()).toContain('value')
  })

  it('formats JSON with 2-space indentation', () => {
    const wrapper = mount(JsonRenderer, {
      props: {
        content: {
          name: 'test',
          value: 42
        }
      }
    })

    const text = wrapper.find('pre').text()
    expect(text).toContain('  "name"')
    expect(text).toContain('  "value"')
  })

  it('renders arrays correctly', () => {
    const wrapper = mount(JsonRenderer, {
      props: {
        content: [1, 2, 3]
      }
    })

    expect(wrapper.find('pre').exists()).toBe(true)
    expect(wrapper.text()).toContain('1')
    expect(wrapper.text()).toContain('2')
    expect(wrapper.text()).toContain('3')
  })

  it('renders primitive values', () => {
    const wrapper = mount(JsonRenderer, {
      props: {
        content: 'simple string'
      }
    })

    expect(wrapper.find('pre').exists()).toBe(true)
    expect(wrapper.text()).toContain('simple string')
  })
})

describe('DataRenderer', () => {
  it('renders TableRenderer for table type', () => {
    const tablePart: DataPart = {
      type: 'table',
      id: 'table-1',
      content: {
        headers: ['Name', 'Age'],
        rows: [['Alice', 25]],
      }
    }

    const wrapper = mount(DataRenderer, {
      props: { part: tablePart }
    })

    expect(wrapper.findComponent(TableRenderer).exists()).toBe(true)
    expect(wrapper.findComponent(JsonRenderer).exists()).toBe(false)
  })

  it('renders JsonRenderer for json type', () => {
    const jsonPart: DataPart = {
      type: 'json',
      id: 'json-1',
      content: { key: 'value' }
    }

    const wrapper = mount(DataRenderer, {
      props: { part: jsonPart }
    })

    expect(wrapper.findComponent(JsonRenderer).exists()).toBe(true)
    expect(wrapper.findComponent(TableRenderer).exists()).toBe(false)
  })

  it('passes content prop to TableRenderer', () => {
    const tablePart: DataPart = {
      type: 'table',
      id: 'table-1',
      content: {
        headers: ['A', 'B'],
        rows: [['1', '2']],
      }
    }

    const wrapper = mount(DataRenderer, {
      props: { part: tablePart }
    })

    const tableRenderer = wrapper.findComponent(TableRenderer)
    expect(tableRenderer.props('content')).toEqual(tablePart.content)
  })

  it('passes content prop to JsonRenderer', () => {
    const jsonPart: DataPart = {
      type: 'json',
      id: 'json-1',
      content: { test: 'data' }
    }

    const wrapper = mount(DataRenderer, {
      props: { part: jsonPart }
    })

    const jsonRenderer = wrapper.findComponent(JsonRenderer)
    expect(jsonRenderer.props('content')).toEqual(jsonPart.content)
  })
})
