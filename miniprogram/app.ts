const STORAGE_KEY = 'lm_openid'

function initOpenId(): string {
  let openid = wx.getStorageSync(STORAGE_KEY) as string
  if (typeof openid !== 'string' || !openid) {
    openid = 'dev_' + Math.random().toString(36).slice(2, 10)
    wx.setStorageSync(STORAGE_KEY, openid)
  }
  return openid
}

const openid = initOpenId()

App<IAppOption>({
  globalData: {
    baseUrl: 'https://stretch-wildfire-blouse.ngrok-free.dev',
    openid,
  },
})
