/**
 * @goose/database Stub Module
 * 
 * NOTE: This is a minimal stub for the missing internal shared package @goose/database.
 * It provides mock implementations of EcosystemRouter and multimodal document helpers
 * so that downstream apps (portal, goose-digital, goose-elevate) compile cleanly
 * without requiring the unbundled private database package.
 */

export interface EcosystemResponse {
  state: string;
  intent: string;
  chatResponse: string;
  sources: Array<{ document_name: string; section?: string; page_number?: number }>;
  componentName?: string;
  recommendations: {
    products: Array<{ id: string | number; name: string; modelNumber?: string; category?: string }>;
    courses: Array<{ id: string | number; title: string }>;
    experts: Array<{ id: string | number; name: string }>;
    upgrades: any[];
    shieldPlans: any[];
    actionLinks: any[];
  };
}

export async function EcosystemRouter(query: string, history: any[] = []): Promise<EcosystemResponse> {
  return {
    state: 'RESOLVED',
    intent: 'GENERAL_QA',
    chatResponse: `[Stub] Processed query: "${query}". Real AI routing is handled by sense-api on port 8001.`,
    sources: [],
    recommendations: {
      products: [],
      courses: [],
      experts: [],
      upgrades: [],
      shieldPlans: [],
      actionLinks: [],
    },
  };
}

export async function processImage(base64Data: string, mimeType: string) {
  return {
    chatResponse: 'Image processed (stubbed). Connect to sense-api /upload-document for live vision processing.',
    sources: [],
    componentName: 'Inspected Industrial Part',
  };
}

export async function processPDF(buffer: Buffer, query: string) {
  return {
    chatResponse: 'PDF processed (stubbed). Connect to sense-api /upload-document for full text extraction.',
    sources: [],
  };
}

export async function processExcel(buffer: Buffer, query: string, filename?: string) {
  return {
    chatResponse: `Spreadsheet ${filename || ''} processed (stubbed).`,
    sources: [],
  };
}
