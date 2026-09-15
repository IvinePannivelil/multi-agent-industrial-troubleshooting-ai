"use client";

import { useEffect, useRef, useState } from "react";
import ChatMessage, { MessageProps } from "./ChatMessage";
import ChatInput from "./ChatInput";
import { AttachedFile } from "./FileUpload";
import { sendChatMessage } from "../lib/api";
import { AlertCircle, Loader2 } from "lucide-react";
import { getMessages, saveMessage, updateSessionTitle } from "@/lib/session";

interface ChatInterfaceProps {
  sessionId: string;
  onSessionUpdated: () => void;
}

export default function ChatInterface({ sessionId, onSessionUpdated }: ChatInterfaceProps) {
  const [messages, setMessages] = useState<MessageProps[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const endOfMessagesRef = useRef<HTMLDivElement>(null);
  const isFirstMessage = useRef(true);

  // Load message history from DB when session changes
  useEffect(() => {
    isFirstMessage.current = true;
    getMessages(sessionId).then((dbMsgs) => {
      const mapped: MessageProps[] = dbMsgs.map((m: any) => ({
        role: m.role as "user" | "assistant",
        content: m.content,
        agent: m.agent ?? undefined,
        state: m.state ?? undefined,
        media: m.media ? JSON.parse(m.media) : undefined,
        steps: m.steps ? JSON.parse(m.steps) : undefined,
        ecosystem_escalation: m.ecosystemEscalation ? JSON.parse(m.ecosystemEscalation) : undefined,
      }));
      setMessages(mapped);
      if (mapped.length > 0) isFirstMessage.current = false;
    });
  }, [sessionId]);

  // Scroll on new message
  useEffect(() => {
    endOfMessagesRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSend = async (query: string, file: AttachedFile | null) => {
    if ((!query.trim() && !file) || !sessionId) return;

    let displayContent = query;
    if (file && !query) displayContent = `Uploaded file: ${file.file.name}`;

    const userMsg: MessageProps = { role: "user", content: displayContent };
    const nextMessages = [...messages, userMsg];
    setMessages(nextMessages);
    setIsLoading(true);
    setError(null);

    // Save user message to DB
    await saveMessage(sessionId, "user", displayContent);

    // On first message, update the session title intelligently in the background
    if (isFirstMessage.current) {
      isFirstMessage.current = false;
      (async () => {
        try {
          const promptText = query.trim() || (file ? `File: ${file.file.name}` : "New Chat");
          const titleRes = await fetch("http://localhost:8001/generate-title", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ query: promptText }),
          });
          const titleData = await titleRes.json();
          await updateSessionTitle(sessionId, titleData.title || "New Session");
          onSessionUpdated();
        } catch (err) {
          const fallback = query.trim().substring(0, 40) || "New Chat";
          await updateSessionTitle(sessionId, fallback);
          onSessionUpdated();
        }
      })();
    }

    try {
      // Process File Upload if present
      if (file) {
        const formData = new FormData();
        formData.append("file", file.file);
        formData.append("session_id", sessionId);

        const uploadRes = await fetch("http://localhost:8001/upload-document", {
          method: "POST",
          body: formData,
        });

        if (!uploadRes.ok) throw new Error("Failed to upload document");

        const uploadData = await uploadRes.json();
        const uploadMsgContent = `Indexed ${file.file.name} (${uploadData.chunks_added || 0} chunks)`;

        const uploadMsg: MessageProps = {
          role: "assistant",
          content: uploadMsgContent,
          agent: "Ingestion System",
        };

        const withUpload = [...nextMessages, uploadMsg];
        setMessages(withUpload);
        await saveMessage(sessionId, "assistant", uploadMsgContent);
      }

      // Process Chat Query if present
      if (query.trim()) {
        const response = await sendChatMessage(sessionId, query);

        const assistantContent = response.response_text || "I was unable to formulate a response.";
        const assistantMsg: MessageProps = {
          role: "assistant",
          content: assistantContent,
          agent: response.agent_used,
          sources: response.sources,
          state: response.state,
          media: response.media,
          steps: response.steps,
          ecosystem_escalation: response.ecosystem_escalation,
        };

        setMessages((prev) => [...prev, assistantMsg]);
        await saveMessage(sessionId, "assistant", assistantContent, {
          agent: response.agent_used,
          state: response.state,
          media: response.media,
          steps: response.steps,
          ecosystemEscalation: response.ecosystem_escalation,
        });
      }
    } catch (err: any) {
      setError(err.message || "Unable to connect to assistant backend.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex h-full w-full flex-col bg-transparent relative">
      <div className="flex-1 overflow-y-auto px-4 py-6 sm:px-6 lg:px-8">
        <div className="mx-auto flex max-w-3xl flex-col gap-6 w-full">
          {messages.length === 0 && (
            <div className="flex flex-col items-center justify-center pt-24 text-center text-gray-500">
              <div className="mb-4 rounded-full bg-white p-4 shadow-sm border border-gray-200">
                <img src="/goose-icon.jpg" alt="Goose Icon" className="h-10 w-10 object-contain rounded-full" />
              </div>
              <h3 className="text-xl font-semibold text-gray-800">How can I help you today?</h3>
              <p className="mt-2 max-w-sm text-sm text-gray-500">
                Upload manuals, ask about products, or get troubleshooting advice.
              </p>
            </div>
          )}

          {messages.map((msg, idx) => (
            <div key={idx} className={`flex w-full ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
              <ChatMessage {...msg} />
            </div>
          ))}

          {isLoading && (
            <div className="flex w-full items-center justify-start gap-2 py-2 text-sm text-gray-500">
              <Loader2 className="h-4 w-4 animate-spin text-gray-400" />
              Industrial Assistant is thinking...
            </div>
          )}

          {error && (
            <div className="flex w-full items-center gap-2 rounded-lg bg-red-50 p-3 text-sm text-red-800 border border-red-200 shadow-sm mt-2">
              <AlertCircle className="h-4 w-4 shrink-0" />
              {error}
            </div>
          )}

          <div ref={endOfMessagesRef} className="h-4" />
        </div>
      </div>

      <div className="bg-transparent px-4 py-4 sm:px-6 lg:px-8 sticky bottom-0">
        <div className="mx-auto max-w-3xl">
          <ChatInput onSend={handleSend} isLoading={isLoading} />
          <div className="mt-3 text-center text-xs text-gray-400">
            Industrial AI Assistant can make mistakes. Verify critical industrial information.
          </div>
        </div>
      </div>
    </div>
  );
}
