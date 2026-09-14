// All session persistence is now backed by the database via API routes.
// No more localStorage — sessions survive browser restarts.

export interface ChatSession {
  id: string;
  title: string;
  createdAt: string;
  updatedAt: string;
}

export interface DbMessage {
  id: string;
  sessionId: string;
  role: "user" | "assistant";
  content: string;
  createdAt: string;
}

// ── Sessions ──────────────────────────────────────────────────────────────────

export async function getSessions(): Promise<ChatSession[]> {
  const res = await fetch("/api/sessions", { cache: "no-store", headers: { 'Cache-Control': 'no-cache' } });
  if (!res.ok) return [];
  return res.json();
}

export async function createSession(title: string = "New Chat"): Promise<ChatSession> {
  const res = await fetch("/api/sessions", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ title }),
  });
  return res.json();
}

export async function updateSessionTitle(id: string, title: string): Promise<void> {
  await fetch(`/api/sessions/${id}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ title }),
  });
}

export async function deleteSession(id: string): Promise<void> {
  await fetch(`/api/sessions/${id}`, { method: "DELETE" });
}

// ── Messages ──────────────────────────────────────────────────────────────────

export async function getMessages(sessionId: string): Promise<DbMessage[]> {
  const res = await fetch(`/api/sessions/${sessionId}/messages`, { cache: "no-store", headers: { 'Cache-Control': 'no-cache' } });
  if (!res.ok) return [];
  return res.json();
}

export async function saveMessage(
  sessionId: string,
  role: "user" | "assistant",
  content: string,
  metadata?: {
    agent?: string;
    state?: string;
    media?: { image?: string; video?: string };
    steps?: string[];
    ecosystemEscalation?: Record<string, string>;
  }
): Promise<void> {
  await fetch(`/api/sessions/${sessionId}/messages`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      role,
      content,
      ...(metadata ?? {}),
    }),
  });
}
