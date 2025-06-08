import React, { useEffect, useRef } from 'react';
import Editor from '@monaco-editor/react';
// import type * as monaco from 'monaco-editor'; // Removed direct import
import './EditorPanel.css';

interface EditorPanelProps {
  filePath: string | null;
  fileContent: string;
}

const EditorPanel: React.FC<EditorPanelProps> = ({ filePath, fileContent }) => {
  const editorRef = useRef<any>(null); // Changed to any for simplicity
  const monacoRef = useRef<any>(null); // Changed to any for simplicity

  // Function to handle editor mount - useful for accessing editor instance
  const handleEditorDidMount = (editor: any, monacoInstance: any) => {
    editorRef.current = editor;
    monacoRef.current = monacoInstance;
  };

  // Effect to update editor content when fileContent prop changes
  useEffect(() => {
    if (editorRef.current && monacoRef.current) {
      editorRef.current.setValue(fileContent);
      // Optionally, set language based on file extension
      if (filePath) {
        const extension = filePath.split('.').pop();
        if (extension === 'v' || extension === 'sv') {
          const model = editorRef.current.getModel();
          if (model) {
            monacoRef.current.editor.setModelLanguage(model, 'verilog');
          }
        } else {
          // Fallback to plain text or infer other languages
          const model = editorRef.current.getModel();
          if (model) {
            monacoRef.current.editor.setModelLanguage(model, 'plaintext');
          }
        }
      }
    }
  }, [fileContent, filePath]);

  return (
    <div className="editor-panel">
      <Editor
        height="100%"
        width="100%"
        language="verilog" // Set default language, can be overridden by useEffect
        value={fileContent} // Use value prop for controlled component
        theme="vs-dark"
        onMount={handleEditorDidMount}
      />
    </div>
  );
};

export default EditorPanel; 