/**
 * /api/sessions/[id]/messages
 * 
 * NOTE: Message history persistence endpoint with Prisma integration.
 * Includes in-memory fallback for local running without PostgreSQL.
 */
import { NextResponse } from "next/server";

export const dynamic = "force-dynamic";

interface InMemMessage {
  id: string;
  sessionId: string;
  role: string;
  content: string;
  createdAt: string;
  agent?: string;
  state?: string;
  media?: string;
  steps?: string;
  ecosystemEscalation?: string;
}

const memoryMessages: Map<string, InMemMessage[]> = new Map();

// GET /api/sessions/[id]/messages — load all messages for a session
export async function GET(_req: Request, context: any) {
  try {
    const params = await context.params;
    const { PrismaClient } = await import("@prisma/client").catch(() => ({ PrismaClient: null }));
    if (PrismaClient) {
      try {
        const prisma = new PrismaClient();
        const messages = await prisma.chatMessage.findMany({
          where: { sessionId: params.id },
          orderBy: { createdAt: "asc" },
        });
        if (messages && messages.length > 0) return NextResponse.json(messages);
      } catch {
        // Continue to in-memory fallback
      }
    }

    const msgs = memoryMessages.get(params.id) || [];
    return NextResponse.json(msgs);
  } catch (err) {
    console.error("GET messages error:", err);
    return NextResponse.json([]);
  }
}

// POST /api/sessions/[id]/messages — save a message + bump session updatedAt
export async function POST(req: Request, context: any) {
  try {
    const params = await context.params;
    const body = await req.json().catch(() => ({}));
    const { role, content, agent, state, media, steps, ecosystemEscalation } = body;

    const { PrismaClient } = await import("@prisma/client").catch(() => ({ PrismaClient: null }));
    if (PrismaClient) {
      try {
        const prisma = new PrismaClient();
        const message = await (prisma.chatMessage.create as any)({
          data: {
            sessionId: params.id,
            role,
            content,
            agent: agent ?? null,
            state: state ?? null,
            media: media ? JSON.stringify(media) : null,
            steps: steps ? JSON.stringify(steps) : null,
            ecosystemEscalation: ecosystemEscalation ? JSON.stringify(ecosystemEscalation) : null,
          },
        });
        await prisma.chatSession.update({
          where: { id: params.id },
          data: { updatedAt: new Date() },
        });
        return NextResponse.json(message);
      } catch {
        // Continue to in-memory fallback
      }
    }

    const newMsg: InMemMessage = {
      id: `msg_${Date.now()}_${Math.random().toString(36).substr(2, 6)}`,
      sessionId: params.id,
      role: role || "user",
      content: content || "",
      createdAt: new Date().toISOString(),
      agent,
      state,
      media: media ? JSON.stringify(media) : undefined,
      steps: steps ? JSON.stringify(steps) : undefined,
      ecosystemEscalation: ecosystemEscalation ? JSON.stringify(ecosystemEscalation) : undefined,
    };

    const existing = memoryMessages.get(params.id) || [];
    existing.push(newMsg);
    memoryMessages.set(params.id, existing);

    return NextResponse.json(newMsg);
  } catch (err) {
    console.error("POST message error:", err);
    return NextResponse.json({ ok: true });
  }
}
