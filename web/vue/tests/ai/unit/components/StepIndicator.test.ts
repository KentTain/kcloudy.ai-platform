// tests/ai/unit/components/StepIndicator.test.ts
import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import StepIndicator from '@/components/ai-elements/step/StepIndicator.vue'

describe('StepIndicator', () => {
  it('renders steps with correct status', () => {
    const wrapper = mount(StepIndicator, {
      props: {
        steps: [
          { title: 'Step 1', status: 'done' },
          { title: 'Step 2', status: 'active' },
          { title: 'Step 3', status: 'pending' },
        ]
      }
    })

    expect(wrapper.findAll('.step-item')).toHaveLength(3)
    expect(wrapper.text()).toContain('Step 1')
    expect(wrapper.text()).toContain('Step 2')
    expect(wrapper.text()).toContain('Step 3')
  })

  it('displays check icon for done steps', () => {
    const wrapper = mount(StepIndicator, {
      props: {
        steps: [{ title: 'Done', status: 'done' }]
      }
    })

    expect(wrapper.find('.check-icon').exists()).toBe(true)
  })

  it('displays spinner for active steps', () => {
    const wrapper = mount(StepIndicator, {
      props: {
        steps: [{ title: 'Active', status: 'active' }]
      }
    })

    expect(wrapper.find('.spinner-icon').exists()).toBe(true)
  })
})
