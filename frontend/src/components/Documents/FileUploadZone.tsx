import React, { useRef, useState } from 'react';
import { Paperclip, Loader2 } from 'lucide-react';
import { api } from '../../services/api';
import type { DocumentItem } from '../../types/chat';

interface Props {
  threadId: string;
  onDocumentUploaded: (doc: DocumentItem) => void;
  onError: (err: string) => void;
}

export const FileUploadZone: React.FC<Props> = ({ threadId, onDocumentUploaded, onError }) => {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [uploading, setUploading] = useState(false);

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (!files || files.length === 0) return;

    setUploading(true);
    for (let i = 0; i < files.length; i++) {
      const file = files[i];
      try {
        const uploadedDoc = await api.uploadDocument(threadId, file);
        onDocumentUploaded(uploadedDoc);
      } catch (err: any) {
        onError(err.message || `Failed to upload ${file.name}`);
      }
    }
    setUploading(false);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  return (
    <>
      <input
        ref={fileInputRef}
        type="file"
        multiple
        style={{ display: 'none' }}
        onChange={handleFileChange}
        accept=".pdf,.docx,.doc,.txt,.csv,.tsv,.xlsx,.xls,.json,.md,.py,.js,.ts,.html,.css,.yaml,.yml"
        id="file-upload-input"
      />
      <button
        type="button"
        className="icon-btn"
        title="Attach document (PDF, DOCX, TXT, CSV, Code)"
        onClick={() => fileInputRef.current?.click()}
        disabled={uploading}
        id="btn-attach-file"
      >
        {uploading ? <Loader2 size={18} className="spin-animation" /> : <Paperclip size={18} />}
      </button>
    </>
  );
};
