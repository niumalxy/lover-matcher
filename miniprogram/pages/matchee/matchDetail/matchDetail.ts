import { request } from '../../../services/api'
import type { MatchOut, MessageOut } from '../../../services/types'

Page({
  data: {
    matchId: '',
    match: null as MatchOut | null,
    messages: [] as MessageOut[],
    deciding: false,
  },
  async onLoad(query: Record<string, string>) {
    this.setData({ matchId: query.id || '' })
    await this.refresh()
  },
  async refresh() {
    if (!this.data.matchId) return
    const match = await request<MatchOut>(`/api/v1/matches/${this.data.matchId}`)
    const messages = await request<MessageOut[]>(`/api/v1/conversations/${match.conversation_id}/messages`)
    this.setData({ match, messages })
  },
  async decide(e: WechatMiniprogram.BaseEvent) {
    const decision = e.currentTarget.dataset.decision as 'approved' | 'rejected'
    this.setData({ deciding: true })
    wx.showLoading({ title: '处理中...' })
    try {
      await request(`/api/v1/matches/${this.data.matchId}/decision`, {
        method: 'POST',
        data: { decision },
      })
      wx.hideLoading()
      wx.showToast({ title: decision === 'approved' ? '已同意，可查看联系方式' : '已拒绝', icon: 'success' })
      await this.refresh()
    } catch (e2) {
      wx.hideLoading()
      console.error(e2)
    } finally {
      this.setData({ deciding: false })
    }
  },
})
