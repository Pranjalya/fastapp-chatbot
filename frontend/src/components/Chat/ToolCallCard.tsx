import React, { useState } from 'react';
import { ChevronDown, ChevronRight, FileSearch } from 'lucide-react';

interface Props {
  tool: string;
  input?: any;
  outputPreview?: string;
}

export const ToolCallCard: React.FC<Props> = ({ tool, input, outputPreview }) => {
  const [expanded, setExpanded] = useState(false);

  const formatToolName = (name: string) => {
    switch (name) {
      case 'search_document': return 'Searching Attached Document';
      case 'read_document_page': return 'Reading Specific Document Page';
      case 'inspect_document_outline': return 'Inspecting Document Structure';
      default: return `Executed Tool: ${name}`;
    }
  };

  return (
    <div className="tool-card">
      <div
        className="tool-card-header"
        style={{ cursor: 'pointer', display: 'flex', justifyContent: 'space-between' }}
        onClick={() => setExpanded(!expanded)}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <FileSearch size={15} />
          <span>{formatToolName(tool)}</span>
        </div>
        {expanded ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
      </div>

      {expanded && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', marginTop: '4px' }}>
          {input && (
            <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>
              <strong>Input:</strong> {JSON.stringify(input)}
            </div>
          )}
          {outputPreview && (
            <div className="tool-preview">
              {outputPreview}
            </div>
          )}
        </div>
      )}
    </div>
  );
};
