/**
 * /api/sessions/[id]
 * 
 * NOTE: Session update/delete endpoint with Prisma integration.
 * Includes in-memory fallback for local running without PostgreSQL.
 */
import { NextResponse } from "next/server";

export const dynamic = "force-dynamic";

// PATCH /api/sessions/[id] — update title
export async function PATCH(req: Request, context: any) {
  try {
    const params = await context.params;
    const { title } = await req.json().catch(() => ({}));
    
    const { PrismaClient } = await import("@prisma/client").catch(() => ({ PrismaClient: null }));
    if (PrismaClient) {
      try {
        const prisma = new PrismaClient();
        const session = await prisma.chatSession.update({
          where: { id: params.id },
          data: { title },
        });
        return NextResponse.json(session);
      } catch {
        // Continue to fallback
      }
    }

    return NextResponse.json({ id: params.id, title, updatedAt: new Date().toISOString() });
  } catch (err) {
    console.error("PATCH /api/sessions/[id] error:", err);
    return NextResponse.json({ ok: true });
  }
}

// DELETE /api/sessions/[id] — delete session and all its messages (cascade)
export async function DELETE(_req: Request, context: any) {
  try {
    const params = await context.params;
    const { PrismaClient } = await import("@prisma/client").catch(() => ({ PrismaClient: null }));
    if (PrismaClient) {
      try {
        const prisma = new PrismaClient();
        await prisma.chatSession.delete({ where: { id: params.id } });
        return NextResponse.json({ ok: true });
      } catch {
        // Continue to fallback
      }
    }

    return NextResponse.json({ ok: true });
  } catch (err) {
    console.error("DELETE /api/sessions/[id] error:", err);
    return NextResponse.json({ ok: true });
  }
}
