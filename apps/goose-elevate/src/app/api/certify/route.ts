/**
 * MOCK INTEGRATION ROUTE: /api/certify
 * 
 * NOTE: This endpoint demonstrates cross-app certification workflow linking
 * Goose Elevate training completions with HireMyEngineer talent profiles.
 * In this standalone open-source repository, the full PostgreSQL database schema is
 * not bundled, so this route safely returns a mock success payload if Prisma is unconfigured.
 */
import { NextResponse } from 'next/server';

export async function POST(req: Request) {
    try {
        const body = await req.json().catch(() => ({}));
        const studentName = body.name || "Jane Doe";
        const focusArea = body.focusArea || "S7-1500 Advanced";

        const { PrismaClient } = await import('@prisma/client').catch(() => ({ PrismaClient: null }));
        if (PrismaClient) {
            try {
                const prisma = new PrismaClient();
                // 1. Identify or Create the 'FRIAP Certified' Skill
                let certifySkill = await prisma.skill.findFirst({
                    where: { name: 'FRIAP Certified' }
                });

                if (!certifySkill) {
                    certifySkill = await prisma.skill.create({
                        data: { name: 'FRIAP Certified' }
                    });
                }

                // 2. Identify or Create the Technical Skill
                let techSkill = await prisma.skill.findFirst({
                    where: { name: focusArea }
                });

                if (!techSkill) {
                    techSkill = await prisma.skill.create({
                        data: { name: focusArea }
                    });
                }

                // 3. Create the New Expert Profile in HireMyEngineer Pipeline
                const newExpert = await prisma.expert.create({
                    data: {
                        name: `${studentName} - Recent Graduate`,
                        bio: `Freshly certified via the Goose Elevate FRIAP curriculum with a focus on ${focusArea}. Ready for field deployment.`,
                        skills: {
                            connect: [
                                { id: certifySkill.id },
                                { id: techSkill.id }
                            ]
                        }
                    },
                    include: { skills: true }
                });

                return NextResponse.json({
                    success: true,
                    message: `Expert ${newExpert.name} successfully certified and added to the HireMyEngineer talent pool.`,
                    expert: newExpert
                });
            } catch {
                // Return mock success fallback below
            }
        }

        // Mock fallback response for standalone mode
        return NextResponse.json({
            success: true,
            message: `[Demo Mode] Expert ${studentName} - Recent Graduate certified in ${focusArea}.`,
            expert: {
                id: "mock-expert-1",
                name: `${studentName} - Recent Graduate`,
                bio: `Freshly certified via the Goose Elevate FRIAP curriculum with a focus on ${focusArea}. Ready for field deployment.`,
                skills: [{ name: "FRIAP Certified" }, { name: focusArea }]
            }
        });

    } catch (error) {
        console.error("CERTIFICATION_ERROR", error);
        return NextResponse.json({ success: false, error: "Failed to process certification pipeline." }, { status: 500 });
    }
}
