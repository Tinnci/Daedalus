import { useState, useEffect } from 'react';
import './MainLayout.css';
import SideBar from './SideBar';
import EditorPanel from './EditorPanel';
import TabBar from './TabBar';
import { EditorFile } from '../types';
import { writeTextFile } from '@tauri-apps/plugin-fs';

const MainLayout = () => {
  const [openFiles, setOpenFiles] = useState<EditorFile[]>([]);
  const [activeFilePath, setActiveFilePath] = useState<string | null>(null);

  const activeFile = openFiles.find(file => file.path === activeFilePath) || null;

  const handleFileOpen = (filePath: string, content: string) => {
    const fileExists = openFiles.some(file => file.path === filePath);
    if (!fileExists) {
      const newFile: EditorFile = { path: filePath, content, isSaved: true };
      setOpenFiles(prevFiles => [...prevFiles, newFile]);
    }
    setActiveFilePath(filePath);
  };
  
  const handleTabClick = (filePath: string) => {
    setActiveFilePath(filePath);
  };

  const handleCloseTab = (filePath: string) => {
    //
    setOpenFiles(prevFiles => {
      const newFiles = prevFiles.filter(file => file.path !== filePath);
      if (activeFilePath === filePath) {
        setActiveFilePath(newFiles.length > 0 ? newFiles[0].path : null);
      }
      return newFiles;
    });
  };

  const handleContentChange = (filePath: string, newContent: string) => {
    setOpenFiles(prevFiles =>
      prevFiles.map(file =>
        file.path === filePath ? { ...file, content: newContent, isSaved: false } : file
      )
    );
  };

  const handleSave = async () => {
    if (!activeFile || activeFile.isSaved) return;

    try {
        await writeTextFile(activeFile.path, activeFile.content);
        setOpenFiles(prevFiles =>
            prevFiles.map(file =>
                file.path === activeFile.path ? { ...file, isSaved: true } : file
            )
        );
        console.log(`File saved: ${activeFile.path}`);
    } catch (error) {
        console.error("Error saving file:", error);
    }
  };

  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.ctrlKey && event.key === 's') {
        event.preventDefault();
        handleSave();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => {
      window.removeEventListener('keydown', handleKeyDown);
    };
  }, [activeFile]);


  return (
    <div className="main-layout">
      <SideBar onFileOpen={handleFileOpen} />
      <div className="editor-section">
        <TabBar 
            openFiles={openFiles} 
            activeFilePath={activeFilePath} 
            onTabClick={handleTabClick}
            onCloseTab={handleCloseTab}
        />
        <EditorPanel 
            key={activeFilePath}
            filePath={activeFilePath} 
            fileContent={activeFile?.content ?? ''}
            onContentChange={handleContentChange}
        />
      </div>
    </div>
  );
};

export default MainLayout; 