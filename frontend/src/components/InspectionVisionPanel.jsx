import { useState } from 'react'

import {
  analyzeInspectionImage,
} from '../api/inspectionVision'


const MAX_IMAGE_BYTES = 10 * 1024 * 1024

const ALLOWED_IMAGE_TYPES = new Set([
  'image/jpeg',
  'image/png',
  'image/webp',
])

const RISK_TYPE_LABELS = {
  fire_safety: '消防安全',
  passage_obstruction: '通道堵塞',
  electrical: '电气安全',
  water_leak: '漏水风险',
  equipment: '设备风险',
  fall_hazard: '跌倒风险',
  vehicle: '车辆风险',
  personnel: '人员风险',
  other: '其他风险',
}


const SEVERITY_LABELS = {
  low: '低风险',
  medium: '中风险',
  high: '高风险',
  critical: '严重风险',
}

function getUploadErrorMessage(error) {
  const detail = error.response?.data?.detail

  if (typeof detail === 'string') {
    return detail
  }

  if (
    detail
    && typeof detail.message === 'string'
  ) {
    return detail.message
  }

  if (error.code === 'ECONNABORTED') {
    return (
      '图片分析超时，请检查后端控制台'
      + '和多模态模型连接。'
    )
  }

  return (
    error.message
    || '巡检照片分析失败'
  )
}


function InspectionVisionPanel({
  onUnauthorized,
}) {
  const [
    selectedImage,
    setSelectedImage,
  ] = useState(null)

  const [
    isAnalyzing,
    setIsAnalyzing,
  ] = useState(false)

  const [
    analysis,
    setAnalysis,
  ] = useState(null)

  const [
    errorMessage,
    setErrorMessage,
  ] = useState('')

  function handleImageChange(event) {
    const imageFile =
      event.target.files?.[0] || null

    setAnalysis(null)
    setErrorMessage('')

    if (!imageFile) {
      setSelectedImage(null)
      return
    }

    if (
      !ALLOWED_IMAGE_TYPES.has(
        imageFile.type,
      )
    ) {
      setSelectedImage(null)
      event.target.value = ''

      setErrorMessage(
        '只支持JPG、PNG和WebP图片。',
      )
      return
    }

    if (imageFile.size > MAX_IMAGE_BYTES) {
      setSelectedImage(null)
      event.target.value = ''

      setErrorMessage(
        '图片不能超过10MB。',
      )
      return
    }

    setSelectedImage(imageFile)
  }

  async function handleSubmit(event) {
    event.preventDefault()

    if (
      !selectedImage
      || isAnalyzing
    ) {
      return
    }

    setErrorMessage('')
    setAnalysis(null)
    setIsAnalyzing(true)

    try {
      const result =
        await analyzeInspectionImage(
          selectedImage,
        )

      setAnalysis(result)
    } catch (error) {
      if (error.response?.status === 401) {
        if (
          typeof onUnauthorized
          === 'function'
        ) {
          onUnauthorized()
        }

        return
      }

      setErrorMessage(
        getUploadErrorMessage(error),
      )
    } finally {
      setIsAnalyzing(false)
    }
  }

  const visionResult = analysis?.result

  const agentResult =
    analysis?.agent_result

  return (
    <section className="vision-panel">
      <div className="vision-heading">
        <div>
          <p className="eyebrow">
            MULTIMODAL INSPECTION
          </p>

          <h2>巡检照片分析</h2>
        </div>

        <span className="vision-limit">
          JPG、PNG、WebP · 最大10MB
        </span>
      </div>

      <p className="vision-description">
        上传一张巡检照片，系统将识别照片中
        可见的风险，并交给巡检Agent生成
        带知识库引用的整改建议。
      </p>

      <form
        className="vision-form"
        onSubmit={handleSubmit}
      >
        <label
          className="vision-file-label"
          htmlFor="inspection-image"
        >
          选择巡检照片
        </label>

        <input
          id="inspection-image"
          type="file"
          accept={
            '.jpg,.jpeg,.png,.webp,'
            + 'image/jpeg,image/png,image/webp'
          }
          disabled={isAnalyzing}
          onChange={handleImageChange}
        />

        {selectedImage && (
          <div className="vision-selected-file">
            <strong>已选择：</strong>
            {selectedImage.name}
          </div>
        )}

        {errorMessage && (
          <div className="error-banner">
            <strong>分析失败：</strong>
            {errorMessage}
          </div>
        )}

        <button
          className="primary-button"
          type="submit"
          disabled={
            !selectedImage
            || isAnalyzing
          }
        >
          {isAnalyzing
            ? '正在分析照片……'
            : '开始分析'}
        </button>
      </form>

            {analysis
        && visionResult
        && agentResult
        && (
        <section className="vision-results">
          <div className="vision-summary">
            <h3>图片识别摘要</h3>

            <dl className="vision-meta">
              <div>
                <dt>文件</dt>
                <dd>{analysis.filename}</dd>
              </div>

              <div>
                <dt>分析人员</dt>
                <dd>
                  {analysis.analyzed_by}
                  （{analysis.analyzed_by_role}）
                </dd>
              </div>

              <div>
                <dt>是否发现风险</dt>
                <dd>
                  {visionResult.has_risk
                    ? '是'
                    : '否'}
                </dd>
              </div>

              <div>
                <dt>是否需要人工复核</dt>
                <dd>
                  {
                    visionResult
                      .requires_manual_review
                      ? '是'
                      : '否'
                  }
                </dd>
              </div>
            </dl>

            <p>{visionResult.summary}</p>
          </div>

          {visionResult.risks.length > 0 && (
            <section className="vision-risk-section">
              <h3>
                发现的风险
                （{visionResult.risks.length}项）
              </h3>

              <div className="vision-risk-list">
                {visionResult.risks.map(
                  (risk, index) => (
                    <article
                      className="vision-risk-card"
                      key={
                        `${risk.risk_type}-${index}`
                      }
                    >
                      <div className="vision-risk-heading">
                        <strong>
                          {
                            RISK_TYPE_LABELS[
                              risk.risk_type
                            ]
                            || risk.risk_type
                          }
                        </strong>

                        <span
                          className={
                            `vision-severity `
                            + `severity-${risk.severity}`
                          }
                        >
                          {
                            SEVERITY_LABELS[
                              risk.severity
                            ]
                            || risk.severity
                          }
                        </span>
                      </div>

                      <dl className="vision-risk-details">
                        <div>
                          <dt>位置</dt>
                          <dd>{risk.location}</dd>
                        </div>

                        <div>
                          <dt>风险描述</dt>
                          <dd>{risk.description}</dd>
                        </div>

                        <div>
                          <dt>可见证据</dt>
                          <dd>
                            {risk.visual_evidence}
                          </dd>
                        </div>

                        <div>
                          <dt>识别可信度</dt>
                          <dd>
                            {
                              Math.round(
                                risk.confidence * 100,
                              )
                            }%
                          </dd>
                        </div>
                      </dl>
                    </article>
                  ),
                )}
              </div>
            </section>
          )}

          {visionResult.risks.length === 0 && (
            <div className="vision-no-risk">
              照片中没有识别到明确的可见风险，
              但结果不能代替工作人员现场巡检。
            </div>
          )}

          {visionResult.uncertainties.length > 0 && (
            <section className="vision-uncertainties">
              <h3>需要注意的不确定项</h3>

              <ul>
                {visionResult.uncertainties.map(
                  (uncertainty, index) => (
                    <li
                      key={
                        `${uncertainty}-${index}`
                      }
                    >
                      {uncertainty}
                    </li>
                  ),
                )}
              </ul>
            </section>
          )}

          <section className="vision-agent-result">
            <div className="vision-agent-heading">
              <div>
                <p className="eyebrow">
                  INSPECTION AGENT
                </p>

                <h3>巡检Agent整改建议</h3>
              </div>

              <span>
                风险等级：
                {agentResult.risk_level}
              </span>
            </div>

            <div className="vision-agent-answer">
              {agentResult.answer}
            </div>

            {agentResult.used_doc_codes.length > 0 && (
              <div className="vision-doc-codes">
                <strong>使用的知识库资料：</strong>

                <div>
                  {agentResult.used_doc_codes.map(
                    (docCode) => (
                      <code key={docCode}>
                        [{docCode}]
                      </code>
                    ),
                  )}
                </div>
              </div>
            )}

            {agentResult.citations.length > 0 && (
              <div className="vision-citations">
                <h4>资料引用</h4>

                {agentResult.citations.map(
                  (citation, index) => (
                    <article
                      className="vision-citation-card"
                      key={
                        `${
                          citation.reference_id
                          || 'citation'
                        }-${index}`
                      }
                    >
                      <strong>
                        {citation.reference_id}
                        {' '}
                        {citation.document_title}
                      </strong>

                      {citation.source_title && (
                        <p>
                          来源：
                          {citation.source_title}
                        </p>
                      )}

                      {citation.citation_locator && (
                        <p>
                          引用位置：
                          {citation.citation_locator}
                        </p>
                      )}

                      {citation.published_date && (
                        <p>
                          发布日期：
                          {citation.published_date}
                        </p>
                      )}

                      {citation.official_url && (
                        <a
                          href={citation.official_url}
                          target="_blank"
                          rel="noreferrer"
                        >
                          查看官方来源
                        </a>
                      )}
                    </article>
                  ),
                )}
              </div>
            )}

            <details className="vision-route">
              <summary>查看多Agent处理流程</summary>

              <ol>
                {agentResult.route_history.map(
                  (routeStep, index) => (
                    <li
                      key={
                        `${routeStep}-${index}`
                      }
                    >
                      {routeStep}
                    </li>
                  ),
                )}
              </ol>
            </details>
          </section>
        </section>
      )}
    </section>
  )
}


export default InspectionVisionPanel