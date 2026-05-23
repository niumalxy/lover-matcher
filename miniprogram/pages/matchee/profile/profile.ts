import { request } from '../../../services/api'
import type { CustomQuestion, ProfileOut, StructuredProfile } from '../../../services/types'

const PRIORITY_VALUES: Array<CustomQuestion['priority']> = ['low', 'medium', 'high']

function arrToText(arr: string[]): string {
  return (arr || []).join('\n')
}

function textToArr(text: string): string[] {
  return (text || '')
    .split('\n')
    .map((s) => s.trim())
    .filter(Boolean)
}

Page({
  data: {
    raw_input: '',
    self_intro: '',
    personality_text: '',
    hobbies_text: '',
    hard_text: '',
    soft_text: '',
    speaking_style: '',
    customQuestions: [] as Array<CustomQuestion & { priorityIndex: number }>,
    priorityOptions: ['低', '中', '高'],
    priorityLabels: { low: '低', medium: '中', high: '高' },
    hasStructured: false,
    extracting: false,
    saving: false,
  },
  async onLoad() {
    try {
      const prof = await request<ProfileOut | null>('/api/v1/profile')
      if (prof && prof.structured) {
        this.fillStructured(prof.structured, prof.raw_input)
      }
    } catch {
      // ignore
    }
  },
  fillStructured(s: StructuredProfile, raw: string) {
    const questions = (s.custom_questions || []).map((q) => ({
      ...q,
      priorityIndex: PRIORITY_VALUES.indexOf(q.priority),
    }))
    this.setData({
      raw_input: raw,
      self_intro: s.self_intro,
      personality_text: arrToText(s.personality),
      hobbies_text: arrToText(s.hobbies),
      hard_text: arrToText(s.hard_requirements),
      soft_text: arrToText(s.soft_requirements),
      speaking_style: s.speaking_style,
      customQuestions: questions,
      hasStructured: true,
    })
  },
  onRawInput(e: WechatMiniprogram.Input) {
    this.setData({ raw_input: e.detail.value })
  },
  onIntroInput(e: WechatMiniprogram.Input) { this.setData({ self_intro: e.detail.value }) },
  onPersonalityInput(e: WechatMiniprogram.Input) { this.setData({ personality_text: e.detail.value }) },
  onHobbiesInput(e: WechatMiniprogram.Input) { this.setData({ hobbies_text: e.detail.value }) },
  onHardInput(e: WechatMiniprogram.Input) { this.setData({ hard_text: e.detail.value }) },
  onSoftInput(e: WechatMiniprogram.Input) { this.setData({ soft_text: e.detail.value }) },
  onStyleInput(e: WechatMiniprogram.Input) { this.setData({ speaking_style: e.detail.value }) },
  onAddQuestion() {
    const q = {
      question: '',
      ideal_answer: '',
      priority: 'medium' as CustomQuestion['priority'],
      priorityIndex: 1,
    }
    this.setData({ customQuestions: [...this.data.customQuestions, q] })
  },
  onQuestionInput(e: WechatMiniprogram.Input) {
    const index = e.currentTarget.dataset.index
    this.setData({ [`customQuestions[${index}].question`]: e.detail.value })
  },
  onAnswerInput(e: WechatMiniprogram.Input) {
    const index = e.currentTarget.dataset.index
    this.setData({ [`customQuestions[${index}].ideal_answer`]: e.detail.value })
  },
  onPriorityChange(e: WechatMiniprogram.PickerChange) {
    const index = e.currentTarget.dataset.index
    const priorityIndex = parseInt(e.detail.value as string, 10)
    const priority = PRIORITY_VALUES[priorityIndex]
    this.setData({
      [`customQuestions[${index}].priority`]: priority,
      [`customQuestions[${index}].priorityIndex`]: priorityIndex,
    })
  },
  onRemoveQuestion(e: WechatMiniprogram.TouchEvent) {
    const index = e.currentTarget.dataset.index
    const list = [...this.data.customQuestions]
    list.splice(index, 1)
    this.setData({ customQuestions: list })
  },
  async onExtract() {
    if (!this.data.raw_input.trim()) {
      wx.showToast({ title: '请先输入描述', icon: 'none' })
      return
    }
    this.setData({ extracting: true })
    wx.showLoading({ title: 'AI 提取中...' })
    try {
      const r = await request<{ structured: StructuredProfile }>('/api/v1/profile/extract', {
        method: 'POST',
        data: { raw_input: this.data.raw_input },
      })
      this.fillStructured(r.structured, this.data.raw_input)
      wx.hideLoading()
      wx.showToast({ title: '提取完成，可调整', icon: 'success' })
    } catch (e) {
      wx.hideLoading()
      console.error(e)
    } finally {
      this.setData({ extracting: false })
    }
  },
  async onSubmit() {
    if (!this.data.hasStructured) {
      wx.showToast({ title: '请先点 AI 提取', icon: 'none' })
      return
    }
    const structured: StructuredProfile = {
      self_intro: this.data.self_intro,
      personality: textToArr(this.data.personality_text),
      hobbies: textToArr(this.data.hobbies_text),
      hard_requirements: textToArr(this.data.hard_text),
      soft_requirements: textToArr(this.data.soft_text),
      speaking_style: this.data.speaking_style,
      custom_questions: this.data.customQuestions.map((q) => ({
        question: q.question,
        ideal_answer: q.ideal_answer,
        priority: q.priority,
      })),
    }
    this.setData({ saving: true })
    wx.showLoading({ title: '保存中...' })
    try {
      await request('/api/v1/profile', {
        method: 'PUT',
        data: { raw_input: this.data.raw_input, structured },
      })
      wx.hideLoading()
      wx.showToast({ title: '已保存，进入候选池', icon: 'success' })
      setTimeout(() => {
        wx.reLaunch({ url: '/pages/index/index' })
      }, 800)
    } catch (e) {
      wx.hideLoading()
      console.error(e)
    } finally {
      this.setData({ saving: false })
    }
  },
})
