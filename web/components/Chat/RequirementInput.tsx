import { ProjectMessage } from "@/types";
import { FC, useState } from "react";

import { Input } from "antd";

const { TextArea } = Input;

interface Props {
	onSubmit: (message: ProjectMessage) => void;
}

export const RequirementInput: FC<Props> = ({ onSubmit }) => {
	const [disable, setDisable] = useState<boolean>(false);

	const onChange = (
		e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>
	) => {
		console.log(e);
	};

	const handleSubmit = () => {
		onSubmit({ role: "user", content: "", project: "test2" });
		setDisable(true);
	};

	return (
		<div className="relative">
			<TextArea
				placeholder="textarea with clear icon"
				allowClear
				onChange={onChange}
				disabled={disable}
			/>
		</div>
	);
};
