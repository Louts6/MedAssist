import useSendMessage from '@/utils/useSendMessage'
import { debounce } from 'throttle-debounce'
import styles from './index.module.scss'

interface HotQuestion {
  emoji: string
  title: string
}

interface HotQuestionsProps {
  list?: HotQuestion[]
}

const list: HotQuestion[] = [
  {
    emoji: '🩺',
    title: '高血压患者会有哪些典型症状？',
  },
  {
    emoji: '💊',
    title: '二甲双胍的用法用量和注意事项',
  },
  {
    emoji: '📋',
    title: '体检报告里转氨酶偏高意味着什么？',
  },
  {
    emoji: '🫀',
    title: '冠心病的诊断标准和治疗方案有哪些？',
  },
  {
    emoji: '�',
    title: '糖尿病患者日常饮食应该注意什么？',
  },
]

export default function HotQuestions(props: HotQuestionsProps) {
  console.log('props', props)

  const sendMessage = useSendMessage()
  // 使用防抖处理点击事件，300ms内只触发一次
  const handleClick = debounce(300, (question: HotQuestion) => {
    sendMessage(question.title)
  })

  return (
    <div className={styles.hotQuestions}>
      {list.map((question) => (
        <div
          key={question.title}
          className={styles.hotQuestion}
          onClick={() => handleClick(question)}
        >
          <span className={styles.emoji}>{question.emoji}</span>
          <span className={styles.title}>{question.title}</span>
        </div>
      ))}
    </div>
  )
}
