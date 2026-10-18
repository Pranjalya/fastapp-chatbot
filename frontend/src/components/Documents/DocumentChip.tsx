import React from 'react';
import { FileText, Database, X } from 'lucide-react';
import type { DocumentItem } from '../../types/chat';

interface Props {
  doc: DocumentItem;
  onRemove?: (id: string) => void;
}

export const DocumentChip: React.FC<Props> = ({ doc, onRemove }) => {
  const isDirect = doc.strategy === 'DIRECT_CONTEXT';

  const formatSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  return (
    <div
      className={`doc-chip ${isDirect ? 'direct' : 'tool'}`}
      title={doc.summary_or_toc || doc.filename}
      id={`doc-chip-${doc.id}`}
    >
      {isDirect ? <FileText size={13} /> : <Database size={13} />}
      <span style={{ maxWidth: '140px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
        {doc.filename}
      </span>
      <span style={{ opacity: 0.7, fontSize: '0.72rem' }}>
        ({isDirect ? 'Direct' : 'Indexed'} · {formatSize(doc.size_bytes)})
      </span>
      {onRemove && (
        <button
          className="doc-chip-remove"
          onClick={() => onRemove(doc.id)}
          aria-label={`Remove ${doc.filename}`}
        >
          <X size={13} />
        </button>
      )}
    </div>
  );
};
