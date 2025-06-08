import React, { useState } from 'react';
import './SideBar.css';
import { open as openDialog } from '@tauri-apps/plugin-dialog';
import { readTextFile, BaseDirectory } from '@tauri-apps/plugin-fs';

interface SideBarProps {
  onFileOpen: (filePath: string, content: string) => void;
}

const SideBar: React.FC<SideBarProps> = ({ onFileOpen }) => {
  const [verilogFiles, setVerilogFiles] = useState<string[]>([]);
  const [selectedFile, setSelectedFile] = useState<string | null>(null);

  const addVerilogFiles = async () => {
    try {
      const selected = await openDialog({
        multiple: true,
        filters: [{
          name: 'Verilog',
          extensions: ['v', 'sv']
        }]
      });

      if (Array.isArray(selected)) {
        // Filter out files already present to avoid duplicates
        const newFiles = selected.filter(file => !verilogFiles.includes(file));
        setVerilogFiles(prevFiles => [...prevFiles, ...newFiles]);
      } else if (selected) {
        // Handle single file selection if multiple is false (though we set it to true)
        if (!verilogFiles.includes(selected)) {
          setVerilogFiles(prevFiles => [...prevFiles, selected]);
        }
      }
    } catch (error) {
      console.error("Error adding files:", error);
    }
  };

  const removeVerilogFiles = () => {
    if (selectedFile) {
      setVerilogFiles(prevFiles => prevFiles.filter(file => file !== selectedFile));
      setSelectedFile(null); // Deselect after removal
    }
  };

  const moveFile = (direction: 'up' | 'down') => {
    if (!selectedFile) return;

    const currentIndex = verilogFiles.indexOf(selectedFile);
    if (currentIndex === -1) return;

    let newIndex = currentIndex;
    if (direction === 'up') {
      newIndex = Math.max(0, currentIndex - 1);
    } else {
      newIndex = Math.min(verilogFiles.length - 1, currentIndex + 1);
    }

    if (newIndex !== currentIndex) {
      const newFiles = [...verilogFiles];
      const [removed] = newFiles.splice(currentIndex, 1);
      newFiles.splice(newIndex, 0, removed);
      setVerilogFiles(newFiles);
    }
  };

  const handleFileDoubleClick = async (filePath: string) => {
    try {
      const content = await readTextFile(filePath, { baseDir: BaseDirectory.Home }); // Assuming files are in Home for now, will refine later
      onFileOpen(filePath, content);
    } catch (error) {
      console.error("Error reading file:", error);
      // You might want to show a user-friendly error message here
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
                  {file.split('/').pop()} {/* Display only basename */}
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
      {/* We will add the hierarchy tree here later */}
    </div>
  );
};

export default SideBar; 