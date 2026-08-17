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


function InspectionAnalysisMessage({ analysis }) {
  const visionResult = analysis?.result
  const agentResult = analysis?.agent_result

  if (!visionResult || !agentResult) {
    return (
      <p className="inspection-message-empty">
        图片分析结果不完整，请重新上传照片。
      </p>
    )
  }

  const risks = visionResult.risks || []
  const uncertainties =
    visionResult.uncertainties || []
  const docCodes =
    agentResult.used_doc_codes || []
  const citations = agentResult.citations || []
  const routeHistory =
    agentResult.route_history || []

  return (
    <div className="inspection-message-result">
      <section className="inspection-summary-card">
        <div className="inspection-message-heading">
          <div>
            <span>照片识别完成</span>
            <h3>{visionResult.summary}</h3>
          </div>

          <span
            className={
              visionResult.has_risk
                ? 'inspection-risk-found'
                : 'inspection-risk-clear'
            }
          >
            {visionResult.has_risk
              ? `发现 ${risks.length} 项风险`
              : '未发现明确风险'}
          </span>
        </div>

        <dl className="inspection-message-meta">
          <div>
            <dt>文件</dt>
            <dd>{analysis.filename}</dd>
          </div>

          <div>
            <dt>分析人员</dt>
            <dd>
              {analysis.analyzed_by}
              {analysis.analyzed_by_role
                ? `（${analysis.analyzed_by_role}）`
                : ''}
            </dd>
          </div>

          <div>
            <dt>人工复核</dt>
            <dd>
              {visionResult.requires_manual_review
                ? '需要'
                : '暂不需要'}
            </dd>
          </div>
        </dl>
      </section>

      {risks.length > 0 && (
        <section className="inspection-message-section">
          <h3>可见风险</h3>

          <div className="vision-risk-list">
            {risks.map((risk, index) => (
              <article
                className="vision-risk-card"
                key={`${risk.risk_type}-${index}`}
              >
                <div className="vision-risk-heading">
                  <strong>
                    {RISK_TYPE_LABELS[
                      risk.risk_type
                    ] || risk.risk_type}
                  </strong>

                  <span
                    className={
                      `vision-severity `
                      + `severity-${risk.severity}`
                    }
                  >
                    {SEVERITY_LABELS[
                      risk.severity
                    ] || risk.severity}
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
                    <dd>{risk.visual_evidence}</dd>
                  </div>

                  <div>
                    <dt>识别可信度</dt>
                    <dd>
                      {Math.round(
                        risk.confidence * 100,
                      )}%
                    </dd>
                  </div>
                </dl>
              </article>
            ))}
          </div>
        </section>
      )}

      {risks.length === 0 && (
        <div className="vision-no-risk">
          照片中没有识别到明确的可见风险，
          但结果不能代替工作人员现场巡检。
        </div>
      )}

      {uncertainties.length > 0 && (
        <section
          className={
            'inspection-message-section '
            + 'inspection-uncertainties'
          }
        >
          <h3>需要现场确认</h3>

          <ul>
            {uncertainties.map(
              (uncertainty, index) => (
                <li
                  key={`${uncertainty}-${index}`}
                >
                  {uncertainty}
                </li>
              ),
            )}
          </ul>
        </section>
      )}

      <section className="inspection-agent-message">
        <div className="vision-agent-heading">
          <div>
            <p className="eyebrow">
              INSPECTION AGENT
            </p>
            <h3>巡检 Agent 整改建议</h3>
          </div>

          <span>
            风险等级：
            {SEVERITY_LABELS[
              agentResult.risk_level
            ] || agentResult.risk_level}
          </span>
        </div>

        <div className="vision-agent-answer">
          {agentResult.answer}
        </div>

        {docCodes.length > 0 && (
          <div className="vision-doc-codes">
            <strong>使用的知识库资料：</strong>
            <div>
              {docCodes.map((docCode) => (
                <code key={docCode}>
                  [{docCode}]
                </code>
              ))}
            </div>
          </div>
        )}

        {citations.length > 0 && (
          <div className="vision-citations">
            <h4>真实资料引用</h4>

            {citations.map((citation, index) => (
              <article
                className="vision-citation-card"
                key={
                  `${citation.reference_id
                    || 'citation'}-${index}`
                }
              >
                <strong>
                  {citation.reference_id}{' '}
                  {citation.document_title}
                </strong>

                {citation.source_title && (
                  <p>
                    来源：{citation.source_title}
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
            ))}
          </div>
        )}

        {routeHistory.length > 0 && (
          <details className="vision-route">
            <summary>查看多 Agent 处理流程</summary>
            <ol>
              {routeHistory.map(
                (routeStep, index) => (
                  <li
                    key={`${routeStep}-${index}`}
                  >
                    {routeStep}
                  </li>
                ),
              )}
            </ol>
          </details>
        )}
      </section>
    </div>
  )
}


export default InspectionAnalysisMessage
