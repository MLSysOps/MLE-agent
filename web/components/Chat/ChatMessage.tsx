import { Message } from "@/types";
import { FC } from "react";

import { MessageRequirement } from "./Requirement";
import { MessagePlan } from "./Plan";
import { MessageCode } from "./Code";
import { MessageSelect } from "./Select";

interface Props {
	message: Message;
}

export const ChatMessage: FC<Props> = ({ message }) => {
	const renderMessageView = () => {
		switch (message.msgType) {
			case "requirement":
				return <MessageRequirement message={message} />;
			case "plan":
				return <MessagePlan message={message} />;
			case "code":
				return <MessageCode message={message} />;
			case "select":
				return <MessageSelect message={message} />;
			default:
				return null;
		}
	};

	return (
		<div
			className={`flex flex-col ${
				message.role === "system" ? "items-start" : "items-end"
			}`}
		>
			<div
				className={`flex items-center ${
					message.role === "system" ? "bg-white" : "bg-blue-500"
				} rounded-2xl px-3 py-2`}
				style={{ overflowWrap: "anywhere" }}
			>
				{renderMessageView()}
			</div>
		</div>
	);
};
