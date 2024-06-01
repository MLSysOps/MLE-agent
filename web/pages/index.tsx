import { Chat } from "@/components/Agent/Chat";
import { Message } from "@/types";
import Head from "next/head";
import { useEffect, useRef, useState } from "react";

import { Card } from "antd";

export default function Home() {
	const [messages, setMessages] = useState<Message[]>([]);
	const [loading, setLoading] = useState<boolean>(false);
	const messagesEndRef = useRef<HTMLDivElement>(null);

	// Scroll to bottom of chat
	const scrollToBottom = () => {
		messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
	};

	// Handle sending a message
	const handleSend = async (message: Message) => {
		const updatedMessages = [...messages, message];

		setMessages(updatedMessages);
		setLoading(true);

		// const response = await fetch(
		// 	`http://localhost:8000/chat?project=${encodeURIComponent(
		// 		message.project.toString()
		// 	)}&message=${encodeURIComponent(message.content.toString())}`,
		// 	{
		// 		headers: {
		// 			"Content-Type": "application/json",
		// 		},
		// 		method: "GET",
		// 	}
		// );

		// if (!response.ok) {
		// 	setLoading(false);
		// 	throw new Error(response.statusText);
		// }

		// const data = response.body;

		// if (!data) {
		// 	setLoading(false);
		// 	return;
		// }

		// const reader = data.getReader();
		// const decoder = new TextDecoder();
		// let done = false;
		// let isFirst = true;

		// while (!done) {
		// 	const { value, done: doneReading } = await reader.read();
		// 	done = doneReading;
		// 	const chunkValue = decoder.decode(value, { stream: true });

		// 	setLoading(false);
		// 	if (isFirst) {
		// 		isFirst = false;
		// 		setMessages((messages) => [
		// 			...messages,
		// 			{
		// 				role: "system",
		// 				content: chunkValue,
		// 				project: message.project,
		// 			},
		// 		]);
		// 	} else {
		// 		setMessages((messages) => {
		// 			const lastMessage = messages[messages.length - 1];
		// 			const updatedMessage = {
		// 				...lastMessage,
		// 				content: lastMessage.content + chunkValue,
		// 			};
		// 			return [...messages.slice(0, -1), updatedMessage];
		// 		});
		// }

		// Scroll to bottom after each chunk is added
		// 	scrollToBottom();
		// }
	};

	const handleReset = () => {
		setMessages([
			{
				role: "system",
				msgType: "requirement",
				project: "test2",
			},
		]);
	};

	useEffect(() => {
		scrollToBottom();
	}, [messages]);

	useEffect(() => {
		setMessages([
			{
				role: "system",
				msgType: "requirement",
				project: "test2",
			},
			{
				role: "user",
				msgType: "requirement",
				project: "test2",
			},
		]);
	}, []);

	return (
		<>
			<Head>
				<title>MLE-Agent</title>
				<meta
					name="description"
					content="MLE-agent is an LLM agent to help you build your AI projects."
				/>
				<meta name="viewport" content="width=device-width, initial-scale=1" />
				<link rel="icon" href="/favicon.ico" />
			</Head>

			<div
				style={{
					display: "flex",
					flexDirection: "row",
					minHeight: "100vh",
					padding: 10,
				}}
			>
				<Chat
					messages={messages}
					loading={loading}
					onSend={handleSend}
					onReset={handleReset}
				/>
				<Card
					bordered={false}
					style={{ flexGrow: 5, flexBasis: 0, marginLeft: 10 }}
				></Card>

				<div ref={messagesEndRef} />
			</div>
		</>
	);
}
