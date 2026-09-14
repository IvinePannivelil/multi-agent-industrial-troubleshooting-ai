/**
 * LEGACY / EXPERIMENTAL ROUTE: /api/doubt
 * 
 * NOTE: This endpoint was an early prototype that called an internal `@goose/database`
 * package directly from Next.js server routes.
 * 
 * In the active architecture, the Portal frontend communicates directly with the
 * Python FastAPI backend (`apps/sense-api` on port 8001 via `/chat` and `/upload-document`).
 * A stub for `@goose/database` is provided in `packages/database` for build compatibility.
 */
import { NextResponse } from 'next/server';
import { EcosystemRouter, processImage, processPDF, processExcel } from '@goose/database';

export async function POST(request: Request) {
    try {
        const contentType = request.headers.get('content-type') || '';

        // ── File upload path (image, PDF, Excel, CSV) ──────────────────────────
        if (contentType.includes('multipart/form-data')) {
            const formData = await request.formData();
            const uploadedFile = formData.get('file') as File | null;
            const query = formData.get('query') as string | null;

            if (!uploadedFile) {
                return NextResponse.json({ message: 'No file provided in form data.' }, { status: 400 });
            }

            const mime = uploadedFile.type || '';
            const arrayBuffer = await uploadedFile.arrayBuffer();
            const buffer = Buffer.from(arrayBuffer);

            // ── Image → Vision handler ──────────────────────────────────────
            if (mime.startsWith('image/')) {
                const base64Data = buffer.toString('base64');
                const result = await processImage(base64Data, mime);
                return NextResponse.json({
                    state: 'RESOLVED',
                    intent: 'HARDWARE_AND_PARTS',
                    chatResponse: result.chatResponse,
                    sources: result.sources,
                    componentName: result.componentName,
                    recommendations: { products: [], courses: [], experts: [], upgrades: [], shieldPlans: [], actionLinks: [] }
                });
            }

            // ── PDF → Text extraction + Gemini Q&A ─────────────────────────
            if (mime === 'application/pdf') {
                const result = await processPDF(buffer, query || '');
                return NextResponse.json({
                    state: 'RESOLVED',
                    intent: 'KNOWLEDGE_GAP',
                    chatResponse: result.chatResponse,
                    sources: result.sources,
                    recommendations: { products: [], courses: [], experts: [], upgrades: [], shieldPlans: [], actionLinks: [] }
                });
            }

            // ── Excel / CSV → Spreadsheet parsing + Gemini Q&A ─────────────
            if (
                mime === 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' ||
                mime === 'application/vnd.ms-excel' ||
                mime === 'text/csv' ||
                mime === 'application/csv'
            ) {
                const result = await processExcel(buffer, query || '', uploadedFile.name);
                return NextResponse.json({
                    state: 'RESOLVED',
                    intent: 'KNOWLEDGE_GAP',
                    chatResponse: result.chatResponse,
                    sources: result.sources,
                    recommendations: { products: [], courses: [], experts: [], upgrades: [], shieldPlans: [], actionLinks: [] }
                });
            }

            return NextResponse.json({ message: `Unsupported file type: ${mime}` }, { status: 415 });
        }

        // ── Standard text path ─────────────────────────────────────────────
        const { query, history } = await request.json();

        if (!query) {
            return NextResponse.json(
                { message: 'Query string is required' },
                { status: 400 }
            );
        }

        const result = await EcosystemRouter(query, history || []);
        return NextResponse.json(result);

    } catch (error) {
        console.error('Error processing doubt:', error);
        return NextResponse.json(
            { message: 'Internal server error while processing doubt.' },
            { status: 500 }
        );
    }
}
