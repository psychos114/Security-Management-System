import { useEffect, useState } from 'react'

import {
  getCurrentUser,
  hasStoredAccessToken,
  loginUser,
  logoutUser,
} from './api/auth'
import http from './api/http'
import LoginPanel from './components/LoginPanel'
import './App.css'


const EXAMPLE_QUESTIONS = [
  '住院部三楼已经起火并出现大量浓烟，系统应该如何处置？',
  '地下停车场消防车道的照片应该重点检查哪些漏检项目？',
  '医护人员投诉门岗没有登记访客，SLA和回访应该如何安排？',
  '深圳医院消防控制室值班人员适用哪些消防法规？',
]


const CATEGORY_LABELS = {
  emergency: '突发事件',
  inspection: '巡检管理',
  complaint_report: '投诉与日报',
  fire_compliance: '消防法规',
  general: '一般问题',
  unclassified: '尚未分类',
}


const RISK_LABELS = {
  unknown: '未知',
  low: '低风险',
  medium: '中风险',
  high: '高风险',
  critical: '重大风险',
}


const RUN_STATUS_LABELS = {
  completed: '处理完成',
  awaiting_confirmation: '等待人工确认',
  approved: '人工已批准',
  rejected: '人工已拒绝',
}


const ACTION_LABELS = {
  create_work_order: '创建处置工单',
  notify_personnel: '通知相关人员',
  escalate_event: '升级并上报事件',
}


function createMessageId() {
  return (
    `${Date.now()}-`
    + Math.random().toString(16).slice(2)
  )
}


function getErrorMessage(error) {
  const detail = error.response?.data?.detail

  if (typeof detail === 'string') {
    return detail
  }

  if (Array.isArray(detail)) {
    return detail
      .map((item) => item.msg)
      .join('；')
  }

  if (detail?.message) {
    return detail.message
  }

  if (error.code === 'ECONNABORTED') {
    return (
      '请求超时，请查看后端控制台，'
      + '确认模型接口是否正常。'
    )
  }

  return error.message || '多Agent请求失败'
}


function renderAnswerText(text) {
  const safeText = text || ''

  const urlPattern =
    /(https?:\/\/[^\s，。；）\]]+)/g

  return safeText
    .split(urlPattern)
    .map((part, index) => {
      const isUrl =
        part.startsWith('http://')
        || part.startsWith('https://')

      if (isUrl) {
        return (
          <a
            key={`${part}-${index}`}
            href={part}
            target="_blank"
            rel="noreferrer"
          >
            {part}
          </a>
        )
      }

      return part
    })
}


function resultToMessage(
  result,
  messageId = createMessageId(),
) {
  return {
    id: messageId,
    role: 'assistant',
    text: result.answer || '',
    requestId: result.request_id,
    runStatus: result.run_status,
    category: result.category,
    riskLevel: result.risk_level,
    answerStatus: result.answer_status,
    validationPassed:
      result.answer_validation_passed,
    usedDocCodes:
      result.used_doc_codes || [],
    citations: result.citations || [],
    pendingAction: result.pending_action,
    confirmationStatus:
      result.confirmation_status,
    confirmedBy: result.confirmed_by || '',
    routeHistory: result.route_history || [],
  }
}


function App() {
  const [authState, setAuthState] =
    useState(() => ({
      status: hasStoredAccessToken()
        ? 'checking'
        : 'anonymous',
      user: null,
      error: '',
    }))

  const [agentStatus, setAgentStatus] =
    useState({
      state: 'loading',
      message: '正在检查后端服务……',
      data: null,
    })

  const [question, setQuestion] =
    useState('')



  const [
    confirmationNote,
    setConfirmationNote,
  ] = useState('已经核实现场情况')

  const [isSubmitting, setIsSubmitting] =
    useState(false)

  const [
    confirmingMessageId,
    setConfirmingMessageId,
  ] = useState('')

  const [errorMessage, setErrorMessage] =
    useState('')

  const [messages, setMessages] = useState([
    {
      id: 'welcome',
      role: 'assistant',
      text: (
        '您好，我是医院物业安管多Agent助手。'
        + '系统会根据问题类型调度专业Agent，'
        + '通过受控混合检索读取资料，'
        + '再生成带真实引用的回答。'
        + '派单、通知和事件升级等关键动作'
        + '必须经过人工确认。'
      ),
      usedDocCodes: [],
      citations: [],
      routeHistory: [],
    },
  ])

  async function checkAgentStatus() {
    setAgentStatus({
      state: 'loading',
      message: '正在检查后端服务……',
      data: null,
    })

    try {
      const response = await http.get(
        '/api/agent/status',
      )

      setAgentStatus({
        state: 'ready',
        message: '多Agent后端服务正常',
        data: response.data,
      })
    } catch (error) {
      setAgentStatus({
        state: 'error',
        message: getErrorMessage(error),
        data: null,
      })
    }
  }

  useEffect(() => {
    let cancelled = false

    http
      .get('/api/agent/status')
      .then((response) => {
        if (cancelled) {
          return
        }

        setAgentStatus({
          state: 'ready',
          message: '多Agent后端服务正常',
          data: response.data,
        })
      })
      .catch((error) => {
        if (cancelled) {
          return
        }

        setAgentStatus({
          state: 'error',
          message: getErrorMessage(error),
          data: null,
        })
      })

    return () => {
      cancelled = true
    }
  }, [])

    useEffect(() => {
    if (!hasStoredAccessToken()) {
      return undefined
    }

    let cancelled = false

    getCurrentUser()
      .then((user) => {
        if (cancelled) {
          return
        }

        setAuthState({
          status: 'authenticated',
          user,
          error: '',
        })
      })
      .catch(() => {
        logoutUser()

        if (cancelled) {
          return
        }

        setAuthState({
          status: 'anonymous',
          user: null,
          error: (
            '登录状态已经失效，'
            + '请重新登录。'
          ),
        })
      })

    return () => {
      cancelled = true
    }
  }, [])

    async function handleLogin(
    username,
    password,
  ) {
    setAuthState({
      status: 'submitting',
      user: null,
      error: '',
    })

    try {
      const result = await loginUser(
        username,
        password,
      )

      setAuthState({
        status: 'authenticated',
        user: result.user,
        error: '',
      })

      setErrorMessage('')
    } catch (error) {
      logoutUser()

      setAuthState({
        status: 'anonymous',
        user: null,
        error: getErrorMessage(error),
      })
    }
  }


  function handleLogout() {
    logoutUser()

    setAuthState({
      status: 'anonymous',
      user: null,
      error: '',
    })

    setQuestion('')
    setErrorMessage('')
    setConfirmingMessageId('')

    setMessages((currentMessages) => (
      currentMessages.filter(
        (message) => (
          message.id === 'welcome'
        ),
      )
    ))
  }

  async function handleSubmit(event) {
    event.preventDefault()

    const normalizedQuestion =
      question.trim()

    if (
      normalizedQuestion.length < 2
      || isSubmitting
    ) {
      return
    }

    setErrorMessage('')
    setIsSubmitting(true)

    setMessages((currentMessages) => [
      ...currentMessages,
      {
        id: createMessageId(),
        role: 'user',
        text: normalizedQuestion,
      },
    ])

    setQuestion('')

    try {
      const response = await http.post(
        '/api/multi-agent/query',
        {
          question: normalizedQuestion,
        },
      )

      setMessages((currentMessages) => [
        ...currentMessages,
        resultToMessage(response.data),
      ])
    } catch (error) {
      setErrorMessage(
        getErrorMessage(error),
      )

      setQuestion(normalizedQuestion)
    } finally {
      setIsSubmitting(false)
    }
  }

  async function handleConfirmation(
    messageId,
    requestId,
    approved,
  ) {
    setErrorMessage('')
    setConfirmingMessageId(messageId)

    try {
      const response = await http.post(
        '/api/multi-agent/confirm',
        {
          request_id: requestId,
          approved,
          note: confirmationNote.trim(),
        },
      )

      setMessages((currentMessages) => (
        currentMessages.map((message) => {
          if (message.id !== messageId) {
            return message
          }

          return resultToMessage(
            response.data,
            messageId,
          )
        })
      ))
    } catch (error) {
      if (error.response?.status === 401) {
        logoutUser()

        setAuthState({
          status: 'anonymous',
          user: null,
          error: (
            '登录状态已经失效，'
            + '请重新登录。'
          ),
        })

        setErrorMessage('')

        setMessages((currentMessages) => (
          currentMessages.filter(
            (message) => (
              message.id === 'welcome'
            ),
          )
        ))
      } else {
        setErrorMessage(
          getErrorMessage(error),
        )
      }
    } finally {
      setConfirmingMessageId('')
    }
  }

  function handleTextareaKeyDown(event) {
    if (
      event.key === 'Enter'
      && (
        event.ctrlKey
        || event.metaKey
      )
    ) {
      event.preventDefault()
      event.currentTarget
        .form
        ?.requestSubmit()
    }
  }

    if (authState.status === 'checking') {
    return (
      <main className="auth-page">
        <section className="login-card">
          <p className="eyebrow">
            SECURITY MANAGEMENT
          </p>

          <h1>医院物业安管系统</h1>

          <p className="login-description">
            正在检查登录状态……
          </p>
        </section>
      </main>
    )
  }

  if (!authState.user) {
    return (
      <LoginPanel
        errorMessage={authState.error}
        isSubmitting={
          authState.status === 'submitting'
        }
        onLogin={handleLogin}
      />
    )
  }

  const canSubmit =
    agentStatus.state === 'ready'
    && question.trim().length >= 2
    && !isSubmitting

  return (
    <div className="app-shell">
      <header className="topbar">
        <div>
          <p className="eyebrow">
            SECURITY MANAGEMENT
          </p>

          <h1>医院物业安管多Agent系统</h1>
        </div>

        <div className="topbar-actions">
          <div
            className={
              `service-status `
              + `service-${agentStatus.state}`
            }
          >
            <span className="status-dot" />
            {agentStatus.message}
          </div>

          <div className="current-user">
            <span>
              {authState.user.role_name}
            </span>

            <strong>
              {authState.user.display_name}
            </strong>
          </div>

          <button
            className="logout-button"
            type="button"
            onClick={handleLogout}
          >
            退出登录
          </button>
        </div>
      </header>

      <main className="workspace">
        <aside className="sidebar">
          <section className="sidebar-card">
            <h2>系统状态</h2>

            {agentStatus.data ? (
              <dl className="status-details">
                <div>
                  <dt>当前模型</dt>
                  <dd>
                    {agentStatus.data.model}
                  </dd>
                </div>

                <div>
                  <dt>知识向量</dt>
                  <dd>
                    {agentStatus.data.vector_count}
                    条
                  </dd>
                </div>

                <div>
                  <dt>原有只读工具</dt>
                  <dd>
                    {
                      agentStatus
                        .data
                        .tools
                        ?.length || 0
                    }
                    个
                  </dd>
                </div>
              </dl>
            ) : (
              <p className="muted-text">
                暂时无法读取后端服务状态。
              </p>
            )}

            <button
              className="secondary-button"
              type="button"
              onClick={checkAgentStatus}
              disabled={
                agentStatus.state
                === 'loading'
              }
            >
              重新检查
            </button>
          </section>

          <section className="sidebar-card">
            <h2>人工确认身份</h2>

            <dl className="status-details">
              <div>
                <dt>确认人</dt>
                <dd>
                  {
                    authState
                      .user
                      .display_name
                  }
                </dd>
              </div>

              <div>
                <dt>岗位</dt>
                <dd>
                  {
                    authState
                      .user
                      .role_name
                  }
                </dd>
              </div>
            </dl>

            <div className="confirmation-form">
              <label htmlFor="confirmation-note">
                确认说明
              </label>

              <textarea
                id="confirmation-note"
                value={confirmationNote}
                maxLength={500}
                onChange={(event) => {
                  setConfirmationNote(
                    event.target.value,
                  )
                }}
              />
            </div>
          </section>

          <section className="sidebar-card">
            <h2>示例问题</h2>

            <div className="example-list">
              {EXAMPLE_QUESTIONS.map(
                (example) => (
                  <button
                    key={example}
                    type="button"
                    onClick={() => {
                      setQuestion(example)
                      setErrorMessage('')
                    }}
                    disabled={isSubmitting}
                  >
                    {example}
                  </button>
                ),
              )}
            </div>
          </section>

          <section className="safety-note">
            <strong>安全提示</strong>

            <p>
              AI只提供处置建议。报警、急救、
              派单、通知和事件升级等关键动作
              必须由工作人员人工确认。
            </p>
          </section>
        </aside>

        <section className="chat-panel">
          <div className="message-list">
            {messages.map((message) => {
              const isConfirming =
                confirmingMessageId
                === message.id

              return (
                <article
                  key={message.id}
                  className={
                    `message `
                    + `message-${message.role}`
                  }
                >
                  <div className="message-role">
                    {message.role === 'user'
                      ? '您'
                      : '安管多Agent'}
                  </div>

                  <div className="message-card">
                    {message.runStatus && (
                      <div className="result-meta">
                        <span
                          className={
                            `result-badge `
                            + `run-${message.runStatus}`
                          }
                        >
                          {
                            RUN_STATUS_LABELS[
                              message.runStatus
                            ]
                            || message.runStatus
                          }
                        </span>

                        <span>
                          {
                            CATEGORY_LABELS[
                              message.category
                            ]
                            || message.category
                          }
                        </span>

                        <span
                          className={
                            `risk-label `
                            + `risk-${message.riskLevel}`
                          }
                        >
                          {
                            RISK_LABELS[
                              message.riskLevel
                            ]
                            || message.riskLevel
                          }
                        </span>
                      </div>
                    )}

                    <div className="answer-text">
                      {renderAnswerText(
                        message.text,
                      )}
                    </div>

                    {message.usedDocCodes
                      ?.length > 0 && (
                      <div className="references">
                        <span>
                          回答使用的真实资料
                        </span>

                        <div>
                          {
                            message
                              .usedDocCodes
                              .map((docCode) => (
                                <code key={docCode}>
                                  [{docCode}]
                                </code>
                              ))
                          }
                        </div>
                      </div>
                    )}

                    {message.pendingAction && (
                      <section className="action-card">
                        <h3>
                          {
                            message.runStatus
                            === 'awaiting_confirmation'
                              ? '待人工确认的关键动作'
                              : '关键动作审批记录'
                          }
                        </h3>

                        <p>
                          {
                            message
                              .pendingAction
                              .summary
                          }
                        </p>

                        <ul>
                          {(
                            message
                              .pendingAction
                              .action_types
                            || []
                          ).map((actionType) => (
                            <li key={actionType}>
                              {
                                ACTION_LABELS[
                                  actionType
                                ]
                                || actionType
                              }
                            </li>
                          ))}
                        </ul>

                        <dl className="action-details">
                          <div>
                            <dt>审批状态</dt>
                            <dd>
                              {
                                message
                                  .confirmationStatus
                              }
                            </dd>
                          </div>

                          <div>
                            <dt>真实动作已执行</dt>
                            <dd>
                              {
                                message
                                  .pendingAction
                                  .executed
                                  ? '是'
                                  : '否'
                              }
                            </dd>
                          </div>

                          {message.confirmedBy && (
                            <div>
                              <dt>确认人</dt>
                              <dd>
                                {
                                  message
                                    .confirmedBy
                                }
                              </dd>
                            </div>
                          )}
                        </dl>

                        {message.runStatus
                          === 'awaiting_confirmation'
                          && (
                          <div className="action-buttons">
                            <button
                              className="approve-button"
                              type="button"
                              disabled={isConfirming}
                              onClick={() => {
                                handleConfirmation(
                                  message.id,
                                  message.requestId,
                                  true,
                                )
                              }}
                            >
                              {isConfirming
                                ? '正在提交……'
                                : '批准建议'}
                            </button>

                            <button
                              className="reject-button"
                              type="button"
                              disabled={isConfirming}
                              onClick={() => {
                                handleConfirmation(
                                  message.id,
                                  message.requestId,
                                  false,
                                )
                              }}
                            >
                              拒绝建议
                            </button>
                          </div>
                        )}
                      </section>
                    )}

                    {message.routeHistory
                      ?.length > 0 && (
                      <details className="route-trace">
                        <summary>
                          查看多Agent流程
                        </summary>

                        <ol>
                          {
                            message
                              .routeHistory
                              .map((node, index) => (
                                <li
                                  key={
                                    `${node}-${index}`
                                  }
                                >
                                  {node}
                                </li>
                              ))
                          }
                        </ol>
                      </details>
                    )}
                  </div>
                </article>
              )
            })}

            {isSubmitting && (
              <article
                className={
                  'message message-assistant'
                }
              >
                <div className="message-role">
                  安管多Agent
                </div>

                <div
                  className={
                    'message-card thinking-card'
                  }
                >
                  <span className="thinking-dot" />
                  正在分类、检索和读取完整资料，
                  请稍候……
                </div>
              </article>
            )}
          </div>

          <form
            className="composer"
            onSubmit={handleSubmit}
          >
            {errorMessage && (
              <div className="error-banner">
                <strong>操作失败：</strong>
                {errorMessage}
              </div>
            )}

            <label htmlFor="question">
              请输入安管业务问题
            </label>

            <textarea
              id="question"
              value={question}
              maxLength={2000}
              placeholder={
                agentStatus.state === 'ready'
                  ? '例如：医院发生电梯困人，现场应该如何处置？'
                  : '请先等待后端服务连接成功'
              }
              disabled={
                agentStatus.state !== 'ready'
                || isSubmitting
              }
              onChange={(event) => {
                setQuestion(
                  event.target.value,
                )
              }}
              onKeyDown={
                handleTextareaKeyDown
              }
            />

            <div className="composer-footer">
              <span>
                {question.length}/2000
                · Ctrl + Enter发送
              </span>

              <button
                className="primary-button"
                type="submit"
                disabled={!canSubmit}
              >
                {isSubmitting
                  ? '正在分析……'
                  : '发送问题'}
              </button>
            </div>
          </form>
        </section>
      </main>
    </div>
  )
}


export default App