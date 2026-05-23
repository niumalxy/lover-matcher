import { request } from './api'

const STORAGE_KEY = 'lm_openid'

function genMockOpenId(): string {
  return 'dev_' + Math.random().toString(36).slice(2, 10)
}

// MVP 开发模式：由 app.ts 在模块初始化时同步设置 openid。
// 想模拟另一个用户：调 resetIdentity() 或在开发者工具里清缓存。
export function getCurrentOpenId(): string {
  return getApp<IAppOption>().globalData.openid || ''
}

export function resetIdentity(): void {
  wx.removeStorageSync(STORAGE_KEY)
  const app = getApp<IAppOption>()
  const openid = genMockOpenId()
  wx.setStorageSync(STORAGE_KEY, openid)
  app.globalData.openid = openid
  request('/api/v1/auth/login', { method: 'POST', data: { code: openid } }).catch(() => {})
}
