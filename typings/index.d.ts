/// <reference path="./types/index.d.ts" />

interface IAppOption {
  globalData: {
    baseUrl: string
    openid: string
    userInfo?: WechatMiniprogram.UserInfo
  }
  userInfoReadyCallback?: WechatMiniprogram.GetUserInfoSuccessCallback
}
