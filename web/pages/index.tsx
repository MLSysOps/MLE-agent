import { Chat } from "@/components/Chat/Chat";
import { Footer } from "@/components/Layout/Footer";
import { Navbar } from "@/components/Layout/Navbar";
import { ProjectMessage } from "@/types";
import Head from "next/head";
import { useEffect, useRef, useState } from "react";

export default function Home() {
  const [messages, setMessages] = useState<ProjectMessage[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Scroll to bottom of chat
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  // Handle sending a message
  const handleSend = async (message: ProjectMessage) => {
    const updatedMessages = [...messages, message];
  
    setMessages(updatedMessages);
    setLoading(true);
  
    const response = await fetch(`http://localhost:8000/chat?project=${encodeURIComponent(message.project)}&message=${encodeURIComponent(message.content)}`, {
      headers: {
        "Content-Type": "application/json",
      },
      method: "GET",
    });
  
    if (!response.ok) {
      setLoading(false);
      throw new Error(response.statusText);
    }
  
    const data = response.body;
  
    if (!data) {
      setLoading(false);
      return;
    }
  
    const reader = data.getReader();
    const decoder = new TextDecoder();
    let done = false;
    let isFirst = true;
  
    while (!done) {
      const { value, done: doneReading } = await reader.read();
      done = doneReading;
      const chunkValue = decoder.decode(value, { stream: true });
  
      setLoading(false);
      if (isFirst) {
        isFirst = false;
        setMessages((messages) => [
          ...messages,
          {
            role: "assistant",
            content: chunkValue,
            project: message.project,
          },
        ]);
      } else {
        setMessages((messages) => {
          const lastMessage = messages[messages.length - 1];
          const updatedMessage = {
            ...lastMessage,
            content: lastMessage.content + chunkValue,
          };
          return [...messages.slice(0, -1), updatedMessage];
        });
      }
  
      // Scroll to bottom after each chunk is added
      scrollToBottom();
    }
  };

  const handleReset = () => {
    setMessages([
      {
        role: "assistant",
        content: `Hi there! I'm MLE-Agent. How can I help you?`,
        project: "test2"
      }
    ]);
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    setMessages([
      {
        role: "assistant",
        content: `Hi there! I'm MLE-Agent. How can I help you?`,
        project: "test2"
      }
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
        <meta
          name="viewport"
          content="width=device-width, initial-scale=1"
        />
        <link
          rel="icon"
          href="/favicon.ico"
        />
      </Head>

      <div className="flex flex-col h-screen">
        <Navbar />

        <div className="flex-1 overflow-auto sm:px-10 pb-4 sm:pb-10">
          <div className="max-w-[800px] mx-auto mt-4 sm:mt-12">
            <Chat
              messages={messages}
              loading={loading}
              onSend={handleSend}
              onReset={handleReset}
            />
            <div ref={messagesEndRef} />
          </div>
        </div>
        <Footer />
      </div>
    </>
  );
}
