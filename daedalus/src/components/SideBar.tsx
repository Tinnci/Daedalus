import React, { useState } from 'react';
import './SideBar.css';
import { open as openDialog } from '@tauri-apps/plugin-dialog';
import { readTextFile } from '@tauri-apps/plugin-fs';
import ControlPanel from './ControlPanel';

interface SideBarProps {
  onFileOpen: (filePath: string, content: string) => void;
  verilogFiles: string[];
  setVerilogFiles: React.Dispatch<React.SetStateAction<string[]>>;
  iverilogFlags: string;
  setIverilogFlags: React.Dispatch<React.SetStateAction<string>>;
  vvpPath: string;
  setVvpPath: React.Dispatch<React.SetStateAction<string>>;
  vcdPath: string;
  setVcdPath: React.Dispatch<React.SetStateAction<string>>;
}

const SideBar: React.FC<SideBarProps> = ({
  onFileOpen,
  verilogFiles,
  setVerilogFiles,
  iverilogFlags,
  setIverilogFlags,
  vvpPath,
  setVvpPath,
  vcdPath,
  setVcdPath
}) => {
  const [selectedFile, setSelectedFile] = useState<string | null>(null);

  const addVerilogFiles = async () => {
    try {
      const selected = await openDialog({
        multiple: true,
        filters: [{ name: 'Verilog', extensions: ['v', 'sv'] }]
      });

      if (selected) {
        const paths = Array.isArray(selected) ? selected : [selected];
        setVerilogFiles(prevFiles => {
          const newFiles = paths.filter(file => !prevFiles.includes(file));
          return [...prevFiles, ...newFiles];
        });
      }
    } catch (error) {
      console.error("Error adding files:", error);
    }
  };

  const removeVerilogFiles = () => {
    if (selectedFile) {
      setVerilogFiles(prevFiles => prevFiles.filter(file => file !== selectedFile));
      setSelectedFile(null);
    }
  };

  const moveFile = (direction: 'up' | 'down') => {
    if (!selectedFile) return;
    const currentIndex = verilogFiles.indexOf(selectedFile);
    if (currentIndex === -1) return;
    const newIndex = direction === 'up' ? Math.max(0, currentIndex - 1) : Math.min(verilogFiles.length - 1, currentIndex + 1);
    if (newIndex !== currentIndex) {
      const newFiles = [...verilogFiles];
      const [removed] = newFiles.splice(currentIndex, 1);
      newFiles.splice(newIndex, 0, removed);
      setVerilogFiles(newFiles);
    }
  };

  const handleFileDoubleClick = async (filePath: string) => {
    try {
      const content = await readTextFile(filePath);
      onFileOpen(filePath, content);
    } catch (error) {
      console.error("Error reading file:", error);
    }
  };

  return (
    <div className="sidebar">
      <h2>Daedalus V2</h2>
      <div className="file-list-section">
        <h3>Verilog Source Files</h3>
        <div className="file-list-container">
          {verilogFiles.length === 0 ? (
            <p>No Verilog files added yet.</p>
          ) : (
            <ul className="file-list">
              {verilogFiles.map(file => (
                <li
                  key={file}
                  className={selectedFile === file ? 'selected' : ''}
                  onClick={() => setSelectedFile(file)}
                  onDoubleClick={() => handleFileDoubleClick(file)}
                >
                  {file.split(/[\\/]/).pop()}
                </li>
              ))}
            </ul>
          )}
        </div>
        <div className="file-list-buttons">
          <button onClick={addVerilogFiles}>Add File(s)</button>
          <button onClick={removeVerilogFiles} disabled={!selectedFile}>Remove Selected</button>
          <button onClick={() => moveFile('up')} disabled={!selectedFile || verilogFiles.indexOf(selectedFile) === 0}>Move Up</button>
          <button onClick={() => moveFile('down')} disabled={!selectedFile || verilogFiles.indexOf(selectedFile) === verilogFiles.length - 1}>Move Down</button>
        </div>
      </div>
      <ControlPanel
        verilogFiles={verilogFiles}
        iverilogFlags={iverilogFlags}
        setIverilogFlags={setIverilogFlags}
        vvpPath={vvpPath}
        setVvpPath={setVvpPath}
        vcdPath={vcdPath}
        setVcdPath={setVcdPath}
      />
    </div>
  );
};

export default SideBar; 