import { useState } from 'react';
import './MainLayout.css';
import SideBar from './SideBar.tsx';
import EditorPanel from './EditorPanel.tsx';

const MainLayout = () => {
  const [currentFilePath, setCurrentFilePath] = useState<string | null>(null);
  const [currentFileContent, setCurrentFileContent] = useState<string>("");

  const handleFileOpen = (filePath: string, content: string) => {
    setCurrentFilePath(filePath);
    setCurrentFileContent(content);
  };

  return (
    <div className="main-layout">
      <SideBar onFileOpen={handleFileOpen} />
      <EditorPanel filePath={currentFilePath} fileContent={currentFileContent} />
    </div>
  );
};

export default MainLayout; 