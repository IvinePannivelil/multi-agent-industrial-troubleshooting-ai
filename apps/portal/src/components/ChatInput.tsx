import { Send } from "lucide-react";
import { useState } from "react";
import FileUpload, { AttachedFile } from "./FileUpload";

interface ChatInputProps {
  onSend: (message: string, file: AttachedFile | null) => void;
  isLoading: boolean;
}

export default function ChatInput({ onSend, isLoading }: ChatInputProps) {
  const [input, setInput] = useState("");
  const [attachedFile, setAttachedFile] = useState<AttachedFile | null>(null);

  const handleFileSelect = (file: File) => {
    let previewUrl;
    if (file.type.startsWith("image/")) {
      previewUrl = URL.createObjectURL(file);
    }
    setAttachedFile({ file, previewUrl });
  };

  const handleClearFile = () => {
    if (attachedFile?.previewUrl) {
      URL.revokeObjectURL(attachedFile.previewUrl);
    }
    setAttachedFile(null);
  };

  const handleSubmit = (e?: React.FormEvent) => {
    e?.preventDefault();
    const trimmed = input.trim();
    if ((!trimmed && !attachedFile) || isLoading) return;
    
    onSend(trimmed, attachedFile);
    setInput("");
    setAttachedFile(null);
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  return (
    <div className="flex flex-col gap-2">
      {/* Show preview above input if file attached - optional alternate layout */}
      <form
        onSubmit={handleSubmit}
        className="flex w-full items-end gap-2 bg-white p-2.5 rounded-xl border border-gray-200 shadow-sm transition-shadow focus-within:shadow-md focus-within:ring-1 focus-within:ring-blue-100"
      >
        <FileUpload
          onFileSelect={handleFileSelect}
          attachedFile={attachedFile}
          onClearFile={handleClearFile}
          disabled={isLoading}
        />
        
        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask Industrial Assistant..."
          className="max-h-32 min-h-[44px] w-full resize-none bg-transparent py-2.5 px-2 focus:outline-none text-sm placeholder:text-gray-400"
          rows={1}
          disabled={isLoading}
        />
        
        <button
          type="submit"
          disabled={(!input.trim() && !attachedFile) || isLoading}
          className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-blue-600 text-white transition-colors hover:bg-blue-700 disabled:opacity-50 disabled:hover:bg-blue-600"
        >
          <Send className="h-4 w-4" />
        </button>
      </form>
    </div>
  );
}
