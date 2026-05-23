import { request } from '../../../services/api'
import type { ConversationOut, MessageOut, SendMessageResult } from '../../../services/types'

Page({
  data: {
    convId: '',
    conv: null as ConversationOut | null,
    messages: [] as MessageOut[],
    input: '',
    sending: false,
    scrollIntoView: '',
  },
  async onLoad(query: Record<string, string>) {
    this.setData({ convId: query.id || '' })
    await this.refresh()
  },
  async refresh() {
    if (!this.data.convId) return
    const convs = await request<ConversationOut[]>('/api/v1/conversations/mine')
    const conv = convs.find((c) => c.id === this.data.convId) || null
    const messages = await request<MessageOut[]>(`/api/v1/conversations/${this.data.convId}/messages`)
    this.setData({ conv, messages })
    this.scrollToBottom()
  },
  scrollToBottom() {
    const msgs = this.data.messages
    if (msgs.length === 0) return
    this.setData({ scrollIntoView: `msg-${msgs[msgs.length - 1].id}` })
  },
  onInput(e: WechatMiniprogram.Input) {
    this.setData({ input: e.detail.value })
  },
  async onSend() {
    const content = this.data.input.trim()
    if (!content) return
    if (this.data.conv && this.data.conv.status !== 'active') {
      wx.showToast({ title: '会话已结束', icon: 'none' })
      return
    }
    this.setData({ sending: true, input: '' })
    try {
      const result = await request<SendMessageResult>(
        `/api/v1/conversations/${this.data.convId}/messages`,
        { method: 'POST', data: { content } }
      )
      await this.refresh()
      if (result.status === 'matched') {
        wx.showModal({
          title: '🎉 助手认为你们很合适',
          content: '已通知对方决定是否同意配对，可去「我发起的匹配」查看进度。',
          showCancel: false,
        })
      } else if (result.status === 'ended') {
        wx.showModal({
          title: '会话已结束',
          content: '助手认为暂不合适。可回到候选池看看其他人。',
          showCancel: false,
        })
      }
    } catch (e) {
      console.error(e)
    } finally {
      this.setData({ sending: false })
    }
  },
})
