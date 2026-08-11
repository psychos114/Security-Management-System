import { useEffect, useState } from 'react'

import http from './api/http'
import './App.css'


const EXAMPLE_QUESTIONS = [
  '医院发生电梯困人，保安现在应该怎么做？',
  '投诉超过SLA还没有解决，应该升级给谁？',
  '深圳物业单位在消防安全方面有哪些责任？',
]


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

  if (detail?.message) {
    return detail.message
  }

  if (error.code === 'ECONNABORTED') {
    return '请求超时，请检查后端控制台后重试。'
  }

  return error.message || 'Agent请求失败'
}


function renderAnswerText(text) {
  const urlPattern =
    /(https?:\/\/[^\s，。；）)\]]+)/g

  return text.split(urlPattern).map(
    (part, index) => {
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
    },
  )
}


function App() {
  const [agentStatus, setAgentStatus] =
    useState({
      state: 'loading',
      message: '正在检查Agent服务……',
      data: null,
    })

  const [question, setQuestion] =
    useState('')

  const [isSubmitting, setIsSubmitting] =
    useState(false)

  const [errorMessage, setErrorMessage] =
    useState('')

  const [messages, setMessages] = useState([
    {
      id: 'welcome',
      role: 'assistant',
      text: (
        '您好，我是医院物业安管知识助手。'
        + '我会先检索知识库并读取完整资料，'
        + '再为您提供带引用的工作建议。'
      ),
      openedDocuments: [],
      toolTrace: [],
    },
  ])

  async function checkAgentStatus() {
    setAgentStatus({
      state: 'loading',
      message: '正在检查Agent服务……',
      data: null,
    })

    try {
      const response = await http.get(
        '/api/agent/status',
      )

      setAgentStatus({
        state: 'ready',
        message: 'Agentic RAG服务正常',
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
        message: 'Agentic RAG服务正常',
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

  async function handleSubmit(event) {
    event.preventDefault()

    const normalizedQuestion =
      question.trim()

    if (
      !normalizedQuestion
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
        openedDocuments: [],
        toolTrace: [],
      },
    ])

    setQuestion('')

    try {
      const response = await http.post(
        '/api/agent/query',
        {
          question: normalizedQuestion,
        },
      )

      const result = response.data

      setMessages((currentMessages) => [
        ...currentMessages,
        {
          id: createMessageId(),
          role: 'assistant',
          text: result.answer,
          openedDocuments:
            result.opened_documents || [],
          allowedDocuments:
            result.allowed_documents || [],
          toolTrace:
            result.tool_trace || [],
          rounds: result.rounds,
          toolCalls: result.tool_calls,
        },
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

          <h1>医院物业安管智能助手</h1>
        </div>

        <div
          className={
            `service-status `
            + `service-${agentStatus.state}`
          }
        >
          <span className="status-dot" />
          {agentStatus.message}
        </div>
      </header>

      <main className="workspace">
        <aside className="sidebar">
          <section className="sidebar-card">
            <h2>知识库状态</h2>

            {agentStatus.data ? (
              <dl className="status-details">
                <div>
                  <dt>模型</dt>
                  <dd>
                    {agentStatus.data.model}
                  </dd>
                </div>

                <div>
                  <dt>知识向量</dt>
                  <dd>
                    {
                      agentStatus
                        .data
                        .vector_count
                    } 条
                  </dd>
                </div>

                <div>
                  <dt>只读工具</dt>
                  <dd>
                    {
                      agentStatus
                        .data
                        .tools
                        .length
                    } 个
                  </dd>
                </div>
              </dl>
            ) : (
              <p className="muted-text">
                暂时无法读取知识库状态。
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
              AI仅提供工作建议。报警、急救、
              专业救援和关键业务动作不能因等待
              AI回答而延误，并需按制度人工确认。
            </p>
          </section>
        </aside>

        <section className="chat-panel">
          <div className="message-list">
            {messages.map((message) => (
              <article
                key={message.id}
                className={
                  `message message-${message.role}`
                }
              >
                <div className="message-role">
                  {message.role === 'user'
                    ? '您'
                    : '安管助手'}
                </div>

                <div className="message-card">
                  <div className="answer-text">
                    {renderAnswerText(
                      message.text,
                    )}
                  </div>

                  {message.openedDocuments
                    ?.length > 0 && (
                    <div className="references">
                      <span>已引用资料</span>

                      <div>
                        {
                          message
                            .openedDocuments
                            .map((docCode) => (
                              <code key={docCode}>
                                [{docCode}]
                              </code>
                            ))
                        }
                      </div>
                    </div>
                  )}

                  {message.toolTrace
                    ?.length > 0 && (
                    <details className="tool-trace">
                      <summary>
                        查看检索过程
                        {message.toolCalls
                          ? `（${message.toolCalls}次工具调用）`
                          : ''}
                      </summary>

                      <ol>
                        {message.toolTrace.map(
                          (item, index) => (
                            <li
                              key={
                                `${item.round}-`
                                + `${item.tool_name}-`
                                + index
                              }
                            >
                              <strong>
                                第{item.round}轮：
                                {item.tool_name}
                              </strong>

                              <span>
                                {item.ok
                                  ? '执行成功'
                                  : '执行失败'}
                              </span>

                              {item.doc_codes
                                ?.length > 0 && (
                                <small>
                                  候选资料：
                                  {
                                    item
                                      .doc_codes
                                      .join('、')
                                  }
                                </small>
                              )}

                              {
                                item
                                  .opened_doc_code
                                && (
                                <small>
                                  打开资料：
                                  {
                                    item
                                      .opened_doc_code
                                  }
                                </small>
                              )}
                            </li>
                          ),
                        )}
                      </ol>
                    </details>
                  )}
                </div>
              </article>
            ))}

            {isSubmitting && (
              <article className="message message-assistant">
                <div className="message-role">
                  安管助手
                </div>

                <div className="message-card thinking-card">
                  <span className="thinking-dot" />
                  正在检索知识库并读取资料，请稍候……
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
                <strong>请求失败：</strong>
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
                  ? '例如：医院发生电梯困人，保安应该怎么处理？'
                  : '请先等待Agent服务连接成功'
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