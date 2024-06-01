import { ProjectMessage } from "@/types";
import { FC } from "react";

interface Props {
	message: ProjectMessage;
}

export const ChatMessage: FC<Props> = ({ message }) => {
	return (
		<div
			className={`flex flex-col ${
				message.role === "system" ? "items-start" : "items-end"
			}`}
		>
			<div
				className={`flex items-center ${
					message.role === "system"
						? "bg-neutral-200 text-neutral-900"
						: "bg-blue-500 text-white"
				} rounded-2xl px-3 py-2 max-w-[90%] whitespace-pre-wrap`}
				style={{ overflowWrap: "anywhere" }}
			>
				{message.content}
			</div>
		</div>
	);
};
