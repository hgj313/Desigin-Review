import { Card, Progress, Tag, List, Typography, Empty } from 'antd';
import type { Report, Finding } from '../types';

const { Title, Text } = Typography;

interface ReportViewProps {
  report: Report | null;
}

const severityConfig = {
  critical: { color: 'red', label: '严重' },
  high: { color: 'orange', label: '高' },
  medium: { color: 'gold', label: '中' },
  low: { color: 'blue', label: '低' },
};

export function ReportView({ report }: ReportViewProps) {
  if (!report) {
    return (
      <Card>
        <Empty description="暂无审查报告" />
      </Card>
    );
  }

  const scoreStatus = report.compliance_score >= 80
    ? 'success'
    : report.compliance_score >= 60
    ? 'normal'
    : 'exception';

  return (
    <Card title={`合规分数: ${report.compliance_score}/100`} style={{ marginTop: 24 }}>
      <Progress
        percent={report.compliance_score}
        status={scoreStatus}
        strokeColor={report.compliance_score >= 80 ? '#52c41a' : '#ff4d4f'}
      />

      <Title level={5} style={{ marginTop: 24 }}>审查结果摘要</Title>
      <Text>{report.summary}</Text>

      {report.findings.length > 0 && (
        <>
          <Title level={5} style={{ marginTop: 24 }}>发现问题 ({report.findings.length})</Title>
          <List
            bordered
            dataSource={report.findings}
            renderItem={(item: Finding) => {
              const config = severityConfig[item.severity] || severityConfig.low;
              return (
                <List.Item>
                  <Tag color={config.color}>{config.label}</Tag>
                  <Text strong style={{ marginRight: 8 }}>{item.dimension}</Text>
                  <Text type="secondary">{item.description}</Text>
                </List.Item>
              );
            }}
          />
        </>
      )}
    </Card>
  );
}