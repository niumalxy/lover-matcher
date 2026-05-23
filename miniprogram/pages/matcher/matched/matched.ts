import { request } from '../../../services/api'
import type { MatchOut, UserOut } from '../../../services/types'

Page({
  data: {
    items: [] as MatchOut[],
    loading: true,
    userId: '',
  },
  async onShow() {
    this.setData({ loading: true })
    try {
      const me = await request<UserOut>('/api/v1/users/me')
      this.setData({ userId: me.id })
      const all = await request<MatchOut[]>('/api/v1/matches/mine')
      const items = all.filter((m) => m.matcher_user_id === me.id)
      this.setData({ items })
    } finally {
      this.setData({ loading: false })
    }
  },
})
