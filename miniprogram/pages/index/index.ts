import { resetIdentity, getCurrentOpenId } from '../../services/auth'
import { request } from '../../services/api'
import type { UserOut } from '../../services/types'

Page({
  data: {
    openid: '',
    hasBasicInfo: false,
    hasProfile: false,
    loading: true,
  },
  async onShow() {
    const openid = getCurrentOpenId()
    this.setData({ openid, loading: false })
    try {
      await request('/api/v1/auth/login', { method: 'POST', data: { code: openid } })
    } catch {
      // login 失败则后续 /users/me 也会 401
    }
    try {
      const user = await request<UserOut>('/api/v1/users/me')
      const hasBasicInfo = Boolean(user.name && user.gender)
      const hasProfile = Boolean(user.name && user.gender && user.expected_gender)
      this.setData({ hasBasicInfo, hasProfile })
      if (!hasBasicInfo) {
        wx.redirectTo({ url: '/pages/matchee/register/register' })
      }
    } catch {
      this.setData({ hasBasicInfo: false, hasProfile: false })
    }
  },
  goMatchee() {
    if (this.data.hasProfile) {
      wx.navigateTo({ url: '/pages/matchee/profile/profile' })
    } else {
      wx.navigateTo({ url: '/pages/matchee/register/register' })
    }
  },
  goMatcher() {
    wx.navigateTo({ url: '/pages/matcher/candidates/candidates' })
  },
  goInbox() {
    wx.navigateTo({ url: '/pages/matchee/inbox/inbox' })
  },
  goMatched() {
    wx.navigateTo({ url: '/pages/matcher/matched/matched' })
  },
  onReset() {
    wx.showModal({
      title: '重置身份',
      content: '会清空本地登录态，下次启动小程序会生成新身份。仅开发期使用。',
      success: (res) => {
        if (res.confirm) {
          resetIdentity()
          wx.reLaunch({ url: '/pages/index/index' })
        }
      },
    })
  },
})
