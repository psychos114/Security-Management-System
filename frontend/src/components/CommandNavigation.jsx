import {
  BookOpenIcon,
  ChartLineIcon,
  ChatCircleDotsIcon,
  ClipboardTextIcon,
  GearIcon,
  ShieldCheckIcon,
} from '@phosphor-icons/react'


const ACTIVE_ITEMS = [
  {
    id: 'command',
    label: '指挥对话',
    icon: ChatCircleDotsIcon,
  },
]


const PLANNED_ITEMS = [
  {
    id: 'tasks',
    label: '任务工单',
    icon: ClipboardTextIcon,
  },
  {
    id: 'knowledge',
    label: '知识库',
    icon: BookOpenIcon,
  },
  {
    id: 'reports',
    label: '报表中心',
    icon: ChartLineIcon,
  },
  {
    id: 'settings',
    label: '系统管理',
    icon: GearIcon,
  },
]


function CommandNavigation() {
  return (
    <nav
      className="command-navigation"
      aria-label="系统功能导航"
    >
      <div
        className="command-brand"
        title="医院物业安管系统"
      >
        <ShieldCheckIcon
          size={34}
          weight="fill"
        />
      </div>

      <div className="command-nav-list">
        {ACTIVE_ITEMS.map((item) => {
          const Icon = item.icon

          const isActive = item.id === 'command'

          return (
            <button
              className={
                `command-nav-button ${
                  isActive
                    ? 'is-active'
                    : ''
                }`
              }
              key={item.id}
              type="button"
              aria-current={
                isActive
                  ? 'page'
                  : undefined
              }
            >
              <Icon
                size={25}
                weight={
                  isActive
                    ? 'fill'
                    : 'regular'
                }
              />

              <span>{item.label}</span>
            </button>
          )
        })}

        <div className="command-nav-divider" />

        {PLANNED_ITEMS.map((item) => {
          const Icon = item.icon

          return (
            <button
              className="command-nav-button"
              key={item.id}
              type="button"
              title={`${item.label}（后续开发）`}
              disabled
            >
              <Icon
                size={24}
                weight="regular"
              />

              <span>{item.label}</span>
            </button>
          )
        })}
      </div>
    </nav>
  )
}


export default CommandNavigation
