// tests/ai/unit/components/test_skill_card.vue.ts
import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import SkillCard from '@/ai/components/SkillCard.vue'
import type { RemoteSkillInfo } from '@/tenant/api/plugin'

describe('SkillCard', () => {
  const mockSkill: RemoteSkillInfo = {
    plugin_id: 'skill-123',
    name: 'Test Skill',
    description: 'A test skill for testing',
    version: '1.0.0',
    author: 'Test Author',
    plugin_type: 'skill',
    skill_type: 'knowledge',
    tags: ['ai', 'test'],
    downloads: 100,
    icon: null,
    download_url: 'https://example.com/skill'
  }

  it('renders skill name and author', () => {
    const wrapper = mount(SkillCard, {
      props: { skill: mockSkill, isInstalled: false }
    })

    expect(wrapper.text()).toContain('Test Skill')
    expect(wrapper.text()).toContain('Test Author')
  })

  it('displays knowledge type badge', () => {
    const wrapper = mount(SkillCard, {
      props: { skill: mockSkill, isInstalled: false }
    })

    const badge = wrapper.find('[data-testid="skill-type-badge"]')
    expect(badge.exists()).toBe(true)
    expect(badge.text()).toBe('knowledge')
  })

  it('displays script type badge', () => {
    const scriptSkill = { ...mockSkill, skill_type: 'script' as const }
    const wrapper = mount(SkillCard, {
      props: { skill: scriptSkill, isInstalled: false }
    })

    const badge = wrapper.find('[data-testid="skill-type-badge"]')
    expect(badge.text()).toBe('script')
  })

  it('shows install button when not installed', () => {
    const wrapper = mount(SkillCard, {
      props: { skill: mockSkill, isInstalled: false }
    })

    const installButton = wrapper.find('[data-testid="install-button"]')
    expect(installButton.exists()).toBe(true)
    expect(installButton.text()).toContain('安装')
  })

  it('shows installed status when already installed', () => {
    const wrapper = mount(SkillCard, {
      props: { skill: mockSkill, isInstalled: true }
    })

    expect(wrapper.text()).toContain('已安装')
    expect(wrapper.find('[data-testid="install-button"]').exists()).toBe(false)
  })

  it('has install button that can be clicked', () => {
    const wrapper = mount(SkillCard, {
      props: { skill: mockSkill, isInstalled: false }
    })

    const installButton = wrapper.find('[data-testid="install-button"]')
    expect(installButton.exists()).toBe(true)
    expect(installButton.attributes('disabled')).toBeUndefined()
  })

  it('has preview button that can be clicked', () => {
    const wrapper = mount(SkillCard, {
      props: { skill: mockSkill, isInstalled: false }
    })

    const previewButton = wrapper.find('[data-testid="preview-button"]')
    expect(previewButton.exists()).toBe(true)
    expect(previewButton.attributes('disabled')).toBeUndefined()
  })

  it('renders tags', () => {
    const wrapper = mount(SkillCard, {
      props: { skill: mockSkill, isInstalled: false }
    })

    const tags = wrapper.findAll('[data-testid="skill-tag"]')
    expect(tags.length).toBe(2)
    expect(tags[0].text()).toBe('ai')
    expect(tags[1].text()).toBe('test')
  })

  it('displays download count', () => {
    const wrapper = mount(SkillCard, {
      props: { skill: mockSkill, isInstalled: false }
    })

    expect(wrapper.text()).toContain('100')
  })
})
