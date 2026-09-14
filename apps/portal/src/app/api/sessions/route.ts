/**
 * /api/sessions
 * 
 * NOTE: This route was designed to persist chat sessions to a database via Prisma.
 * Because the internal `packages/database` schema is omitted from this public repository,
 * an in-memory store fallback is provided below so the Portal interface works out-of-the-box
 * without requiring a configured PostgreSQL instance.
 */
import { NextResponse } from "next/server";

export const dynamic = "force-dynamic";

// In-memory fallback session store
interface SessionItem {
  id: string;
  title: string;
  createdAt: string;
  updatedAt: string;
}

const memorySessions: Map<string, SessionItem> = new Map([
  [
    "default-session",
    {
      id: "default-session",
      title: "Pasteurizer Troubleshooting",
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    },
  ],
]);

export { memorySessions };

// GET /api/sessions — fetch all sessions, newest first
export async function GET() {
  try {
    const { PrismaClient } = await import("@prisma/client").catch(() => ({ PrismaClient: null }));
    if (PrismaClient) {
      try {
        const prisma = new PrismaClient();
        const sessions = await prisma.chatSession.findMany({
          orderBy: { updatedAt: "desc" },
        });
        if (sessions && sessions.length > 0) return NextResponse.json(sessions);
      } catch {
        // Fall back to memory store below
      }
    }

    const sessions = Array.from(memorySessions.values()).sort(
      (a, b) => new Date(b.updatedAt).getTime() - new Date(a.updatedAt).getTime()
    );
    return NextResponse.json(sessions);
  } catch (err) {
    console.error("GET /api/sessions error:", err);
    return NextResponse.json(Array.from(memorySessions.values()));
  }
}

// POST /api/sessions — create a new session
export async function POST(req: Request) {
  try {
    const body = await req.json().catch(() => ({}));
    const title = body?.title || "New Chat";
    const newId = `session_${Date.now()}_${Math.random().toString(36).substr(2, 6)}`;

    const { PrismaClient } = await import("@prisma/client").catch(() => ({ PrismaClient: null }));
    if (PrismaClient) {
      try {
        const prisma = new PrismaClient();
        const session = await prisma.chatSession.create({
          data: { title },
        });
        return NextResponse.json(session);
      } catch {
        // Fall back to memory store below
      }
    }

    const newSession: SessionItem = {
      id: newId,
      title,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    };
    memorySessions.set(newId, newSession);
    return NextResponse.json(newSession);
  } catch (err) {
    console.error("POST /api/sessions error:", err);
    const fallbackId = `fallback_${Date.now()}`;
    return NextResponse.json({
      id: fallbackId,
      title: "New Chat",
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    });
  }
}
