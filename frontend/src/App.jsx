import {
  useEffect,
  useRef,
  useState,
} from 'react'
import CommandContextRail from './components/CommandContextRail'
import CommandHeader from './components/CommandHeader'
import CommandNavigation from './components/CommandNavigation'

import {
  getCurrentUser,
  hasStoredAccessToken,
  loginUser,
  logoutUser,
} from './api/auth'
import http from './api/http'
import {
  streamMultiAgentQuery,
} from './api/multiAgentStream'
import LoginPanel from './components/LoginPanel'
import InspectionVisionPanel from './components/InspectionVisionPanel'
import './App.css'
import './CommandCenter.css'




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
  const messageListRef = useRef(null)

  const [authState, setAuthState] =
    useState(() => ({
      status: hasStoredAccessToken()
        ? 'checking'
        : 'anonymous',
      user: null,
      error: '',
    }))

  const [
    activeView,
    setActiveView,
  ] = useState('command')

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

  useEffect(() => {
    const messageList = messageListRef.current

    if (!messageList) {
      return
    }

    messageList.scrollTop = (
      messageList.scrollHeight
    )
  }, [messages])

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

    setActiveView('command')

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

    const streamingMessageId = (
      createMessageId()
    )

    setMessages((currentMessages) => [
      ...currentMessages,
      {
        id: createMessageId(),
        role: 'user',
        text: normalizedQuestion,
      },
      {
        id: streamingMessageId,
        role: 'assistant',
        text: '',
        isStreaming: true,
        streamStatus: '正在连接多Agent服务',
        usedDocCodes: [],
        citations: [],
        routeHistory: [],
      },
    ])

    setQuestion('')

    try {
      await streamMultiAgentQuery(
        normalizedQuestion,
        {
          onStart: (data) => {
            setMessages((currentMessages) => (
              currentMessages.map((message) => (
                message.id === streamingMessageId
                  ? {
                      ...message,
                      requestId: data.request_id,
                      streamStatus: data.message,
                    }
                  : message
              ))
            ))
          },
          onStatus: (data) => {
            setMessages((currentMessages) => (
              currentMessages.map((message) => (
                message.id === streamingMessageId
                  ? {
                      ...message,
                      streamStatus: data.message,
                    }
                  : message
              ))
            ))
          },
          onMetadata: (data) => {
            setMessages((currentMessages) => (
              currentMessages.map((message) => (
                message.id === streamingMessageId
                  ? {
                      ...message,
                      requestId: data.request_id,
                      runStatus: data.run_status,
                      category: data.category,
                      riskLevel: data.risk_level,
                      answerStatus: data.answer_status,
                      validationPassed: (
                        data.answer_validation_passed
                      ),
                      usedDocCodes: (
                        data.used_doc_codes || []
                      ),
                      citations: data.citations || [],
                      pendingAction: (
                        data.pending_action
                      ),
                      confirmationStatus: (
                        data.confirmation_status
                      ),
                      confirmedBy: (
                        data.confirmed_by || ''
                      ),
                      routeHistory: (
                        data.route_history || []
                      ),
                    }
                  : message
              ))
            ))
          },
          onAnswerDelta: (text) => {
            setMessages((currentMessages) => (
              currentMessages.map((message) => (
                message.id === streamingMessageId
                  ? {
                      ...message,
                      text: message.text + text,
                      streamStatus: '',
                    }
                  : message
              ))
            ))
          },
          onComplete: (result) => {
            setMessages((currentMessages) => (
              currentMessages.map((message) => (
                message.id === streamingMessageId
                  ? resultToMessage(
                      result,
                      streamingMessageId,
                    )
                  : message
              ))
            ))
          },
        },
      )
    } catch (error) {
      setMessages((currentMessages) => (
        currentMessages.filter(
          (message) => (
            message.id !== streamingMessageId
          ),
        )
      ))

      if (error.status === 401) {
        logoutUser()

        setAuthState({
          status: 'anonymous',
          user: null,
          error: (
            '登录状态已经失效，'
            + '请重新登录。'
          ),
        })
      } else {
        setErrorMessage(
          getErrorMessage(error),
        )

        setQuestion(normalizedQuestion)
      }
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
      event.key !== 'Enter'
      || event.shiftKey
      || event.nativeEvent.isComposing
    ) {
      return
    }

    event.preventDefault()
    event.currentTarget
      .form
      ?.requestSubmit()
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

  const handledAssistantMessages =
    messages.filter((message) => (
      message.role === 'assistant'
      && message.requestId
    ))

  const latestAssistantMessage =
    handledAssistantMessages.at(-1)
    || null

  const pendingApprovalMessage = (
    [...handledAssistantMessages]
      .reverse()
      .find((message) => (
        message.pendingAction
        && !message.isStreaming
        && message.runStatus
          === 'awaiting_confirmation'
      ))
    || null
  )


  const canSubmit =
    agentStatus.state === 'ready'
    && question.trim().length >= 2
    && !isSubmitting

  return (
    <div className="command-app">
      <CommandNavigation
        activeView={activeView}
        onViewChange={setActiveView}
      />

      <div className="command-main">
        <CommandHeader
          agentStatus={agentStatus}
          onCheckStatus={checkAgentStatus}
          onLogout={handleLogout}
          user={authState.user}
        />

        {activeView === 'inspection' ? (
          <main className="inspection-page">
            <InspectionVisionPanel
              onUnauthorized={handleLogout}
            />
          </main>
        ) : (
          <main className="command-workspace">
            <section className="conversation-panel">
              <header className="conversation-heading">
                <div>
                  <h1>安管指挥台</h1>

                  <p>
                    向多智能体系统提问，
                    获取应急处置建议并确认
                    关键动作。
                  </p>
                </div>

                <span className="conversation-model">
                  {
                    agentStatus.data?.model
                    || '正在读取模型'
                  }
                </span>
              </header>

              <div
                ref={messageListRef}
                aria-live="polite"
                className={
                  'message-list '
                  + 'command-message-scroll'
                }
              >
            {messages.map((message) => {
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

                      {message.isStreaming
                        && message.text && (
                        <span
                          className="streaming-cursor"
                          aria-hidden="true"
                        />
                      )}

                      {message.isStreaming
                        && !message.text && (
                        <span className="streaming-status">
                          <span
                            className="thinking-dot"
                            aria-hidden="true"
                          />
                          {
                            message.streamStatus
                            || '正在生成回答'
                          }
                        </span>
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
                · Enter 发送
                · Shift + Enter 换行
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

            <CommandContextRail
              confirmationNote={
                confirmationNote
              }
              isConfirming={
                confirmingMessageId
                === pendingApprovalMessage?.id
              }
              latestMessage={
                latestAssistantMessage
              }
              pendingApprovalMessage={
                pendingApprovalMessage
              }
              onConfirmationNoteChange={
                setConfirmationNote
              }
              onConfirm={
                handleConfirmation
              }
            />
          </main>
        )}
      </div>
    </div>
  )
}


export default App
