import * as api from '@/api'
import IconFile from '@/assets/component/file.svg'
import IconSend from '@/components/icons/IconSend'
import { sessionActions, sessionState } from '@/store/session'
import {
  GlobalOutlined,
  LoadingOutlined,
  ReadOutlined,
} from '@ant-design/icons'
import { Button, Input, Space, Upload, UploadFile } from 'antd'
import classNames from 'classnames'
import { PropsWithChildren, useMemo, useState } from 'react'
import { useSnapshot } from 'valtio'
import './index.scss'

const IconFile2 = (
  <svg
    className="com-sender__file-icon"
    xmlns="http://www.w3.org/2000/svg"
    width="24"
    height="24"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="2"
    strokeLinecap="round"
    strokeLinejoin="round"
    aria-hidden="true"
  >
    <path d="M15 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7Z"></path>
    <path d="M14 2v4a2 2 0 0 0 2 2h4"></path>
    <path d="M10 9H8"></path>
    <path d="M16 13H8"></path>
    <path d="M16 17H8"></path>
  </svg>
)

export default function ComSender(
  props: PropsWithChildren<{
    className?: string
    loading?: boolean
    onSend?: (value: string, files: string[]) => void | Promise<void>
    onContract?: () => void
  }>,
) {
  const { className, onSend, onContract, loading, ...rest } = props
  const [value, setValue] = useState('')
  const [fileList, setFileList] = useState<
    (UploadFile & {
      loading?: boolean
    })[]
  >([])

  const uploading = useMemo(() => {
    return fileList.some((file) => file.loading)
  }, [fileList])

  const session = useSnapshot(sessionState)

  const handleClickUpload = () => {
    if (session.useDeep) {
      window.$app.message.warning('深度探索模式下不能上传附件')
      return
    }
  }

  async function send() {
    if (uploading) {
      window.$app.message.info('正在上传中，请耐心等待')
      return
    }
    if (loading) return
    if (!value) return
    await onSend?.(
      value,
      fileList.filter((item) => item.url).map((item) => item.url!),
    )
    setValue('')
    setFileList([])
  }

  async function upload(
    file: UploadFile & {
      loading?: boolean
    },
  ) {
    if (fileList.length >= 10) {
      window.$app.message.error('最多只能上传 10 个附件')
      return
    }

    file.loading = true

    if (file.type?.startsWith('image/')) {
      file.preview = URL.createObjectURL(file as any)
    }

    setFileList((prev) => [...prev, file])

    try {
      const { data } = await api.session.upload({ files: file as any })
      file.url = data.url

      window.$app.message.success(`${file.name} 上传成功`)
    } catch (error) {
      window.$app.message.error(`${file.name} 上传失败`)
    } finally {
      file.loading = false
      setFileList((prev) => [...prev])
    }
  }

  return (
    <div className={classNames('com-sender', className)} {...rest}>
      {fileList.length ? (
        <div className="com-sender__files">
          {fileList.map((file) => (
            <div key={file.uid} className="com-sender__file">
              {file.type?.startsWith('image/') ? (
                <img className="com-sender__file-image" src={file.preview} />
              ) : (
                <>
                  {IconFile2}
                  <div className="com-sender__file-name" title={file.name}>
                    {file.name}
                  </div>
                </>
              )}
            </div>
          ))}
        </div>
      ) : null}

      <div className="com-sender__main">
        <Input.TextArea
          value={value}
          onChange={(e) => setValue(e.target.value)}
          placeholder="按 Enter 发送，Shift + Enter 换行"
          autoSize={{ minRows: 2 }}
          autoFocus
          onPressEnter={(e) => {
            if (!e.shiftKey) {
              e.preventDefault()
              send()
            }
          }}
        />

        <div className="com-sender__actions">
          <Space className="com-sender__actions-left" size={12}>
            {
              <Upload
                accept=".doc, .docx, .pdf, application/msword, application/pdf"
                disabled={session.useDeep}
                showUploadList={false}
                beforeUpload={(file) => {
                  upload(file)
                  return false
                }}
              >
                <Button
                  variant="text"
                  color="default"
                  onClick={handleClickUpload}
                >
                  {uploading ? <LoadingOutlined /> : <img src={IconFile} />}
                  附件
                </Button>
              </Upload>
            }

            <Button
              color={session.useDeep ? 'primary' : 'default'}
              variant={session.useDeep ? 'filled' : 'outlined'}
              icon={<ReadOutlined />}
              onClick={() => sessionActions.setUseDeep(!session.useDeep)}
            >
              深度探索
            </Button>

            <Button
              color={session.useWeb ? 'primary' : 'default'}
              variant={session.useWeb ? 'filled' : 'outlined'}
              icon={<GlobalOutlined />}
            >
              网络搜索
            </Button>
          </Space>

          <Space className="com-sender__actions-right" size={12}>
            <Button
              className="btn-send"
              color="primary"
              variant="filled"
              onClick={send}
              loading={loading}
              disabled={!value && !fileList.length}
              icon={<IconSend />}
            ></Button>
          </Space>
        </div>
      </div>

      {/* <div className="com-sender__footer">
        <Space></Space>
      </div> */}
    </div>
  )
}
