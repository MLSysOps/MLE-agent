import { Message } from "@/types";
import { FC, useState } from "react";

import { Button, Form, Input } from "antd";

const { TextArea } = Input;
const formItemLayout = {
	labelCol: {
		xs: { span: 24 },
		sm: { span: 6 },
	},
	wrapperCol: {
		xs: { span: 24 },
		sm: { span: 14 },
	},
};

interface Props {
	message: Message;
}

export const MessageCode: FC<Props> = ({ message }) => {
	const [disable, setDisable] = useState<boolean>(true);

	const onChange = (
		e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>
	) => {
		console.log(e);
	};

	const handleSubmit = () => {
		// onSubmit({ });
		setDisable(true);
	};

	return (
		<div className="relative">
			<Form {...formItemLayout} variant="filled" style={{ maxWidth: 600 }}>
				<Form.Item
					label="Project Name"
					name="projectName"
					rules={[{ required: true, message: "Please input the project name" }]}
				>
					<Input disabled={disable} />
				</Form.Item>

				<Form.Item
					label="User Requirements"
					name="userRequirements"
					rules={[
						{ required: true, message: "Please input the user's requirements" },
					]}
				>
					<Input.TextArea disabled={disable} />
				</Form.Item>
				<Form.Item wrapperCol={{ offset: 6, span: 16 }}>
					<Button type="primary" htmlType="submit" disabled={disable}>
						Submit
					</Button>
				</Form.Item>
			</Form>
		</div>
	);
};
