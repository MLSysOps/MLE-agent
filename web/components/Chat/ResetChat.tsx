import { FC } from "react";
import { Button } from "antd";

interface Props {
	onReset: () => void;
}

export const ResetChat: FC<Props> = ({ onReset }) => {
	return (
		<div className="flex flex-row items-center">
			<Button onClick={() => onReset()}>Reset</Button>
		</div>
	);
};
