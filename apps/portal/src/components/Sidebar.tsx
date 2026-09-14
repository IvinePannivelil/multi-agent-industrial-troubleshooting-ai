import { Plus, MessageSquare, Trash2 } from "lucide-react";
import { ChatSession } from "../lib/session";

interface SidebarProps {
  sessions: ChatSession[];
  activeSessionId: string | null;
  onSelectSession: (id: string) => void;
  onNewChat: () => void;
  onDeleteSession: (id: string) => void;
}

export default function Sidebar({ sessions, activeSessionId, onSelectSession, onNewChat, onDeleteSession }: SidebarProps) {
  return (
    <div className="grid grid-rows-[auto_auto_1fr_auto] h-screen w-[260px] bg-gray-900 text-gray-300">
      
      {/* Top Logo - Fixed Height */}
      <div className="px-3 pt-5 pb-2 flex justify-center border-b border-gray-800/50">
        <img 
          src="/goose-logo-full.jpg" 
          alt="Goose Logo" 
          className="h-[40px] w-auto object-contain bg-white px-3 py-1.5 rounded" 
        />
      </div>

      {/* New Chat Button - Fixed Height */}
      <div className="px-3 pt-4 pb-4">
        <button
          onClick={onNewChat}
          className="flex w-full items-center gap-2 rounded-lg bg-slate-800 p-2.5 px-3 text-sm font-medium text-white transition-all hover:bg-slate-700 hover:scale-[1.02] active:scale-[0.98]"
        >
          <Plus className="h-4 w-4 text-accent" />
          New Chat
        </button>
      </div>

      {/* Chat History Section - Scrolling Area */}
      <div className="min-h-0 overflow-y-auto px-3 overflow-x-hidden custom-scrollbar">
        <div className="mb-2 px-2 pt-2 text-[10px] font-bold text-gray-500 uppercase tracking-[0.1em]">
          History
        </div>
        <div className="flex flex-col gap-1.5 pb-20">
          {sessions.map((session) => (
            <div
              key={session.id}
              className={`group flex items-center justify-between gap-1 rounded-lg transition-all ${
                activeSessionId === session.id ? "bg-gray-800 text-white shadow-sm" : "hover:bg-gray-800/60"
              }`}
            >
              <button
                onClick={() => onSelectSession(session.id)}
                className="flex flex-1 items-center gap-3 truncate p-2.5 px-3 text-sm text-left outline-none"
              >
                <MessageSquare className={`h-4 w-4 shrink-0 ${activeSessionId === session.id ? "text-accent" : "text-gray-500"}`} />
                <span className="truncate font-medium">{session.title}</span>
              </button>
              
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  onDeleteSession(session.id);
                }}
                className={`p-2.5 pr-3 shrink-0 text-gray-500 hover:text-red-400 opacity-0 group-hover:opacity-100 transition-opacity ${activeSessionId === session.id ? "opacity-100" : ""}`}
                title="Delete Session"
              >
                <Trash2 className="h-4 w-4" />
              </button>
            </div>
          ))}
          {sessions.length === 0 && (
            <div className="p-3 text-center text-xs text-gray-500 italic">
              No previous conversations.
            </div>
          )}
        </div>
      </div>
      
      {/* Footer - Fixed at bottom */}
      <div className="p-4 border-t border-gray-800/80 bg-gray-950/20 text-[10px] font-medium text-center text-gray-500 uppercase tracking-widest">
        Enterprise Beta
      </div>
    </div>
  );
}
