import { useState, useEffect } from 'react';
import { Layout, Typography, List, Card, Spin, Button, Space, message, Tag } from 'antd';
import { ReloadOutlined } from '@ant-design/icons';
import { UploadPanel } from './components/UploadPanel';
import { ReportView } from './components/ReportView';
import { listReports, healthCheck } from './api/client';
import type { Report } from './types';

const { Header, Content } = Layout;
const { Title, Text } = Typography;

function App() {
  const [reports, setReports] = useState<Report[]>([]);
  const [loading, setLoading] = useState(false);
  const [selectedReport, setSelectedReport] = useState<Report | null>(null);
  const [apiHealthy, setApiHealthy] = useState<boolean | null>(null);

  const fetchReports = async () => {
    setLoading(true);
    try {
      const data = await listReports();
      setReports(data);
      if (data.length > 0 && !selectedReport) {
        setSelectedReport(data[0]);
      }
    } catch (err) {
      console.error('Failed to fetch reports:', err);
    } finally {
      setLoading(false);
    }
  };

  const checkApiHealth = async () => {
    try {
      await healthCheck();
      setApiHealthy(true);
    } catch {
      setApiHealthy(false);
      message.error('无法连接到后端 API，请确保 FastAPI 服务已启动');
    }
  };

  useEffect(() => {
    checkApiHealth();
    fetchReports();
  }, []);

  const handleReviewStart = () => {
    fetchReports();
  };

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Header style={{ background: '#001529', padding: '0 24px', display: 'flex', alignItems: 'center' }}>
        <Title level={3} style={{ color: 'white', margin: 0 }}>设计文档审查系统</Title>
        {apiHealthy === false && (
          <Tag color="error" style={{ marginLeft: 16 }}>API 未连接</Tag>
        )}
      </Header>

      <Content style={{ padding: '24px 48px', maxWidth: 1200, margin: '0 auto', width: '100%' }}>
        <Card title="上传文件" style={{ marginBottom: 24 }}>
          <UploadPanel onReviewStart={handleReviewStart} />
        </Card>

        <Space style={{ marginBottom: 16 }}>
          <Button
            icon={<ReloadOutlined />}
            onClick={fetchReports}
            loading={loading}
          >
            刷新报告列表
          </Button>
        </Space>

        {loading ? (
          <Spin size="large" style={{ display: 'block', textAlign: 'center', margin: 40 }} />
        ) : (
          <Card title="历史报告" style={{ marginBottom: 24 }}>
            {reports.length === 0 ? (
              <Text type="secondary">暂无审查报告</Text>
            ) : (
              <List
                bordered
                dataSource={reports}
                renderItem={(item) => (
                  <List.Item
                    onClick={() => setSelectedReport(item)}
                    style={{
                      cursor: 'pointer',
                      background: selectedReport?.report_id === item.report_id ? '#f0f0f0' : undefined,
                    }}
                  >
                    <List.Item.Meta
                      title={`报告 ${item.report_id.slice(0, 8)}...`}
                      description={
                        <Space>
                          <Tag color={item.compliance_score >= 80 ? 'green' : item.compliance_score >= 60 ? 'orange' : 'red'}>
                            {item.compliance_score}/100
                          </Tag>
                          <Text type="secondary">{item.findings.length} 个问题</Text>
                        </Space>
                      }
                    />
                  </List.Item>
                )}
              />
            )}
          </Card>
        )}

        {selectedReport && <ReportView report={selectedReport} />}
      </Content>
    </Layout>
  );
}

export default App;