import React, { useState, useRef, useEffect } from 'react';
import { Command, Child } from '@tauri-apps/plugin-shell';
import { invoke } from '@tauri-apps/api/core';
import './ControlPanel.css';

interface ControlPanelProps {
    verilogFiles: string[];
    iverilogFlags: string;
    setIverilogFlags: (value: string) => void;
    vvpPath: string;
    setVvpPath: (value: string) => void;
    vcdPath: string;
    setVcdPath: (value: string) => void;
}

interface LogEntry {
    type: 'cmd' | 'stdout' | 'stderr' | 'success' | 'error';
    content: string;
}

const ControlPanel: React.FC<ControlPanelProps> = ({ 
    verilogFiles,
    iverilogFlags,
    setIverilogFlags,
    vvpPath,
    setVvpPath,
    vcdPath,
    setVcdPath
}) => {
    const [log, setLog] = useState<LogEntry[]>([]);
    const logRef = useRef<HTMLDivElement>(null);

    const appendLog = (entry: LogEntry) => {
        setLog(prev => [...prev, entry]);
    };

    useEffect(() => {
        if (logRef.current) {
            logRef.current.scrollTop = logRef.current.scrollHeight;
        }
    }, [log]);

    const runCommand = async (command: string, args: string[]) => {
        appendLog({ type: 'cmd', content: `$ ${command} ${args.join(' ')}` });

        const cmd = Command.create(command, args);
        
        cmd.stdout.on('data', (line) => appendLog({ type: 'stdout', content: line }));
        cmd.stderr.on('data', (line) => appendLog({ type: 'stderr', content: line }));

        try {
            const output = await cmd.execute();
            if (output.code === 0) {
                appendLog({ type: 'success', content: `Command finished successfully.` });
            } else {
                appendLog({ type: 'error', content: `Command failed with code ${output.code}.` });
            }
            return output;
        } catch (e: any) {
            appendLog({ type: 'error', content: `Execution failed: ${e.toString()}` });
            return null;
        }
    };

    const handleCompile = async () => {
        if (verilogFiles.length === 0) {
            appendLog({ type: 'error', content: "No Verilog files to compile." });
            return;
        }
        const args = [...iverilogFlags.split(' '), '-o', vvpPath, ...verilogFiles];
        await runCommand('iverilog', args);
    };

    const handleSimulate = async () => {
        const args = [vvpPath];
        await runCommand('vvp', args);
    };

    const handleViewWave = () => {
        appendLog({ type: 'cmd', content: `$ gtkwave ${vcdPath}` });
        Command.create('gtkwave', [vcdPath])
            .spawn()
            .then((child: Child) => {
                 appendLog({ type: 'success', content: `GTKWave process started with PID: ${child.pid}` });
            }).catch((e: unknown) => {
                appendLog({ type: 'error', content: `Failed to launch GTKWave: ${String(e)}` });
            });
    };

    const handleCleanProject = async () => {
        const filesToClean = [vvpPath, vcdPath];
        appendLog({ type: 'cmd', content: `$ clean project (deleting: ${filesToClean.join(', ')})` });
        try {
            await invoke('clean_project', { paths: filesToClean });
            appendLog({ type: 'success', content: 'Clean project successful.' });
        } catch (error) {
            appendLog({ type: 'error', content: `Failed to clean project: ${error}` });
        }
    };

    return (
        <div className="control-panel">
            <h3>Simulation Control</h3>
            <div className="control-group">
                <label htmlFor="iverilog-flags">Icarus Verilog Flags:</label>
                <input id="iverilog-flags" type="text" value={iverilogFlags} onChange={e => setIverilogFlags(e.target.value)} />
            </div>
            <div className="control-group">
                <label htmlFor="vvp-path">Compiled Output (.vvp):</label>
                <input id="vvp-path" type="text" value={vvpPath} onChange={e => setVvpPath(e.target.value)} />
            </div>
            <div className="control-group">
                <label htmlFor="vcd-path">Waveform Output (.vcd):</label>
                <input id="vcd-path" type="text" value={vcdPath} onChange={e => setVcdPath(e.target.value)} />
            </div>
            <div className="button-group">
                <button onClick={handleCompile}>Compile</button>
                <button onClick={handleSimulate}>Simulate</button>
                <button onClick={handleViewWave}>View Wave</button>
                <button onClick={handleCleanProject} className="btn-danger">Clean Project</button>
            </div>
            <div className="output-log" ref={logRef}>
                {log.map((entry, index) => {
                    const className = `log-${entry.type}`;
                    return <div key={index} className={className}>{entry.content}</div>;
                })}
            </div>
        </div>
    );
};

export default ControlPanel; 