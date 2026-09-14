import { Paperclip, X, FileText, Image as ImageIcon } from "lucide-react";
import { useRef } from "react";

export interface AttachedFile {
  file: File;
  previewUrl?: string;
}

interface FileUploadProps {
  onFileSelect: (file: File) => void;
  attachedFile: AttachedFile | null;
  onClearFile: () => void;
  disabled: boolean;
}

export default function FileUpload({ onFileSelect, attachedFile, onClearFile, disabled }: FileUploadProps) {
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      onFileSelect(file);
    }
    // Reset input so the same file can be selected again if cleared
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  const isImage = attachedFile?.file.type.startsWith("image/");

  return (
    <div className="flex items-center">
      <input
        type="file"
        ref={fileInputRef}
        onChange={handleFileChange}
        className="hidden"
        disabled={disabled}
        accept=".pdf,.doc,.docx,.xls,.xlsx,.csv,image/*"
      />
      
      {!attachedFile && (
        <button
          type="button"
          onClick={() => fileInputRef.current?.click()}
          disabled={disabled}
          className="flex h-10 w-10 items-center justify-center rounded-full text-gray-400 hover:bg-gray-100 hover:text-gray-600 disabled:opacity-50"
          title="Attach file"
        >
          <Paperclip className="h-5 w-5" />
        </button>
      )}

      {/* Preview Chip */}
      {attachedFile && (
        <div className="relative flex items-center gap-2 rounded-lg border border-blue-200 bg-blue-50 px-3 py-1.5 text-sm text-blue-800 shadow-sm transition-all overflow-hidden max-w-[200px]">
           {isImage ? (
             <ImageIcon className="h-4 w-4 shrink-0 text-blue-500" />
           ) : (
             <FileText className="h-4 w-4 shrink-0 text-blue-500" />
           )}
          <span className="truncate font-medium text-xs">
            {attachedFile.file.name}
          </span>
          <button
            type="button"
            onClick={onClearFile}
            disabled={disabled}
            className="ml-1 rounded-full p-0.5 text-blue-500 hover:bg-blue-200 hover:text-blue-700"
          >
            <X className="h-3.5 w-3.5" />
          </button>
        </div>
      )}
    </div>
  );
}
