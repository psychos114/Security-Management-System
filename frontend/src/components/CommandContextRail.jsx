import {
  CheckIcon,
  FileTextIcon,
  RobotIcon,
  WarningCircleIcon,
  XIcon,
} from '@phosphor-icons/react'


const RISK_LABELS = {
  low: '低风险',
  medium: '中风险',
  high: '高风险',
  critical: '严重风险',
}


const AGENT_LABELS = {
  emergency: '突发事件Agent',
  inspection: '巡检Agent',
  complaint_report: '投诉日报Agent',
  fire_compliance: '消防法规Agent',
  general: '通用调度',
}


function CommandContextRail({
  confirmationNote,
  isConfirming,
  latestMessage,
  onConfirm,
  onConfirmationNoteChange,
  pendingApprovalMessage,
}) {
  const riskLevel =
    latestMessage?.riskLevel || 'low'

  const citations =
    latestMessage?.citations || []

  const agentLabel =
    AGENT_LABELS[latestMessage?.category]
    || '等待调度'

  return (
    <aside className="command-context">
      <section className="context-block">
        <h2>事件风险等级</h2>

        {latestMessage ? (
          <div
            className={
              `context-risk risk-${riskLevel}`
            }
          >
            <WarningCircleIcon
              size={34}
              weight="fill"
            />

            <div>
              <strong>
                {RISK_LABELS[riskLevel]
                  || riskLevel}
              </strong>

              <span>
                {pendingApprovalMessage
                  ? '等待人工确认'
                  : '当前无需审批'}
              </span>
            </div>
          </div>
        ) : (
          <p className="context-empty">
            提交问题后显示风险评估。
          </p>
        )}
      </section>

      <section className="context-block">
        <h2>当前专业Agent</h2>

        <div className="context-agent">
          <RobotIcon
            size={40}
            weight="duotone"
          />

          <div>
            <strong>{agentLabel}</strong>

            <span>
              {latestMessage
                ? '已完成专业路线调度'
                : '等待接收业务问题'}
            </span>
          </div>
        </div>
      </section>

      <section className="context-block">
        <h2>知识库证据</h2>

        {citations.length > 0 ? (
          <div className="context-evidence-list">
            {citations
              .slice(0, 4)
              .map((citation, index) => (
                <a
                  key={
                    `${
                      citation.reference_id
                      || 'citation'
                    }-${index}`
                  }
                  href={
                    citation.official_url
                    || undefined
                  }
                  target={
                    citation.official_url
                      ? '_blank'
                      : undefined
                  }
                  rel={
                    citation.official_url
                      ? 'noreferrer'
                      : undefined
                  }
                  onClick={(event) => {
                    if (
                      !citation.official_url
                    ) {
                      event.preventDefault()
                    }
                  }}
                >
                  <FileTextIcon size={18} />

                  <span>
                    <strong>
                      {
                        citation.reference_id
                        || '内部资料'
                      }
                    </strong>

                    <small>
                      {
                        citation.document_title
                        || citation.source_title
                        || '知识库资料'
                      }
                    </small>
                  </span>
                </a>
              ))}
          </div>
        ) : (
          <p className="context-empty">
            Agent打开完整资料后，
            真实引用会显示在这里。
          </p>
        )}
      </section>

      {pendingApprovalMessage && (
        <section
          className={
            'context-block context-approval'
          }
        >
          <h2>待人工确认</h2>

          <p className="approval-warning">
            关键动作需人工确认后执行，
            请审慎决策。
          </p>

          <p className="approval-summary">
            {
              pendingApprovalMessage
                .pendingAction
                ?.summary
              || 'Agent建议执行关键动作'
            }
          </p>

          <label htmlFor="rail-confirmation-note">
            审批说明
          </label>

          <textarea
            id="rail-confirmation-note"
            value={confirmationNote}
            maxLength={500}
            disabled={isConfirming}
            onChange={(event) => {
              onConfirmationNoteChange(
                event.target.value,
              )
            }}
          />

          <div className="context-approval-actions">
            <button
              className="context-approve"
              type="button"
              disabled={isConfirming}
              onClick={() => {
                onConfirm(
                  pendingApprovalMessage.id,
                  pendingApprovalMessage
                    .requestId,
                  true,
                )
              }}
            >
              <CheckIcon
                size={22}
                weight="bold"
              />

              {isConfirming
                ? '正在提交'
                : '批准建议'}
            </button>

            <button
              className="context-reject"
              type="button"
              disabled={isConfirming}
              onClick={() => {
                onConfirm(
                  pendingApprovalMessage.id,
                  pendingApprovalMessage
                    .requestId,
                  false,
                )
              }}
            >
              <XIcon
                size={22}
                weight="bold"
              />

              拒绝建议
            </button>
          </div>

          <small className="approval-boundary">
            真实动作尚未执行。
          </small>
        </section>
      )}
    </aside>
  )
}


export default CommandContextRail