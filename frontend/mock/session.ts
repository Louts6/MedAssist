import fs from 'node:fs'
import { MockMethod } from 'vite-plugin-mock'

export default [
  {
    url: '/api/create_session', // 模拟登录的链接
    method: 'post', // 请求方式
    timeout: 500, // 超时时间
    statusCode: 200, // 返回的http状态码
    response: {
      session_id: 'abcdef1234567890',
      status: 'success',
      message: 'Session created successfully',
    },
  },
  {
    url: '/api/ai_search/',
    method: 'post',
    rawResponse: async (req, res) => {
      const datas = fs.readFileSync('./mock/data/chat').toString().split('\n')

      res.setHeader('Content-Type', 'text/event-stream')
      res.setHeader('Cache-Control', 'no-cache')
      res.setHeader('Connection', 'keep-alive')
      res.flushHeaders()

      for (let i = 0; i < datas.length; i += 1) {
        await sleep(1)
        res.write(datas[i])
        res.write('\n')
      }

      res.end()

      function sleep(ms: number) {
        return new Promise((resolve) => setTimeout(resolve, ms))
      }
    },
  },
  {
    url: '/api/upload_files/',
    method: 'post',
    rawResponse: async (req, res) => {
      await new Promise((resolve) => setTimeout(resolve, 1000))
      res.end()
    },
  },
  {
    url: '/api/get_messages',
    method: 'get',
    response: {
      data: [],
    },
  },
] as MockMethod[]
