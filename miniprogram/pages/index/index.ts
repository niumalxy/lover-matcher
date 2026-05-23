import { resetIdentity, getCurrentOpenId } from '../../services/auth'
import { request } from '../../services/api'
import type { UserOut } from '../../services/types'

Page({
  data: {
    openid: '',
    hasProfile: false,
  },
  async onShow() {
    const openid = getCurrentOpenId()
    this.setData({ openid })
    try {
      const user = await request<UserOut>('/api/v1/users/me')
      const hasProfile = Boolean(user.name && user.gender && user.expected_gender)
      this.setData({ hasProfile })
    } catch {
      this.setData({ hasProfile: false })
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
    if (this.data.hasProfile) {
      wx.navigateTo({ url: '/pages/matcher/candidates/candidates' })
    } else {
      wx.navigateTo({ url: '/pages/matchee/register/register' })
    }
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
