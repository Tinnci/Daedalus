import React, { useState, useRef, useEffect } from 'react';
import { Command, Child } from '@tauri-apps/plugin-shell';
import './ControlPanel.css';

interface ControlPanelProps {
    verilogFiles: string[];
}

interface LogEntry {
    type: 'cmd' | 'stdout' | 'stderr' | 'success' | 'error';
    content: string;
}

const ControlPanel: React.FC<ControlPanelProps> = ({ verilogFiles }) => {
    const [iverilogFlags, setIverilogFlags] = useState<string>('-g2012');
    const [vvpPath, setVvpPath] = useState<string>('design.vvp');
    const [vcdPath, setVcdPath] = useState<string>('wave.vcd');
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
        let childStdout = '';
        let childStderr = '';
        
        const onStdout = (line: string) => {
            childStdout += line + '\n';
            appendLog({ type: 'stdout', content: line });
        };
        const onStderr = (line: string) => {
            childStderr += line + '\n';
            appendLog({ type: 'stderr', content: line });
        };
        
        cmd.stdout.on('data', onStdout);
        cmd.stderr.on('data', onStderr);

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
        // gtkwave runs as a detached process
        appendLog({ type: 'cmd', content: `$ gtkwave ${vcdPath}` });
        const command = Command.create('gtkwave', [vcdPath]);
        command.spawn().then((child: Child) => {
             appendLog({ type: 'success', content: `GTKWave process started with PID: ${child.pid}` });
        }).catch((e: unknown) => {
            appendLog({ type: 'error', content: `Failed to launch GTKWave: ${String(e)}` });
        });
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