import { useState } from 'react';
import { Upload, Button, Select, Space, message } from 'antd';
import { UploadOutlined } from '@ant-design/icons';
import type { UploadFile } from 'antd/es/upload/interface';
import { upload, triggerReview } from '../api/client';

interface UploadPanelProps {
  onReviewStart: () => void;
}

export function UploadPanel({ onReviewStart }: UploadPanelProps) {
  const [fileList, setFileList] = useState<UploadFile[]>([]);
  const [reviewType, setReviewType] = useState<'prd' | 'prototype'>('prd');
  const [uploading, setUploading] = useState(false);

  const handleUpload = async () => {
    if (!fileList[0]?.originFileObj) {
      message.warning('请先选择文件');
      return;
    }

    setUploading(true);
    try {
      const formData = new FormData();
      formData.append('file', fileList[0].originFileObj!);

      const uploadRes = await upload(formData);
      message.success(`文件 "${uploadRes.filename}" 上传成功`);

      await triggerReview({
        document_path: uploadRes.path,
        review_types: [reviewType],
      });
      message.success('审查任务已启动');
      setFileList([]);
      onReviewStart();
    } catch (err) {
      message.error('操作失败，请重试');
      console.error(err);
    } finally {
      setUploading(false);
    }
  };

  return (
    <Space direction="vertical" style={{ width: '100%' }} size="middle">
      <Upload.Dragger
        fileList={fileList}
        onChange={({ fileList: newFileList }) => setFileList(newFileList)}
        beforeUpload={() => false}
        accept=".md,.txt,.pdf,.png,.jpg,.jpeg,.gif,.webp"
        maxCount={1}
      >
        <Button icon={<UploadOutlined />}>点击或拖拽上传文件</Button>
        <p style={{ marginTop: 8, color: '#666' }}>
          支持 PRD 文档 (.md, .txt, .pdf) 和原型图 (.png, .jpg, .jpeg, .gif, .webp)
        </p>
      </Upload.Dragger>

      <Select
        value={reviewType}
        onChange={setReviewType}
        style={{ width: 200 }}
        options={[
          { value: 'prd', label: 'PRD 文档' },
          { value: 'prototype', label: '原型图' },
        ]}
      />

      <Button
        type="primary"
        loading={uploading}
        onClick={handleUpload}
        disabled={fileList.length === 0}
        size="large"
      >
        {uploading ? '处理中...' : '上传并审查'}
      </Button>
    </Space>
  );
}