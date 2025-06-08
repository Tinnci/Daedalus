import React from 'react';
import './TabBar.css';
import { EditorFile } from '../types';

interface TabBarProps {
  openFiles: EditorFile[];
  activeFilePath: string | null;
  onTabClick: (filePath: string) => void;
  onCloseTab: (filePath: string) => void;
}

const TabBar: React.FC<TabBarProps> = ({ openFiles, activeFilePath, onTabClick, onCloseTab }) => {
  
  const handleCloseClick = (e: React.MouseEvent, filePath: string) => {
    e.stopPropagation(); // Prevent onTabClick from being triggered
    onCloseTab(filePath);
  };
  
  return (
    <div className="tab-bar">
      {openFiles.map(file => (
        <div
          key={file.path}
          className={`tab ${file.path === activeFilePath ? 'active' : ''}`}
          onClick={() => onTabClick(file.path)}
        >
          <span className="tab-name">{file.path.split(/[\\/]/).pop()}{!file.isSaved ? '*' : ''}</span>
          <button className="tab-close-btn" onClick={(e) => handleCloseClick(e, file.path)}>x</button>
        </div>
      ))}
    </div>
  );
};

export default TabBar; 