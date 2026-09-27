import * as api from '@/api'
import ComPageLayout from '@/components/page-layout'
import ComSender from '@/components/sender'
import { ChatRole, ChatType } from '@/configs'
import { deviceActions } from '@/store/device'
import { sessionState } from '@/store/session'
import { usePageTransport } from '@/utils'
import { useMount, useRequest, useUnmount } from 'ahooks'
import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { useParams } from 'react-router-dom'
import { proxy, useSnapshot } from 'valtio'
import ChatMessage from './component/chat-message'
import styles from './index.module.scss'
import { createChatId, transportToChatEnter } from './shared'

// 滚动到页面底部的辅助函数，当距离底部小于阈值时自动滚动
async function scrollToBottom() {
  await new Promise((resolve) => setTimeout(resolve))

  const threshold = 200
  const distanceToBottom =
    document.documentElement.scrollHeight -
    document.documentElement.scrollTop -
    document.documentElement.clientHeight

  if (distanceToBottom <= threshold) {
    window.scrollTo({
      top: document.documentElement.scrollHeight,
      behavior: 'smooth',
    })
  }
}

export default function Index() {
  const { id } = useParams()
  const { data: ctx } = usePageTransport(transportToChatEnter)
  const sessionStore = useSnapshot(sessionState)

  // 使用valtio管理聊天消息列表状态
  const [chat] = useState(() => {
    return proxy({
      list: [] as API.ChatItem[],
    })
  })
  const { list } = useSnapshot(chat) as { list: API.ChatItem[] }

  // 加载聊天历史记录
  const history = useRequest(
    async () => {
      const { data } = await api.session.detail({
        session_id: id!,
      })
      return data
    },
    {
      manual: true,
      onSuccess(data) {
        data.forEach((item) => {
          if (item.user_question) {
            chat.list.push({
              id: createChatId(),
              role: ChatRole.User,
              type: ChatType.Text,
              content: item.user_question,
            })
          }

          if (item.model_answer) {
            let reference: API.Reference[] = []
            let recommended_questions: string[] = []

            if (item.documents) {
              try {
                reference = JSON.parse(item.documents) as API.Reference[]
              } catch (error) {
                console.error(error)
              }
            }

            if (item.recommended_questions) {
              try {
                // 后端返回的最后一条内容的最前面有多余字符`"`，需要去掉
                recommended_questions = (item.recommended_questions || []).map(
                  (q) => q.replace(/^"/, ''),
                )
              } catch (error) {
                console.error(error)
              }
            }

            chat.list.push({
              id: createChatId(),
              role: ChatRole.Assistant,
              type: ChatType.Document,
              content: item.model_answer,
              think: item.think,
              reference: reference,
              recommended_questions: recommended_questions?.length
                ? recommended_questions
                : undefined,
            })
          }
        })

        setTimeout(() => {
          window.scrollTo({
            top: document.documentElement.scrollHeight,
          })
        })
      },
    },
  )

  const loading = useMemo(() => {
    return list.some((o) => o.loading) || history.loading
  }, [list, history.loading])
  const loadingRef = useRef(loading)
  loadingRef.current = loading
  useEffect(() => {
    deviceActions.setChatting(loading)
  }, [loading])
  useUnmount(() => {
    deviceActions.setChatting(false)
  })

  // 发送聊天消息并处理流式响应
  const sendChat = useCallback(
    async (target: API.ChatItem, message: string, attachments?: string[]) => {
      target.loading = true
      try {
        const res = await api.session.chat({
          id: id!,
          message,
          web_search: sessionStore.useWeb,
          deep_research: sessionStore.useDeep,
          attachments: attachments,
        })

        // 获取流式响应的reader
        const reader = res.data.getReader()
        if (!reader) return

        await read(reader)
      } catch (error: unknown) {
        target.error = (error as Error)?.message ?? 'Unknown error'
        throw error
      } finally {
        target.loading = false
      }

      // 读取流式响应数据
      async function read(
        reader: ReadableStreamDefaultReader<AllowSharedBufferSource>,
      ) {
        let temp = ''
        const decoder = new TextDecoder('utf-8')
        while (true) {
          const { value, done } = await reader.read()
          temp += decoder.decode(value)

          // 按行解析SSE数据
          while (true) {
            const index = temp.indexOf('\n')
            if (index === -1) break

            const slice = temp.slice(0, index)
            temp = temp.slice(index + 1)

            if (slice.startsWith('data: ')) {
              parseData(slice)
              scrollToBottom()
            }
          }

          if (done) {
            console.debug('数据接受完毕', temp)
            target.loading = false
            break
          }
        }
      }

      // 解析SSE数据并更新聊天消息
      function parseData(slice: string) {
        try {
          const str = slice
            .trim()
            .replace(/^data: /, '')
            .trim()
          if (str === '[DONE]') {
            return
          }

          const json = JSON.parse(str)
          // 处理内容更新，区分思考内容和回答内容
          if (json?.content) {
            if (json.thinking) {
              target.think = `${target.think || ''}${json.content || ''}`
            } else {
              target.content = `${target.content || ''}${json.content || ''}`
            }
          }

          // 处理参考文档
          if (json?.documents?.length) {
            target.reference = json.documents
          }

          // 处理推荐问题
          if (json?.recommended_questions?.length) {
            target.recommended_questions = json.recommended_questions
          }

          // 处理图片结果
          if (json?.image_results) {
            target.image_results = json.image_results
          }

          // 处理视频结果
          if (json?.video_results) {
            target.video_results = json.video_results
          }
        } catch {
          console.debug('解析失败')
          console.debug(slice)
        }
      }
    },
    [chat],
  )

  // 发送消息的主函数，处理用户输入并创建对话项
  const send = useCallback(
    async (message: string, attachments?: string[]) => {
      if (loadingRef.current) return
      if (!message) return

      if (chat.list.length === 0) {
        // 首次发送消息，创建用户消息和AI回复占位
        chat.list.push({
          id: createChatId(),
          role: ChatRole.User,
          type: ChatType.Text,
          content: message,
        })

        chat.list.push({
          id: createChatId(),
          role: ChatRole.Assistant,
          type: ChatType.Document,
          documents: [],
        })

        const target = chat.list[chat.list.length - 1]

        await sendChat(target, message!, attachments)
      } else {
        // 非首次发送，添加新的对话项
        chat.list.push({
          id: createChatId(),
          role: ChatRole.User,
          type: ChatType.Text,
          content: message,
        })

        chat.list.push({
          id: createChatId(),
          role: ChatRole.Assistant,
          type: ChatType.Document,
          content: '',
        })
        scrollToBottom()

        const target = chat.list[chat.list.length - 1]

        await sendChat(target, message!, attachments)
      }
    },
    [chat, sendChat],
  )
  // 组件挂载时，处理页面间传递的消息或加载历史记录
  useMount(async () => {
    if (ctx?.data.message) {
      send(ctx.data.message)
    } else {
      history.run()
    }
  })

  return (
    <ComPageLayout sender={<ComSender loading={loading} onSend={send} />}>
      <div className={styles['chat-page']}>
        <ChatMessage
          list={list}
          loading={loading}
          deepResearch={sessionStore.useDeep}
          onSend={send}
        />
      </div>
    </ComPageLayout>
  )
}
