import { useState } from 'react'


function LoginPanel({
  errorMessage,
  isSubmitting,
  onLogin,
}) {
  const [username, setUsername] =
    useState('demo.security')

  const [password, setPassword] =
    useState('')

  const canSubmit =
    username.trim().length >= 3
    && password.length > 0
    && !isSubmitting

  async function handleSubmit(event) {
    event.preventDefault()

    if (!canSubmit) {
      return
    }

    await onLogin(
      username.trim(),
      password,
    )
  }

  return (
    <main className="auth-page">
      <section className="login-card">
        <p className="eyebrow">
          SECURITY MANAGEMENT
        </p>

        <h1>医院物业安管系统</h1>

        <p className="login-description">
          请使用系统账号登录。登录身份将用于
          关键动作审批和巡检照片分析记录。
        </p>

        <form
          className="login-form"
          onSubmit={handleSubmit}
        >
          <label htmlFor="login-username">
            用户名
          </label>

          <input
            id="login-username"
            type="text"
            value={username}
            minLength={3}
            maxLength={100}
            autoComplete="username"
            disabled={isSubmitting}
            onChange={(event) => {
              setUsername(event.target.value)
            }}
          />

          <label htmlFor="login-password">
            密码
          </label>

          <input
            id="login-password"
            type="password"
            value={password}
            autoComplete="current-password"
            disabled={isSubmitting}
            onChange={(event) => {
              setPassword(event.target.value)
            }}
          />

          {errorMessage && (
            <div className="login-error">
              {errorMessage}
            </div>
          )}

          <button
            className="login-button"
            type="submit"
            disabled={!canSubmit}
          >
            {isSubmitting
              ? '正在登录……'
              : '登录系统'}
          </button>
        </form>

        <p className="login-hint">
          演示账号包括保安、安管经理等角色，
          密码使用后端配置的演示密码。
        </p>
      </section>
    </main>
  )
}


export default LoginPanel