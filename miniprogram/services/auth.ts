import { request } from './api'

const STORAGE_KEY = 'lm_openid'

function genMockOpenId(): string {
  return 'dev_' + Math.random().toString(36).slice(2, 10)
}

// MVP 开发模式：本地生成并持久化一个 mock openid，后端 dev_mode 把 code 当 openid。
// 想模拟另一个用户：调 resetIdentity() 或在开发者工具里清缓存。
export async function ensureLogin(): Promise<string> {
  const app = getApp<IAppOption>()
  let openid = wx.getStorageSync(STORAGE_KEY) as string
  if (!openid) {
    openid = genMockOpenId()
    wx.setStorageSync(STORAGE_KEY, openid)
  }
  app.globalData.openid = openid
  await request('/api/v1/auth/login', { method: 'POST', data: { code: openid } })
  return openid
}

export function getCurrentOpenId(): string {
  return getApp<IAppOption>().globalData.openid || ''
}

export function resetIdentity(): void {
  wx.removeStorageSync(STORAGE_KEY)
  getApp<IAppOption>().globalData.openid = ''
}
