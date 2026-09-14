"use client";

import { useState, useEffect, useCallback } from "react";
import Sidebar from "@/components/Sidebar";
import ChatInterface from "@/components/ChatInterface";
import { getSessions, createSession, deleteSession, ChatSession } from "@/lib/session";

export default function Home() {
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const loadSessions = useCallback(async () => {
    const loaded = await getSessions();
    if (loaded.length > 0) {
      setSessions(loaded);
      // Keep active session if still present, else open the first
      setActiveSessionId((prev) =>
        loaded.find((s) => s.id === prev) ? prev : loaded[0].id
      );
    } else {
      const init = await createSession("New Chat");
      setSessions([init]);
      setActiveSessionId(init.id);
    }
    setLoading(false);
  }, []);

  useEffect(() => {
    loadSessions();
  }, [loadSessions]);

  const handleNewChat = async () => {
    const newSess = await createSession("New Chat");
    await loadSessions();
    setActiveSessionId(newSess.id);
  };

  const handleSelectSession = (id: string) => {
    setActiveSessionId(id);
  };

  const handleSessionUpdated = async () => {
    await loadSessions();
  };

  const handleDeleteSession = async (id: string) => {
    await deleteSession(id);
    const updated = await getSessions();
    setSessions(updated);
    if (activeSessionId === id) {
      if (updated.length > 0) {
        setActiveSessionId(updated[0].id);
      } else {
        const fresh = await createSession("New Chat");
        setSessions([fresh]);
        setActiveSessionId(fresh.id);
      }
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-950 flex items-center justify-center">
        <div className="flex flex-col items-center gap-3">
          <div className="h-8 w-8 animate-spin rounded-full border-2 border-slate-600 border-t-white" />
          <span className="text-sm text-gray-500">Loading sessions...</span>
        </div>
      </div>
    );
  }

  return (
    <main className="flex h-screen w-full bg-gray-50 text-slate-800 overflow-hidden font-sans">
      <Sidebar
        sessions={sessions}
        activeSessionId={activeSessionId}
        onSelectSession={handleSelectSession}
        onNewChat={handleNewChat}
        onDeleteSession={handleDeleteSession}
      />

      <div className="flex flex-1 flex-col relative w-full h-full bg-white overflow-hidden shadow-[-4px_0_15px_rgba(0,0,0,0.05)] z-10 rounded-l-2xl">
        <header className="sticky top-0 z-10 flex w-full items-center border-b border-gray-100 bg-white/80 px-6 py-[14px] backdrop-blur-md relative min-h-[60px]">
          <div className="absolute left-1/2 -translate-x-1/2 flex items-center gap-3">
            <img src="/goose-icon.jpg" alt="Goose Icon" className="h-[32px] w-[32px] object-contain rounded-full border border-gray-200" />
            <span className="text-xl font-semibold tracking-tight text-gray-900">
              Goose Sense
            </span>
          </div>
        </header>

        <div className="flex-1 overflow-hidden relative">
          {activeSessionId && (
            <ChatInterface
              key={activeSessionId}
              sessionId={activeSessionId}
              onSessionUpdated={handleSessionUpdated}
            />
          )}
        </div>
      </div>
    </main>
  );
}
