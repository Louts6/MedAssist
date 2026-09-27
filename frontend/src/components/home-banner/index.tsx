import decImg from '../../assets/home_banner_dec.png'
import portraitImg from '../../assets/home_banner_portrait.png'
import styles from './index.module.scss'

export default function HomeBanner() {
  return (
    <div className={styles.banner}>
      <div className={styles.content}>
        <h1 className={styles.title}>智能问诊助手</h1>
        <p className={styles.subtitle}>医学文献库 + 检查报告解析 + 诊疗指南Agent~</p>
      </div>
      <div className={styles.decoration}>
        <img src={portraitImg} alt="培训助手" className={styles.portrait} />
        <img src={decImg} alt="装饰背景" className={styles.decImage} />
      </div>
    </div>
  )
}
