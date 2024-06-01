import { ProjectMessage } from "@/types";
import { FC } from "react";
import { RequirementInput } from "../Chat/RequirementInput";
import { ChatLoader } from "./ChatLoader";
import { ChatMessage } from "../Chat/ChatMessage";
import { ResetChat } from "./ResetChat";

import { Card } from "antd";

interface Props {
	messages: ProjectMessage[];
	loading: boolean;
	onSend: (message: ProjectMessage) => void;
	onReset: () => void;
}

export const Chat: FC<Props> = ({ messages, loading, onSend, onReset }) => {
	return (
		<Card bordered={false} style={{ flexGrow: 6, flexBasis: 0 }}>
			<div className="flex flex-row justify-between items-center mb-4 sm:mb-8">
				<ResetChat onReset={onReset} />
			</div>

			<div className="flex flex-col rounded-lg px-2 sm:p-4 sm:border border-neutral-300">
				{messages.map((message, index) => (
					<div key={index} className="my-1 sm:my-1.5">
						<ChatMessage message={message} />
					</div>
				))}

				{loading && (
					<div className="my-1 sm:my-1.5">
						<ChatLoader />
					</div>
				)}

				<div className="mt-4 sm:mt-8 bottom-[56px] left-0 w-full">
					<RequirementInput onSubmit={onSend} />
				</div>
			</div>
		</Card>
	);
};
