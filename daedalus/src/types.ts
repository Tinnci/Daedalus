export interface EditorFile {
  path: string;
  content: string;
  isSaved: boolean;
}

export interface DependencyStatus {
  iverilog: boolean;
  vvp: boolean;
  gtkwave: boolean;
}

export interface ProjectSettings {
  iverilogFlags: string;
  vvpPath: string;
  vcdPath: string;
  verilogFiles: string[];
  openFiles: EditorFile[];
  activeFilePath: string | null;
} 