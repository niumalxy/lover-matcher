import { request } from '../../../services/api'
import type { CandidateSummary, ConversationOut } from '../../../services/types'

Page({
  data: {
    items: [] as CandidateSummary[],
    loading: true,
    baseUrl: '',
  },
  async onShow() {
    this.setData({ baseUrl: getApp<IAppOption>().globalData.baseUrl, loading: true })
    try {
      const items = await request<CandidateSummary[]>('/api/v1/candidates')
      this.setData({ items })
    } finally {
      this.setData({ loading: false })
    }
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
