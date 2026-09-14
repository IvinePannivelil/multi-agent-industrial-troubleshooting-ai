import { ChevronDown, ChevronUp, FileText } from "lucide-react";
import { useState } from "react";

export interface Source {
  document_name: string;
  section: string;
  page_number: number;
}

interface SourcesAccordionProps {
  sources: Source[];
}

export default function SourcesAccordion({ sources }: SourcesAccordionProps) {
  const [isOpen, setIsOpen] = useState(false);

  if (!sources || sources.length === 0) return null;

  return (
    <div className="mt-4 overflow-hidden rounded-lg border border-gray-200 bg-gray-50 text-sm">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex w-full items-center justify-between px-4 py-2 text-gray-700 hover:bg-gray-100 transition-colors"
      >
        <div className="flex items-center gap-2 font-medium">
          <FileText className="h-4 w-4 text-blue-500" />
          Sources ({sources.length})
        </div>
        {isOpen ? (
          <ChevronUp className="h-4 w-4" />
        ) : (
          <ChevronDown className="h-4 w-4" />
        )}
      </button>

      {isOpen && (
        <div className="flex flex-col gap-2 border-t border-gray-200 p-3 bg-white">
          {sources.map((source, index) => (
            <div key={index} className="flex flex-col rounded-md bg-gray-50 p-2 text-xs text-gray-600">
              <span className="font-semibold text-gray-900">{source.document_name}</span>
              {source.section && <span>Section: {source.section}</span>}
              {source.page_number > 0 && <span>Page: {source.page_number}</span>}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
