import type { ApiEnvelope } from './types'

interface RequestOptions {
  method?: 'GET' | 'POST' | 'PUT' | 'DELETE'
  data?: unknown
  header?: Record<string, string>
}

function getBaseUrl(): string {
  return getApp<IAppOption>().globalData.baseUrl
}

function getOpenId(): string {
  return getApp<IAppOption>().globalData.openid || ''
}

function fullUrl(path: string): string {
  return `${getBaseUrl()}${path}`
}

function buildHeader(extra?: Record<string, string>): Record<string, string> {
  const header: Record<string, string> = {
    'content-type': 'application/json',
    'ngrok-skip-browser-warning': 'true',
    ...(extra || {}),
  }
  const openid = getOpenId()
  if (openid) header['X-OpenId'] = openid
  return header
}

export function request<T = unknown>(path: string, opts: RequestOptions = {}): Promise<T> {
  return new Promise((resolve, reject) => {
    wx.request({
      url: fullUrl(path),
      method: opts.method || 'GET',
      data: opts.data as WechatMiniprogram.IAnyObject,
      header: buildHeader(opts.header),
      success: (res) => {
        const body = res.data as ApiEnvelope<T>
        if (body && typeof body === 'object' && 'code' in body) {
          if (body.code === 0) {
            resolve(body.data)
          } else {
            wx.showToast({ title: body.msg || '请求失败', icon: 'none' })
            reject(new Error(body.msg || 'request failed'))
          }
        } else {
          reject(new Error('非标准响应'))
        }
      },
      fail: (e) => {
        wx.showToast({ title: '网络错误', icon: 'none' })
        reject(e)
      },
    })
  })
}

export function uploadFile<T = unknown>(path: string, filePath: string): Promise<T> {
  return new Promise((resolve, reject) => {
    const openid = getOpenId()
    wx.uploadFile({
      url: fullUrl(path),
      filePath,
      name: 'file',
      header: { 'ngrok-skip-browser-warning': 'true', ...(openid ? { 'X-OpenId': openid } : {}) },
      success: (res) => {
        try {
          const body = JSON.parse(res.data) as ApiEnvelope<T>
          if (body.code === 0) {
            resolve(body.data)
          } else {
            wx.showToast({ title: body.msg || '上传失败', icon: 'none' })
            reject(new Error(body.msg || 'upload failed'))
          }
        } catch (e) {
          reject(e)
        }
      },
      fail: (e) => {
        wx.showToast({ title: '上传失败', icon: 'none' })
        reject(e)
      },
    })
  })
}
