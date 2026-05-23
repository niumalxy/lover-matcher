import { request, uploadFile } from '../../../services/api'
import type { UserOut } from '../../../services/types'

interface UploadAvatarResult {
  avatar_url: string
}

Page({
  data: {
    name: '',
    gender: 'F' as 'M' | 'F',
    expected_gender: 'M' as 'M' | 'F' | 'ANY',
    contact: '',
    avatarUrl: '',
    avatarLocalPath: '',
  },
  async onLoad() {
    try {
      const user = await request<UserOut>('/api/v1/users/me')
      this.setData({
        name: user.name,
        gender: (user.gender || 'F') as 'M' | 'F',
        expected_gender: (user.expected_gender || 'M') as 'M' | 'F' | 'ANY',
        contact: user.contact,
        avatarUrl: user.avatar_url ? `${getApp<IAppOption>().globalData.baseUrl}${user.avatar_url}` : '',
      })
    } catch {
      // ignore
    }
  },
  onNameInput(e: WechatMiniprogram.Input) {
    this.setData({ name: e.detail.value })
  },
  onContactInput(e: WechatMiniprogram.Input) {
    this.setData({ contact: e.detail.value })
  },
  onGenderChange(e: WechatMiniprogram.RadioGroupChange) {
    this.setData({ gender: e.detail.value as 'M' | 'F' })
  },
  onExpectedGenderChange(e: WechatMiniprogram.RadioGroupChange) {
    this.setData({ expected_gender: e.detail.value as 'M' | 'F' | 'ANY' })
  },
  chooseAvatar() {
    wx.chooseMedia({
      count: 1,
      mediaType: ['image'],
      sourceType: ['album', 'camera'],
      success: (res) => {
        this.setData({ avatarLocalPath: res.tempFiles[0].tempFilePath })
      },
    })
  },
  async onSubmit() {
    if (!this.data.name) {
      wx.showToast({ title: '请填写姓名', icon: 'none' })
      return
    }
    wx.showLoading({ title: '保存中...' })
    try {
      await request('/api/v1/users/me', {
        method: 'PUT',
        data: {
          name: this.data.name,
          gender: this.data.gender,
          expected_gender: this.data.expected_gender,
          contact: this.data.contact,
        },
      })
      if (this.data.avatarLocalPath) {
        const result = await uploadFile<UploadAvatarResult>(
          '/api/v1/users/me/avatar',
          this.data.avatarLocalPath
        )
        this.setData({ avatarUrl: `${getApp<IAppOption>().globalData.baseUrl}${result.avatar_url}` })
      }
      wx.hideLoading()
      wx.showToast({ title: '已保存', icon: 'success' })
      setTimeout(() => {
        wx.redirectTo({ url: '/pages/index/index' })
      }, 600)
    } catch (e) {
      wx.hideLoading()
      console.error(e)
    }
  },
})
