import React, { useEffect, useRef } from 'react';
import Editor from '@monaco-editor/react';
// import type * as monaco from 'monaco-editor'; // Removed direct import
import './EditorPanel.css';

interface EditorPanelProps {
  filePath: string | null;
  fileContent: string;
  onContentChange: (filePath: string, newContent: string) => void;
}

const EditorPanel: React.FC<EditorPanelProps> = ({ filePath, fileContent, onContentChange }) => {
  const editorRef = useRef<any>(null); // Changed to any for simplicity
  const monacoRef = useRef<any>(null); // Changed to any for simplicity

  // Function to handle editor mount - useful for accessing editor instance
  const handleEditorDidMount = (editor: any, monacoInstance: any) => {
    editorRef.current = editor;
    monacoRef.current = monacoInstance;
  };

  const handleEditorChange = (value: string | undefined) => {
    if (filePath && typeof value === 'string') {
      onContentChange(filePath, value);
    }
  };

  // Effect to update editor content when fileContent prop changes
  useEffect(() => {
    if (editorRef.current) {
        if(editorRef.current.getValue() !== fileContent) {
            editorRef.current.setValue(fileContent);
        }
    }
    // ... logic to set language based on filePath ...
    if (editorRef.current && monacoRef.current && filePath) {
        const extension = filePath.split('.').pop();
        const model = editorRef.current.getModel();
        if (model) {
            if (extension === 'v' || extension === 'sv') {
                monacoRef.current.editor.setModelLanguage(model, 'verilog');
            } else {
                monacoRef.current.editor.setModelLanguage(model, 'plaintext');
            }
        }
    }
  }, [fileContent, filePath]);

  if (filePath === null) {
    return (
        <div className="editor-panel-placeholder">
            <p>No file selected</p>
            <p>Double-click a file in the sidebar to open it.</p>
        </div>
    );
  }

  return (
    <div className="editor-panel">
      <Editor
        height="100%"
        width="100%"
        key={filePath} // Use key to force re-mount when file path changes
        defaultValue={fileContent}
        language="verilog"
        theme="vs-dark"
        onMount={handleEditorDidMount}
        onChange={handleEditorChange}
      />
    </div>
  );
};

export default EditorPanel; 