import { request } from '../../../services/api'
import type { MatchOut } from '../../../services/types'

Page({
  data: {
    items: [] as MatchOut[],
    loading: true,
  },
  async onShow() {
    this.setData({ loading: true })
    try {
      const items = await request<MatchOut[]>('/api/v1/matches/pending')
      this.setData({ items })
    } finally {
      this.setData({ loading: false })
    }
  },
  goDetail(e: WechatMiniprogram.BaseEvent) {
    const id = e.currentTarget.dataset.id as string
    wx.navigateTo({ url: `/pages/matchee/matchDetail/matchDetail?id=${id}` })
  },
})
