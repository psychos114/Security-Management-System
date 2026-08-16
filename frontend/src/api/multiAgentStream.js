import {
  getAccessToken,
} from './http'


const API_BASE_URL = (
  import.meta.env.VITE_API_BASE_URL || ''
).replace(/\/$/, '')


async function createResponseError(response) {
  let responseData

  try {
    responseData = await response.json()
  } catch {
    responseData = null
  }

  const detail = responseData?.detail

  let message = `请求失败（${response.status}）`

  if (typeof detail === 'string') {
    message = detail
  } else if (detail?.message) {
    message = detail.message
  }

  const error = new Error(message)
  error.status = response.status

  return error
}


function dispatchStreamEvent(
  event,
  callbacks,
) {
  const data = event.data || {}

  if (event.type === 'start') {
    callbacks.onStart?.(data)
    return
  }

  if (event.type === 'status') {
    callbacks.onStatus?.(data)
    return
  }

  if (event.type === 'metadata') {
    callbacks.onMetadata?.(data)
    return
  }

  if (event.type === 'answer_delta') {
    callbacks.onAnswerDelta?.(
      data.text || '',
    )
    return
  }

  if (event.type === 'complete') {
    callbacks.onComplete?.(
      data.result || {},
    )
    return
  }

  if (event.type === 'error') {
    throw new Error(
      data.message
      || '多Agent流式回答失败',
    )
  }
}


function processStreamLines(
  lines,
  callbacks,
) {
  for (const line of lines) {
    const normalizedLine = line.trim()

    if (!normalizedLine) {
      continue
    }

    const event = JSON.parse(
      normalizedLine,
    )

    dispatchStreamEvent(
      event,
      callbacks,
    )
  }
}


export async function streamMultiAgentQuery(
  question,
  callbacks = {},
) {
  const accessToken = getAccessToken()

  const response = await fetch(
    `${API_BASE_URL}/api/multi-agent/query/stream`,
    {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(accessToken
          ? {
              Authorization:
                `Bearer ${accessToken}`,
            }
          : {}),
      },
      body: JSON.stringify({
        question,
      }),
    },
  )

  if (!response.ok) {
    throw await createResponseError(
      response,
    )
  }

  if (!response.body) {
    throw new Error(
      '当前浏览器无法读取流式响应',
    )
  }

  const reader = response.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''

  while (true) {
    const {
      value,
      done,
    } = await reader.read()

    buffer += decoder.decode(
      value,
      {
        stream: !done,
      },
    )

    const lines = buffer.split('\n')
    buffer = lines.pop() || ''

    processStreamLines(
      lines,
      callbacks,
    )

    if (done) {
      break
    }
  }

  if (buffer.trim()) {
    processStreamLines(
      [buffer],
      callbacks,
    )
  }
}
