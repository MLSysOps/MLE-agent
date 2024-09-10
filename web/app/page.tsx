"use client";
import React, { useState, useEffect } from 'react';
import { Layout, Card, Input, Button, message, Form, Select, Spin, Flex, Row, Col } from 'antd';
import { HomeOutlined, BookOutlined, MailOutlined, GithubOutlined, XOutlined, DiscordOutlined} from '@ant-design/icons';
import dynamic from "next/dynamic";

const MDEditor = dynamic(
  () => import("@uiw/react-md-editor"),
  { ssr: false }
);
const { Content, Header } = Layout;
const { TextArea } = Input;
const { Option } = Select;

interface ReportData {
  project_okr: string;
  business_goal: string[];
  dev_progress: string[];
  communicate_progress: string[];
  dev_todo: { task: string; description: string; priority: string }[];
  communicate_todo: { task: string; priority: string }[];
  hard_parts: string[];
  require_manager_help: string[];
  suggestions_to_user: string[];
  reference: { title: string; link: string;}[];
}

interface ReportRequest {
  repo: string;
  username: string;
  okr?: string;
  dateRange?: string;
  recurringReports?: string;
  additionalSources?: string[];
}

export default function Home() {
  const [reportContent, setReportContent] = useState<string>("");
  const [reportData, setReportData] = useState<ReportData | null>(null);
  const [form] = Form.useForm<ReportRequest>();
  const [loading, setLoading] = useState<boolean>(false);

  useEffect(() => {
    fetchLatestReport();
    form.setFieldsValue({ recurringReports: 'weekly' });
  }, [form]);

  const fetchLatestReport = async () => {
    try {
      const response = await fetch('http://localhost:8000/latest_report');
      if (response.status === 404) {
        setReportContent("No report has been found. Please click 'Generate Report' to create one.");
        setReportData(null);
        return;
      }
      if (!response.ok) {
        throw new Error('Failed to fetch the latest report');
      }
      const data: ReportData = await response.json();
      setReportData(data);
      const markdownContent = convertToMarkdown(data);
      setReportContent(markdownContent);
    } catch (error) {
      console.error('Error fetching latest report:', error);
      message.error('Failed to fetch the latest report');
    }
  };

  const convertToMarkdown = (data: ReportData): string => {
    let markdown = '';
    markdown += `## Project Report\n\n`;

    if (data.project_okr) {
      markdown += `### Project OKR\n${data.project_okr}\n\n`;
    }

    markdown += `### Business Goal\n${data.business_goal.map(goal => `- ${goal}`).join('\n')}\n\n`;
    markdown += `### Work Finished This Week\n\n`;
    markdown += `#### Development Progress\n${data.dev_progress.map(progress => `- ${progress}`).join('\n')}\n\n`;
    markdown += `#### Communication/Design Progress\n${data.communicate_progress.map(progress => `- ${progress}`).join('\n')}\n\n`;
    markdown += `### Work TODOs in the Next Week\n\n`;
    markdown += `#### Development TODOs\n${data.dev_todo.map(todo => `- ${todo.task} **(${todo.priority})**: ${todo.description}`).join('\n')}\n\n`;
    markdown += `#### Communication TODOs\n${data.communicate_todo.map(todo => `- ${todo.task} **(${todo.priority})**`).join('\n')}\n\n`;
    markdown += `### Hard Problems\n\n`;
    markdown += `#### Challenges\n${data.hard_parts.map(part => `- ${part}`).join('\n')}\n\n`;
    markdown += `#### Manager Help Required\n${data.require_manager_help.map(help => `- ${help}`).join('\n')}\n\n`;
    markdown += `### Other Progress and Thoughts\n\n`;
    markdown += `#### Suggestions\n${data.suggestions_to_user.map(suggestion => `- ${suggestion}`).join('\n')}\n\n`;
    markdown += `#### References\n${data.reference.map(ref => `- [${ref.title}](${ref.link})`).join('\n')}\n\n`;
    return markdown;
  };

  const handleGenerateReport = async (values: ReportRequest) => {
    setLoading(true);
    try {
      const response = await fetch('http://localhost:8000/gen_report', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(values),
      });

      if (!response.ok) {
        throw new Error('Failed to generate report');
      }

      const result = await response.json();
      
      if (result.result) {
        setReportData(result.result);
        const markdownContent = convertToMarkdown(result.result);
        setReportContent(markdownContent);
        message.success('Report generated successfully');
      } else {
        message.info('Report generation completed, but no data returned');
      }
    } catch (error) {
      console.error('Error generating report:', error);
      message.error('Failed to generate report');
    } finally {
      setLoading(false);
    }
  };

  const handleSaveReport = () => {
    message.info('Save report functionality not implemented yet');
  };

  return (
    <Layout className="min-h-screen">
      <Header style={{ backgroundColor: '#f5f5f5' }}>
        <Row gutter={16} style={{ paddingTop: '10px' }}>
          <Col span={8}>
            <a href='https://repx.app/' style={{ display: 'block', textAlign: 'left' }}>
              <img src='./logo.png' style={{ height: '3rem', display: 'inline-block' }} alt="Repx.app" />
            </a>
          </Col>
          <Col offset={8} span={8}>
            <Flex style={{ display: 'flex', height: '100%' }} align='flex-end' justify='flex-end'>
              <Button type="text" block style={{ width: '100px' }} icon={<HomeOutlined />} href="https://repx.app/">
                Home
              </Button>
              <Button type="text" block style={{ width: '100px' }} icon={<BookOutlined />} href="https://docs.repx.app/">
                Docs
              </Button>
              <Button type="text" block style={{ width: '120px' }} icon={<DiscordOutlined />} href="https://discord.gg/xHW3Yz4x">
                Feedback
              </Button>
              <Button type="text" block style={{ minWidth: '48px', maxWidth: '48px' }} icon={<GithubOutlined />} href="https://github.com/MLSysOps/MLE-agent"/>
              <Button type="text" block style={{ minWidth: '48px', maxWidth: '48px' }} icon={<XOutlined />} href="https://x.com/zhzHNN/"/>
            </Flex>
          </Col>
        </Row>
      </Header>
      <Content className="p-8">
        <div className="flex gap-4" style={{ alignItems: 'flex-start' }}>
          <Card className="w-[70%]" style={{ maxHeight: 'calc(100vh - 50px)', overflowY: 'auto' }}>
            <Spin size="large" spinning={loading} tip="Generating. This may take a few minutes...">
              <MDEditor value={reportContent} preview='preview' onChange={setReportContent} height='calc(100vh - 50px)'/>
            </Spin>
          </Card>

          <Card className="w-[30%]" title="Settings" style={{ position: 'sticky', top: '20px' }}>
            <Form
              form={form}
              onFinish={handleGenerateReport}
              layout="vertical"
            >
              <Form.Item
                name="token"
                label="GitHub Token"
                rules={[{ required: true, message: 'Please enter the GitHub token' }]}
              >
                <Input placeholder="Enter GitHub token" type="password"/>
              </Form.Item>
              <Form.Item
                name="repo"
                label="Repository"
                rules={[{ required: true, message: 'Please enter the GitHub repository' }]}
              >
                <Input placeholder="Enter GitHub repository" />
              </Form.Item>
              <Form.Item
                name="username"
                label="Username"
                rules={[{ required: true, message: 'Please enter the GitHub username' }]}
              >
                <Input placeholder="Enter GitHub username" />
              </Form.Item>
              <Form.Item
                name="dateRange"
                label="Date Range"
                rules={[{ message: 'Please select a date range' }]}
              >
                <Select placeholder="Select date range">
                  <Option value="lastDay">Last Day</Option>
                  <Option value="lastWeek">Last Week</Option>
                  <Option value="lastMonth">Last Month</Option>
                </Select>
              </Form.Item>
              <Form.Item
                name="okr"
                label="OKR (Optional)"
              >
                <TextArea 
                  placeholder="Enter OKR"
                  autoSize={{ minRows: 3, maxRows: 6 }}
                />
              </Form.Item>
              <Form.Item
                name="additionalSources"
                label={
                  <span>
                    Additional Data Sources (
                    <a href="https://repx.app" target="_blank" rel="noopener noreferrer">RepX PRO</a> required)
                  </span>
                }
              >
                <div style={{ display: 'flex', width: '100%' }}>
                  <Button style={{ flex: '1 1 0', margin: '2px' }} href='https://repx.app'>Zoom Meetings</Button>
                  <Button style={{ flex: '1 1 0', margin: '2px' }} href='https://repx.app'>Google Calendar</Button>
                </div>
                <div style={{ display: 'flex', width: '100%'}}>
                  <Button style={{ flex: '1 1 0', margin: '2px' }} href='https://repx.app'>Slack</Button>
                  <Button style={{ flex: '1 1 0', margin: '2px' }} href='https://repx.app'>GitLab</Button>
                </div>
              </Form.Item>
              <Form.Item
                name="recurringReports"
                label="Recurring Reports"
                rules={[{ required: false, message: 'Please select a recurring option' }]}
              >
                <Select disabled placeholder="Select recurring option">
                  <Option value="daily">Daily</Option>
                  <Option value="weekly">Weekly</Option>
                  <Option value="monthly">Monthly</Option>
                  <Option value="never">Never</Option>
                </Select>
              </Form.Item>
              <Form.Item>
              <div style={{ display: 'flex', width: '100%' }}>
                  <Button style={{ flex: '1 1 0', marginRight: '4px' }} type="primary" htmlType="submit" loading={loading}>
                    Generate Report
                  </Button>
                </div>
              </Form.Item>
            </Form>
          </Card>
        </div>
      </Content>
    </Layout>
  );
}