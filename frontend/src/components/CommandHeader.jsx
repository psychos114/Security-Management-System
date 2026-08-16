import {
  SignOutIcon,
  UserCircleIcon,
} from '@phosphor-icons/react'


function CommandHeader({
  agentStatus,
  onCheckStatus,
  onLogout,
  user,
}) {
  return (
    <header className="command-header">
      <div className="command-title">
        <strong>医院物业安管系统</strong>
        <span>安管指挥台</span>
      </div>

      <div className="command-header-actions">
        <button
          className={
            `command-service-status `
            + `service-${agentStatus.state}`
          }
          type="button"
          onClick={onCheckStatus}
          disabled={
            agentStatus.state === 'loading'
          }
        >
          <span className="status-dot" />
          {agentStatus.message}
        </button>

        <div className="command-user">
          <UserCircleIcon
            size={30}
            weight="duotone"
          />

          <div>
            <strong>{user.display_name}</strong>
            <span>{user.role_name}</span>
          </div>
        </div>

        <button
          className="command-logout"
          type="button"
          title="退出登录"
          onClick={onLogout}
        >
          <SignOutIcon size={22} />
        </button>
      </div>
    </header>
  )
}


export default CommandHeader