import { useState, useEffect } from 'react';
import './MainLayout.css';
import SideBar from './SideBar';
import EditorPanel from './EditorPanel';
import TabBar from './TabBar';
import { EditorFile, DependencyStatus, ProjectSettings } from '../types';
import { writeTextFile, readTextFile } from '@tauri-apps/plugin-fs';
import { open as openDialog, save as saveDialog } from '@tauri-apps/plugin-dialog';
import { invoke } from '@tauri-apps/api/core';

const MainLayout = () => {
  const [openFiles, setOpenFiles] = useState<EditorFile[]>([]);
  const [activeFilePath, setActiveFilePath] = useState<string | null>(null);
  const [dependencyStatus, setDependencyStatus] = useState<DependencyStatus | null>(null);

  // Lifted state
  const [verilogFiles, setVerilogFiles] = useState<string[]>([]);
  const [iverilogFlags, setIverilogFlags] = useState<string>('-g2012');
  const [vvpPath, setVvpPath] = useState<string>('design.vvp');
  const [vcdPath, setVcdPath] = useState<string>('wave.vcd');

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

  const saveProject = async () => {
    try {
        const filePath = await saveDialog({
            filters: [{ name: 'JSON', extensions: ['json'] }]
        });
        if (filePath) {
            const projectData: ProjectSettings = {
                verilogFiles,
                iverilogFlags,
                vvpPath,
                vcdPath,
                openFiles,
                activeFilePath,
            };
            await writeTextFile(filePath, JSON.stringify(projectData, null, 2));
            console.log(`Project saved to ${filePath}`);
        }
    } catch (error) {
        console.error("Error saving project:", error);
    }
  };

  const openProject = async () => {
    try {
        const selected = await openDialog({
            multiple: false,
            filters: [{ name: 'JSON', extensions: ['json'] }]
        });
        if (selected) {
            const content = await readTextFile(selected);
            const projectData: ProjectSettings = JSON.parse(content);

            setVerilogFiles(projectData.verilogFiles || []);
            setIverilogFlags(projectData.iverilogFlags || '-g2012');
            setVvpPath(projectData.vvpPath || 'design.vvp');
            setVcdPath(projectData.vcdPath || 'wave.vcd');
            setOpenFiles(projectData.openFiles || []);
            setActiveFilePath(projectData.activeFilePath || null);

            console.log(`Project loaded from ${selected}`);
        }
    } catch (error) {
        console.error("Error opening project:", error);
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

  useEffect(() => {
    const checkDeps = async () => {
      try {
        const result = await invoke<DependencyStatus>('check_dependencies');
        setDependencyStatus(result);
      } catch (error) {
        console.error("Failed to check dependencies:", error);
      }
    };
    checkDeps();
  }, []);

  const missingDependencies = dependencyStatus
    ? Object.entries(dependencyStatus)
        .filter(([, found]) => !found)
        .map(([name]) => name)
    : [];

  return (
    <div className="main-layout">
      {missingDependencies.length > 0 && (
        <div className="dependency-warning">
          Warning: The following required tools are not found in your system's PATH: {missingDependencies.join(', ')}. Please install them and restart the application.
        </div>
      )}
       <div style={{ position: 'absolute', top: '40px', right: '10px', zIndex: 1000}}>
          <button onClick={saveProject}>Save Project</button>
          <button onClick={openProject}>Open Project</button>
        </div>
      <SideBar 
        onFileOpen={handleFileOpen}
        verilogFiles={verilogFiles}
        setVerilogFiles={setVerilogFiles}
        iverilogFlags={iverilogFlags}
        setIverilogFlags={setIverilogFlags}
        vvpPath={vvpPath}
        setVvpPath={setVvpPath}
        vcdPath={vcdPath}
        setVcdPath={setVcdPath}
      />
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