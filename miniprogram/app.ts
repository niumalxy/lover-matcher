import { ensureLogin } from './services/auth'

App<IAppOption>({
  globalData: {
    baseUrl: 'http://localhost:8000',
    openid: '',
  },
  onLaunch() {
    ensureLogin().catch((e) => console.error('[lm] login failed', e))
  },
})
