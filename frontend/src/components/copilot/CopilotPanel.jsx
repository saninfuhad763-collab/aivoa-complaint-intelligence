import React, { useState } from 'react';
import MessageList from './MessageList.jsx';
import CopilotInput from './CopilotInput.jsx';
import DocumentUpload from '../documents/DocumentUpload.jsx';

export default function CopilotPanel() {
  const [file, setFile] = useState(null);

  return (
    <div className="panel panel-right">
      {/* Panel header */}
      <div className="panel-header">
        <span className="panel-title">AI Copilot</span>
        <span className="panel-badge badge-ai">AI</span>
      </div>

      {/* Copilot inner */}
      <div className="copilot-panel">
        {/* Message area */}
        <MessageList />

        {/* Document upload */}
        <DocumentUpload file={file} onFileChange={setFile} />

        {/* Input area */}
        <CopilotInput />
      </div>
    </div>
  );
}
