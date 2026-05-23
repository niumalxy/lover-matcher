import { request } from '../../../services/api'
import type { CandidateListResult, CandidateSummary, ConversationOut } from '../../../services/types'

Page({
  data: {
    items: [] as CandidateSummary[],
    myUserId: '',
    loading: true,
    baseUrl: '',
    genderFilter: '' as string,
    genderOptions: [
      { label: '不限', value: '' },
      { label: '男', value: 'M' },
      { label: '女', value: 'F' },
    ],
  },
  async onShow() {
    this.setData({ baseUrl: getApp<IAppOption>().globalData.baseUrl, loading: true })
    await this.loadCandidates()
  },
  async loadCandidates() {
    const gender = this.data.genderFilter
    let url = '/api/v1/candidates'
    if (gender) {
      url += `?gender=${gender}`
    }
    try {
      const res = await request<CandidateListResult>(url)
      this.setData({ items: res.items, myUserId: res.viewer_user_id })
    } finally {
      this.setData({ loading: false })
    }
  },
  onGenderChange(e: WechatMiniprogram.TouchEvent) {
    const value = e.currentTarget.dataset.value as string
    this.setData({ genderFilter: value, loading: true, items: [] })
    this.loadCandidates()
  },
  async tapCandidate(e: WechatMiniprogram.BaseEvent) {
    const matcheeUserId = e.currentTarget.dataset.id as string
    wx.showLoading({ title: '创建会话...' })
    try {
      const conv = await request<ConversationOut>('/api/v1/conversations', {
        method: 'POST',
        data: { matchee_user_id: matcheeUserId },
      })
      wx.hideLoading()
      wx.navigateTo({ url: `/pages/matcher/chat/chat?id=${conv.id}` })
    } catch (e2) {
      wx.hideLoading()
      console.error(e2)
    }
  },
})
