import IconNewChat from '@/assets/layout/newchat.svg'
import StoreImage from '@/assets/layout/store.svg'
// eslint-disable-next-line @typescript-eslint/no-unused-vars
// eslint-disable-next-line @typescript-eslint/no-unused-vars
import IconVip from '@/assets/layout/vip.svg'
import { Avatar } from 'antd'
import { useMemo } from 'react'
import { Link } from 'react-router-dom'
import './nav.scss'

export function Nav() {
  const list = useMemo(
    () => [
      {
        key: '1',
        label: '新对话',
        icon: IconNewChat,
        href: '/',
      },
      {
        key: '2',
        label: '文档',
        icon: StoreImage,
        href: '/repository',
      },
      // {
      //   key: '3',
      //   label: '设置',
      //   icon: IconSetting,
      // },
      // {
      //   key: '4',
      //   label: '',
      //   icon: IconQuestion,
      // },
      {
        key: '5',
        label: '充值',
        icon: IconVip,
        href: '/pricing',
      },
    ],
    [],
  )

  return (
    <div className="base-layout-nav">
      {list.map((item) => (
        <Link
          className="base-layout-nav__item"
          key={item.key}
          title={item.label}
          to={item.href ?? '#'}
        >
          <img src={item.icon} alt={item.label} />
        </Link>
      ))}

      <Avatar>W</Avatar>
    </div>
  )
}
