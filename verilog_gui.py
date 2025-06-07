import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
from tkinter import ttk # Import ttk module
import shutil
import subprocess
import os
import json
import shlex # Import shlex for safe command string splitting

# For syntax highlighting
from pygments import highlight
from pygments.lexers import VerilogLexer
from pygments.formatters import TerminalFormatter # We will use this to get style info
from pygments.token import Token

class VerilogGUI:
    def __init__(self, master):
        self.master = master
        master.title("Verilog GUI Wrapper")
        # master.geometry("800x600") # Removed fixed geometry

        self.tool_paths = {}
        self.verilog_files = []
        self.project_path = ""
        self.config_file_path = "config.json"

        # Load window state on startup
        self.load_window_state()

        # Set protocol for window closing
        self.master.protocol("WM_DELETE_WINDOW", self.on_closing)

        # Initialize Notebook and main console tab (Moved before create_widgets)
        self.notebook = ttk.Notebook(self.master)
        self.notebook.pack(expand=True, fill="both", padx=5, pady=5)

        self.console_frame = ttk.Frame(self.notebook) # This will hold all existing widgets
        self.notebook.add(self.console_frame, text="控制台")

        # Dictionary to keep track of opened editor tabs: {file_path: scrolledtext_widget}
        self.open_editors = {}

        # --- GUI Elements ---
        self.create_widgets()

        # Define Pygments token type to Tkinter tag name and color mapping
        # These tags will be configured on each editor's ScrolledText widget
        self.pygments_tag_styles = {
            Token.Keyword: {"tag": "keyword", "foreground": "blue"},
            Token.Comment: {"tag": "comment", "foreground": "green"},
            Token.String: {"tag": "string", "foreground": "#a31515"}, # Dark red for strings
            Token.Literal.Number: {"tag": "number", "foreground": "#000080"}, # Navy for numbers
            Token.Name.Builtin: {"tag": "builtin", "foreground": "#800080"}, # Purple for built-ins
            Token.Operator: {"tag": "operator", "foreground": "#808000"}, # Olive for operators
            Token.Punctuation: {"tag": "punctuation", "foreground": "#808080"}, # Grey for punctuation
            Token.Name.Other: {"tag": "plain", "foreground": "black"}, # Default text color
            Token.Error: {"tag": "error", "foreground": "white", "background": "red"}, # Error style
            # Add more specific tokens as needed for Verilog
            Token.Name.Variable: {"tag": "variable", "foreground": "#008080"}, # Teal for variables
            Token.Name.Function: {"tag": "function", "foreground": "#CC0000"}, # Darker red for functions
            Token.Name.Class: {"tag": "class", "foreground": "#0000FF"}, # Blue for classes
            Token.Text: {"tag": "text", "foreground": "black"}, # Fallback for plain text
        }

        # --- Environment Check on startup ---
        self.check_dependencies()

    def create_widgets(self):
        # Frame for file selection
        file_frame = ttk.LabelFrame(self.console_frame, text="Verilog Source Files")
        file_frame.pack(fill="x")

        # Use Treeview for file list
        self.file_listbox = ttk.Treeview(file_frame, columns=("Filename"), show="headings", height=5)
        self.file_listbox.heading("Filename", text="Filename")
        self.file_listbox.pack(side=tk.LEFT, fill="both", expand=True)
        
        # Bind double-click event to open file in editor
        self.file_listbox.bind("<Double-1>", self.open_file_in_editor)
        
        scrollbar = ttk.Scrollbar(self.file_listbox, orient="vertical", command=self.file_listbox.yview)
        self.file_listbox.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill="y")

        btn_frame_files = ttk.Frame(file_frame)
        btn_frame_files.pack(side=tk.RIGHT, padx=5)
        
        self.add_file_btn = ttk.Button(btn_frame_files, text="Add File(s)", command=self.add_verilog_files)
        self.add_file_btn.pack(fill="x", pady=2)

        self.remove_file_btn = ttk.Button(btn_frame_files, text="Remove Selected", command=self.remove_verilog_files)
        self.remove_file_btn.pack(fill="x", pady=2)

        self.move_up_btn = ttk.Button(btn_frame_files, text="Move Up", command=self.move_file_up)
        self.move_up_btn.pack(fill="x", pady=2)

        self.move_down_btn = ttk.Button(btn_frame_files, text="Move Down", command=self.move_file_down)
        self.move_down_btn.pack(fill="x", pady=2)

        # Frame for output settings
        output_frame = ttk.LabelFrame(self.console_frame, text="Output Settings")
        output_frame.pack(fill="x")

        ttk.Label(output_frame, text="Compiled Output (.vvp):").grid(row=0, column=0, sticky="w", pady=2)
        self.vvp_output_entry = ttk.Entry(output_frame, width=40)
        self.vvp_output_entry.insert(0, "design.vvp")
        self.vvp_output_entry.grid(row=0, column=1, sticky="ew", pady=2)

        ttk.Label(output_frame, text="Waveform Output (.vcd):").grid(row=1, column=0, sticky="w", pady=2)
        self.vcd_output_entry = ttk.Entry(output_frame, width=40)
        self.vcd_output_entry.insert(0, "wave.vcd")
        self.vcd_output_entry.grid(row=1, column=1, sticky="ew", pady=2)

        ttk.Label(output_frame, text="GTKWave Save File (.gtkw):").grid(row=2, column=0, sticky="w", pady=2)
        self.gtkw_file_entry = ttk.Entry(output_frame, width=40)
        self.gtkw_file_entry.insert(0, "wave.gtkw")
        self.gtkw_file_entry.grid(row=2, column=1, sticky="ew", pady=2)
        output_frame.grid_columnconfigure(1, weight=1)

        # Frame for command buttons
        cmd_frame = ttk.Frame(self.console_frame)
        cmd_frame.pack(fill="x")

        self.compile_btn = ttk.Button(cmd_frame, text="Compile (iverilog)", command=self.compile_verilog)
        self.compile_btn.pack(side=tk.LEFT, expand=True, fill="x", padx=5)

        self.simulate_btn = ttk.Button(cmd_frame, text="Simulate (vvp)", command=self.simulate_verilog)
        self.simulate_btn.pack(side=tk.LEFT, expand=True, fill="x", padx=5)

        self.view_wave_btn = ttk.Button(cmd_frame, text="View Wave (GTKWave)", command=self.view_waveform)
        self.view_wave_btn.pack(side=tk.LEFT, expand=True, fill="x", padx=5)

        self.clean_btn = ttk.Button(cmd_frame, text="Clean Project", command=self.clean_project)
        self.clean_btn.pack(side=tk.LEFT, expand=True, fill="x", padx=5)

        # Frame for Advanced Options
        adv_frame = ttk.LabelFrame(self.console_frame, text="Advanced Options")
        adv_frame.pack(fill="x", padx=10, pady=5)

        ttk.Label(adv_frame, text="Icarus Verilog Flags:").pack(side=tk.LEFT, padx=5)
        self.iverilog_flags_entry = ttk.Entry(adv_frame)
        self.iverilog_flags_entry.pack(side=tk.LEFT, fill="x", expand=True, padx=5)

        # Frame for information output
        log_frame = ttk.LabelFrame(self.console_frame, text="Command Output & Log")
        log_frame.pack(fill="both", expand=True)

        self.output_log_widget = scrolledtext.ScrolledText(log_frame, wrap=tk.WORD, height=15)
        self.output_log_widget.pack(fill="both", expand=True)

        # Configure tags for log highlighting
        self.output_log_widget.tag_config("ERROR", foreground="red")
        self.output_log_widget.tag_config("WARNING", foreground="orange")
        self.output_log_widget.tag_config("CMD", foreground="blue")

        # Menu Bar for project management
        menubar = tk.Menu(self.master)
        self.master.config(menu=menubar)

        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Open Project...", command=self.open_project)
        file_menu.add_command(label="Save", command=self.save_current_file)
        file_menu.add_command(label="Save Project As...", command=self.save_project_as)
        file_menu.add_command(label="Close Current Tab", command=self.close_current_tab)
        file_menu.add_separator()
        file_menu.add_command(label="New Project", command=self.new_project)
        file_menu.add_command(label="Exit", command=self.master.quit)

        edit_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Edit", menu=edit_menu)
        edit_menu.add_command(label="Find...", command=self.find_text)
        edit_menu.add_command(label="Replace...", command=self.replace_text)

        # Menu for Code Templates
        template_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Templates", menu=template_menu)
        template_menu.add_command(label="New Module", command=lambda: self.insert_template("new_module"))
        template_menu.add_command(label="New Testbench", command=lambda: self.insert_template("new_testbench"))
        template_menu.add_command(label="always @(posedge clk) block", command=lambda: self.insert_template("always_posedge_clk"))

    def check_dependencies(self):
        """检查iverilog, vvp, gtkwave是否存在于PATH中"""
        dependencies = {
            "Icarus Verilog (iverilog)": "iverilog",
            "Icarus Verilog VVP": "vvp",
            "GTKWave": "gtkwave"
        }
        
        missing = []
        found_paths = {}
        
        for name, cmd in dependencies.items():
            path = shutil.which(cmd) # 在系统PATH中查找命令
            if path:
                self.output_log_widget.insert(tk.END, f"找到 {name} at: {path}\n")
                found_paths[cmd] = path
            else:
                missing.append(name)
                
        if missing:
            messagebox.showerror(
                "依赖缺失",
                "以下必要的工具未找到或未添加到系统环境变量中:\n\n" + "\n".join(missing) + "\n\n请安装并配置好这些工具，然后重启程序。"
            )
            self.output_log_widget.insert(tk.END, "\n--- 依赖缺失，部分功能可能无法使用 ---\n")
            # Disable buttons if dependencies are missing
            self.compile_btn.config(state=tk.DISABLED)
            self.simulate_btn.config(state=tk.DISABLED)
            self.view_wave_btn.config(state=tk.DISABLED)
            return None
        
        messagebox.showinfo("环境检查成功", "所有依赖工具均已找到！")
        self.output_log_widget.insert(tk.END, "\n--- 环境检查成功，所有依赖工具均已找到！ ---\n")
        self.tool_paths = found_paths
        # Enable buttons if dependencies are found
        self.compile_btn.config(state=tk.NORMAL)
        self.simulate_btn.config(state=tk.NORMAL)
        self.view_wave_btn.config(state=tk.NORMAL)
        return found_paths

    def run_command(self, command_list):
        """执行一个命令并将其输出实时显示在GUI的文本框中"""
        self.output_log_widget.delete('1.0', tk.END) # 清空上次的输出
        self.output_log_widget.insert(tk.END, f"正在执行命令: {' '.join(command_list)}\n\n", "CMD") # Tag the command line as CMD
        self.output_log_widget.update()

        try:
            # Popen允许我们非阻塞地读取输出
            process = subprocess.Popen(
                command_list,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT, # 将错误输出重定向到标准输出
                text=True,
                encoding='utf-8',
                # Windows下不显示控制台窗口
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )
            
            # 实时读取输出并插入到文本框
            while True:
                line = process.stdout.readline()
                if not line:
                    break

                # Simple check for keywords and apply tags
                if "error" in line.lower():
                    self.output_log_widget.insert(tk.END, line, "ERROR")
                elif "warning" in line.lower():
                    self.output_log_widget.insert(tk.END, line, "WARNING")
                else:
                    self.output_log_widget.insert(tk.END, line)

                self.output_log_widget.see(tk.END) # 滚动到底部
                self.output_log_widget.update_idletasks() # Use update_idletasks for better responsiveness
                
            process.wait() # 等待进程结束
            
            if process.returncode == 0:
                self.output_log_widget.insert(tk.END, "\n--- 命令执行成功 ---\n")
                return True
            else:
                self.output_log_widget.insert(tk.END, f"\n--- 命令执行失败 (返回代码: {process.returncode}) ---\n")
                return False

        except FileNotFoundError:
            self.output_log_widget.insert(tk.END, f"错误: 命令 '{command_list[0]}' 未找到。请确保它已安装并位于系统PATH中。\n")
            return False
        except Exception as e:
            self.output_log_widget.insert(tk.END, f"发生未知错误: {e}\n")
            return False

    def launch_gtkwave(self, gtkwave_path, vcd_file_path):
        """启动GTKWave来查看VCD文件"""
        if not os.path.exists(vcd_file_path):
            self.output_log_widget.insert(tk.END, f"\n错误: VCD文件 '{vcd_file_path}' 不存在。请先进行仿真。\n")
            return

        gtkw_file_path = self.gtkw_file_entry.get()
        command = [gtkwave_path, vcd_file_path]

        # 如果用户指定了 .gtkw 文件并且它存在，就添加到命令中
        if gtkw_file_path and os.path.exists(gtkw_file_path):
            self.output_log_widget.insert(tk.END, f"找到 GTKWave 配置文件: {gtkw_file_path}\n")
            command.append(gtkw_file_path)
        else:
            self.output_log_widget.insert(tk.END, "未找到 GTKWave 配置文件，将使用默认视图。\n")

        self.output_log_widget.insert(tk.END, f"\n正在启动 GTKWave 加载 {vcd_file_path}...\n")
        try:
            # 使用Popen启动一个独立的进程，我们的GUI不用等它
            subprocess.Popen(command,
                             creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
        except FileNotFoundError:
            self.output_log_widget.insert(tk.END, f"\n错误: GTKWave 未在 '{gtkwave_path}' 找到。\n")
        except Exception as e:
            self.output_log_widget.insert(tk.END, f"\n启动 GTKWave 失败: {e}\n")

    def clean_project(self):
        self.output_log_widget.delete('1.0', tk.END) # Clear previous log
        self.output_log_widget.insert(tk.END, "\n--- 正在清理项目文件 ---\n")
        self.output_log_widget.update_idletasks()

        files_to_clean = []
        vvp_file = self.vvp_output_entry.get()
        vcd_file = self.vcd_output_entry.get()

        if vvp_file: files_to_clean.append(vvp_file)
        if vcd_file: files_to_clean.append(vcd_file)

        cleaned_count = 0
        for f in files_to_clean:
            # Construct the full path relative to the current project directory if project_path is set,
            # otherwise assume current working directory.
            file_full_path = os.path.join(os.path.dirname(self.project_path) if self.project_path else os.getcwd(), f)

            if os.path.exists(file_full_path):
                try:
                    os.remove(file_full_path)
                    self.output_log_widget.insert(tk.END, f"已删除: {os.path.basename(f)}\n")
                    cleaned_count += 1
                except Exception as e:
                    self.output_log_widget.insert(tk.END, f"删除 {os.path.basename(f)} 失败: {e}\n")
            else:
                self.output_log_widget.insert(tk.END, f"文件不存在，跳过: {os.path.basename(f)}\n")

        if cleaned_count > 0:
            self.output_log_widget.insert(tk.END, "\n--- 清理完成 ---\n")
        else:
            self.output_log_widget.insert(tk.END, "\n--- 没有发现可清理的文件 ---\n")
        self.output_log_widget.see(tk.END)

    def add_verilog_files(self):
        files = filedialog.askopenfilenames(
            title="选择 Verilog 源文件",
            filetypes=[("Verilog Files", "*.v"), ("All Files", "*.*")]
        )
        for f in files:
            if f not in self.verilog_files:
                self.verilog_files.append(f)
                # Display only the basename in the Treeview
                self.file_listbox.insert("", "end", values=(os.path.basename(f),))

    def remove_verilog_files(self):
        selected_items = self.file_listbox.selection()
        if not selected_items:
            messagebox.showinfo("提示", "请选择要移除的文件。")
            return
        
        # Process from end to start to avoid index issues when deleting
        for item in sorted(selected_items, reverse=True):
            # Get the current index of the item in the Treeview
            index_in_treeview = self.file_listbox.index(item)
            
            # Remove from internal list using the index
            if 0 <= index_in_treeview < len(self.verilog_files):
                del self.verilog_files[index_in_treeview]
            
            # Remove from Treeview
            self.file_listbox.delete(item)

    def move_file_up(self):
        selected_items = self.file_listbox.selection()
        if not selected_items:
            return # No item selected
        
        # We only move the first selected item for simplicity. Can be extended to multiple.
        item_id = selected_items[0]
        current_index = self.file_listbox.index(item_id)
        
        if current_index > 0:
            # Swap in the internal list
            self.verilog_files[current_index], self.verilog_files[current_index - 1] = \
                self.verilog_files[current_index - 1], self.verilog_files[current_index]
            
            # Move in the Treeview
            self.file_listbox.move(item_id, '', current_index - 1)
            # Re-select the moved item
            self.file_listbox.selection_set(item_id)
            self.file_listbox.focus(item_id)

    def move_file_down(self):
        selected_items = self.file_listbox.selection()
        if not selected_items:
            return # No item selected
        
        # We only move the first selected item for simplicity. Can be extended to multiple.
        item_id = selected_items[0]
        current_index = self.file_listbox.index(item_id)
        
        if current_index < len(self.verilog_files) - 1:
            # Swap in the internal list
            self.verilog_files[current_index], self.verilog_files[current_index + 1] = \
                self.verilog_files[current_index + 1], self.verilog_files[current_index]
            
            # Move in the Treeview
            self.file_listbox.move(item_id, '', current_index + 1)
            # Re-select the moved item
            self.file_listbox.selection_set(item_id)
            self.file_listbox.focus(item_id)

    def compile_verilog(self):
        if not self.tool_paths.get('iverilog'):
            messagebox.showerror("错误", "iverilog 未找到。请检查环境设置。")
            return
        if not self.verilog_files:
            messagebox.showerror("错误", "请选择至少一个 Verilog 源文件进行编译。")
            return

        output_vvp = self.vvp_output_entry.get()
        if not output_vvp:
            messagebox.showerror("错误", "请指定编译输出文件名 (.vvp)。")
            return

        extra_flags = []
        flags_str = self.iverilog_flags_entry.get()
        if flags_str:
            extra_flags = shlex.split(flags_str)

        compile_cmd = [self.tool_paths['iverilog'], '-o', output_vvp] + extra_flags + self.verilog_files
        self.run_command(compile_cmd)

    def simulate_verilog(self):
        if not self.tool_paths.get('vvp'):
            messagebox.showerror("错误", "vvp 未找到。请检查环境设置。")
            return
        
        output_vvp = self.vvp_output_entry.get()
        if not output_vvp or not os.path.exists(output_vvp):
            messagebox.showerror("错误", f"编译输出文件 '{output_vvp}' 不存在或未指定。请先成功编译。")
            return

        # VCD output is handled by iverilog/vvp if $dumpfile and $dumpvars are used in testbench
        # We assume the testbench generates the VCD file named in vcd_output_entry
        # If the user's testbench doesn't generate this specific name, they need to adjust it
        # For simple cases, vvp simulation will implicitly create vcd if $dumpfile is used.
        simulate_cmd = [self.tool_paths['vvp'], output_vvp]
        self.run_command(simulate_cmd)

    def view_waveform(self):
        if not self.tool_paths.get('gtkwave'):
            messagebox.showerror("错误", "GTKWave 未找到。请检查环境设置。")
            return
        
        vcd_file = self.vcd_output_entry.get()
        if not vcd_file:
            messagebox.showerror("错误", "请指定波形文件名 (.vcd)。")
            return

        self.launch_gtkwave(self.tool_paths['gtkwave'], vcd_file)

    def open_project(self):
        project_file = filedialog.askopenfilename(
            title="Open Daedalus Project",
            filetypes=[("Daedalus Project Files", "*.json")]
        )
        if not project_file: return

        try:
            with open(project_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.project_path = project_file
            self.verilog_files = data.get('verilog_files', [])
            self.vvp_output_entry.delete(0, tk.END)
            self.vvp_output_entry.insert(0, data.get('vvp_output', "design.vvp"))
            self.vcd_output_entry.delete(0, tk.END)
            self.vcd_output_entry.insert(0, data.get('vcd_output', "wave.vcd"))
            self.gtkw_file_entry.delete(0, tk.END)
            self.gtkw_file_entry.insert(0, data.get('gtkw_file', "wave.gtkw"))

            # Clear and repopulate Treeview
            for item in self.file_listbox.get_children():
                self.file_listbox.delete(item)
            for f in self.verilog_files:
                self.file_listbox.insert("", "end", values=(os.path.basename(f),))
            
            messagebox.showinfo("项目加载", f"项目 '{os.path.basename(project_file)}' 加载成功！")

        except Exception as e:
            messagebox.showerror("错误", f"加载项目失败: {e}")

    def save_project_as(self):
        project_file = filedialog.asksaveasfilename(
            title="保存项目为...",
            defaultextension=".json",
            filetypes=[("JSON Files", "*.json"), ("All Files", "*.*")]
        )
        if project_file:
            project_data = {
                "source_files": self.verilog_files,
                "output_vvp": self.vvp_output_entry.get(),
                "output_vcd": self.vcd_output_entry.get(),
                "gtkw_file": self.gtkw_file_entry.get()
            }
            try:
                with open(project_file, 'w', encoding='utf-8') as f:
                    json.dump(project_data, f, indent=2)
                self.project_path = project_file
                self.output_log_widget.insert(tk.END, f"\n项目保存成功到: {os.path.basename(project_file)}\n")
            except Exception as e:
                messagebox.showerror("错误", f"保存项目失败: {e}")
                self.output_log_widget.insert(tk.END, f"\n保存项目失败: {e}\n")

    def new_project(self):
        """清空当前项目设置，开始一个新项目"""
        self.verilog_files = []
        # Clear and repopulate Treeview (corrected for ttk.Treeview)
        for item in self.file_listbox.get_children():
            self.file_listbox.delete(item)
        self.vvp_output_entry.delete(0, tk.END)
        self.vvp_output_entry.insert(0, "design.vvp")
        self.vcd_output_entry.delete(0, tk.END)
        self.vcd_output_entry.insert(0, "wave.vcd")
        self.gtkw_file_entry.delete(0, tk.END)
        self.gtkw_file_entry.insert(0, "wave.gtkw")
        self.project_path = ""
        self.output_log_widget.insert(tk.END, "\n--- 新项目已创建，所有设置已清空 ---\n")
        messagebox.showinfo("新建项目", "新项目已成功创建。")

    def load_window_state(self):
        """从配置文件加载窗口大小和位置"""
        if os.path.exists(self.config_file_path):
            try:
                with open(self.config_file_path, 'r') as f:
                    config = json.load(f)
                geometry = config.get('geometry')
                if geometry:
                    self.master.geometry(geometry)
            except Exception as e:
                print(f"加载窗口状态失败: {e}")
                # Fallback to default if loading fails
                self.master.geometry("800x600")
        else:
            # Default geometry if no config file exists
            self.master.geometry("800x600")

    def save_window_state(self):
        """保存当前窗口的大小和位置到配置文件"""
        geometry = self.master.geometry()
        config = {'geometry': geometry}
        try:
            with open(self.config_file_path, 'w') as f:
                json.dump(config, f)
        except Exception as e:
            print(f"保存窗口状态失败: {e}")

    def on_closing(self):
        """窗口关闭时的回调函数，检查未保存的文件，保存状态并退出"""
        unsaved_files = []
        for file_path, (tab_frame, text_widget) in self.open_editors.items():
            if text_widget.edit_modified():
                unsaved_files.append(os.path.basename(file_path))

        if unsaved_files:
            file_list_str = "\n - ".join(unsaved_files)
            message = f"您有以下文件尚未保存:\n\n - {file_list_str}\n\n您想在退出前保存它们吗？"
            
            user_choice = messagebox.askyesnocancel("退出前保存?", message)

            if user_choice is True: # User chose "Yes"
                for file_path, (tab_frame, text_widget) in self.open_editors.items():
                    if text_widget.edit_modified():
                        self.save_current_file(file_path, text_widget) # Call the new save method
                
            elif user_choice is None: # User chose "Cancel"
                return # Abort the closing process

        # If user chose "No", we just proceed to close.
        self.save_window_state()
        self.master.destroy()

    def open_file_in_editor(self, event):
        selected_items = self.file_listbox.selection()
        if not selected_items:
            messagebox.showinfo("提示", "请选择要打开的文件。")
            return

        item_id = selected_items[0]
        # Get the index of the selected item in the Treeview
        index_in_treeview = self.file_listbox.index(item_id)
        
        file_path_to_open = ""
        if 0 <= index_in_treeview < len(self.verilog_files):
            file_path_to_open = self.verilog_files[index_in_treeview]
        else:
            messagebox.showerror("错误", "无法获取文件路径。")
            return
        
        file_basename = os.path.basename(file_path_to_open)

        if file_path_to_open in self.open_editors:
            # If the file is already open in an editor, focus on that tab
            self.notebook.select(self.open_editors[file_path_to_open][0]) # select the frame
        else:
            # If the file is not open in an editor, open a new tab
            tab_data = self.create_editor_tab(file_path_to_open)
            if tab_data: # If creation was successful (tab_frame, text_widget)
                tab_frame, text_widget = tab_data
                self.notebook.add(tab_frame, text=file_basename)
                self.notebook.select(tab_frame)
                self.open_editors[file_path_to_open] = (tab_frame, text_widget)
            else:
                messagebox.showerror("错误", f"无法创建编辑器标签页以打开文件：{file_basename}")

    def create_editor_tab(self, file_path):
        editor_frame = ttk.Frame(self.notebook)

        # Frame to hold line numbers and text widget
        text_line_frame = ttk.Frame(editor_frame)
        text_line_frame.pack(expand=True, fill="both")
        
        self.linenumbers = tk.Canvas(text_line_frame, width=30, background="#f0f0f0", highlightthickness=0)
        self.linenumbers.pack(side=tk.LEFT, fill="y")

        text_widget = scrolledtext.ScrolledText(text_line_frame, wrap=tk.WORD, undo=True)
        text_widget.pack(side=tk.LEFT, expand=True, fill="both")

        # Configure Pygments related tags
        for token_type, style_config in self.pygments_tag_styles.items():
            text_widget.tag_config(style_config["tag"], **{k: v for k, v in style_config.items() if k != "tag"})

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            text_widget.insert(tk.END, content)
            text_widget.edit_modified(False) # Reset modified flag after loading
            self._apply_syntax_highlighting(text_widget) # Apply initial highlighting
            self._update_line_numbers(text_widget, self.linenumbers) # Initial line number update
            self._check_editor_modified_status(text_widget, file_path) # Initial status check
        except Exception as e:
            messagebox.showerror("错误", f"无法打开文件 {os.path.basename(file_path)}: {e}")
            editor_frame.destroy() # Clean up the frame if opening fails
            return None # Indicate failure

        # Bind key release event for real-time highlighting and line numbers
        text_widget.bind("<KeyRelease>", lambda event, tw=text_widget, ln=self.linenumbers, fp=file_path: self._handle_editor_content_change(event, tw, ln, fp))
        text_widget.bind("<Configure>", lambda event, tw=text_widget, ln=self.linenumbers, fp=file_path: self._update_line_numbers(tw, ln)) # Configure also updates line numbers
        text_widget.bind("<MouseWheel>", lambda event, tw=text_widget, ln=self.linenumbers, fp=file_path: self._update_line_numbers(tw, ln))
        text_widget.bind("<Button-4>", lambda event, tw=text_widget, ln=self.linenumbers, fp=file_path: self._update_line_numbers(tw, ln)) # For Linux scroll up
        text_widget.bind("<Button-5>", lambda event, tw=text_widget, ln=self.linenumbers, fp=file_path: self._update_line_numbers(tw, ln)) # For Linux scroll down
        text_widget.bind("<<Modified>>", lambda event, tw=text_widget, fp=file_path: self._check_editor_modified_status(tw, fp)) # Bind to the <<Modified>> event

        # Link text widget scroll to line numbers scroll
        text_widget.config(yscrollcommand=lambda *args: self._on_text_scroll(text_widget, self.linenumbers, *args))

        # Create a context menu for the editor
        context_menu = tk.Menu(text_widget, tearoff=0)
        context_menu.add_command(label="剪切", command=lambda: text_widget.event_generate("<<Cut>>"))
        context_menu.add_command(label="复制", command=lambda: text_widget.event_generate("<<Copy>>"))
        context_menu.add_command(label="粘贴", command=lambda: text_widget.event_generate("<<Paste>>"))
        context_menu.add_separator()
        context_menu.add_command(label="全选", command=lambda: text_widget.event_generate("<<SelectAll>>"))
        context_menu.add_command(label="关闭当前标签页", command=lambda: self.close_tab_by_widget(text_widget)) # Add close tab to context menu

        def show_context_menu(event):
            context_menu.tk_popup(event.x_root, event.y_root)

        text_widget.bind("<Button-3>", show_context_menu) # Bind right-click

        return editor_frame, text_widget # Return both the frame and the text widget

    def _handle_editor_content_change(self, event, text_widget, linenumbers_canvas, file_path):
        # Call syntax highlighting
        self._apply_syntax_highlighting(text_widget)
        # Call line number update
        self._update_line_numbers(text_widget, linenumbers_canvas)
        # Call modified status check
        self._check_editor_modified_status(text_widget, file_path)

    def _on_text_scroll(self, text_widget, linenumbers_canvas, *args):
        text_widget.yview(*args) # Apply scroll to text widget
        self._update_line_numbers(text_widget, linenumbers_canvas) # Update line numbers

    def _update_line_numbers(self, text_widget, linenumbers_canvas):
        linenumbers_canvas.delete("all")

        # Get the first visible line number
        first_visible_line = int(text_widget.index("@0,0").split(".")[0])
        # Get the last visible line number by checking the yview
        last_visible_line = int(text_widget.index(f"@0,{linenumbers_canvas.winfo_height()}").split(".")[0]) + 1 # +1 to ensure last line is checked

        for line_number in range(first_visible_line, last_visible_line):
            dline = text_widget.dlineinfo(f"{line_number}.0")
            if dline is None: # Line is not visible or doesn't exist
                continue
            
            y = dline[1] # Y-coordinate of the line
            linenumbers_canvas.create_text(2, y, anchor="nw", text=str(line_number), fill="gray")

    def _check_editor_modified_status(self, text_widget, file_path):
        is_modified = text_widget.edit_modified()
        file_basename = os.path.basename(file_path)

        # Find the tab associated with this file_path
        tab_index = -1
        for i, (f_path, (tab_frame, _)) in enumerate(self.open_editors.items()):
            if f_path == file_path:
                tab_index = self.notebook.index(tab_frame)
                break
        
        if tab_index != -1:
            current_tab_text = self.notebook.tab(tab_index, "text")
            expected_tab_text = file_basename + "*" if is_modified else file_basename

            if current_tab_text != expected_tab_text:
                self.notebook.tab(tab_index, text=expected_tab_text)

    def _apply_syntax_highlighting(self, text_widget):
        # Clear all existing tags
        for tag_name in text_widget.tag_names():
            if tag_name not in ("sel", "error", "warning", "cmd", "match"): # Exclude built-in selection and my log/find tags
                text_widget.tag_remove(tag_name, "1.0", tk.END)

        content = text_widget.get("1.0", tk.END + "-1c") # Get all text, excluding the final newline
        lexer = VerilogLexer() # Initialize Verilog Lexer

        offset = 0
        for token_type, value in lexer.get_tokens_unprocessed(content):
            tag_config = self.pygments_tag_styles.get(token_type)
            # Try to find a more general tag if specific one not found
            if not tag_config:
                # Walk up the token hierarchy to find a matching tag
                current_type = token_type
                while current_type.parent and not tag_config:
                    current_type = current_type.parent
                    tag_config = self.pygments_tag_styles.get(current_type)
            
            if tag_config: # Apply tag if found
                start_index = text_widget.index(f"1.0 + {offset}c")
                end_index = text_widget.index(f"1.0 + {offset + len(value)}c")
                text_widget.tag_add(tag_config["tag"], start_index, end_index)
            offset += len(value)

    def find_text(self):
        current_text_widget = self._get_current_editor_widget()
        if not current_text_widget:
            messagebox.showinfo("提示", "请先打开一个文件进行编辑。")
            return

        find_dialog = tk.Toplevel(self.master)
        find_dialog.title("查找")
        find_dialog.transient(self.master) # Make dialog transient to main window
        find_dialog.grab_set() # Grab focus
        find_dialog.resizable(False, False)

        ttk.Label(find_dialog, text="查找内容:").grid(row=0, column=0, padx=5, pady=5)
        search_entry = ttk.Entry(find_dialog, width=30)
        search_entry.grid(row=0, column=1, padx=5, pady=5)
        search_entry.focus_set()

        def find_next_occurrence():
            search_term = search_entry.get()
            if not search_term: return

            # Clear previous highlights
            current_text_widget.tag_remove("match", "1.0", tk.END)

            start_pos = current_text_widget.search(search_term, current_text_widget.index(tk.INSERT), stopindex=tk.END, nocase=True)
            
            if start_pos:
                end_pos = f"{start_pos}+{len(search_term)}c"
                current_text_widget.tag_add("match", start_pos, end_pos)
                current_text_widget.tag_config("match", background="yellow", foreground="black")
                current_text_widget.see(start_pos)
                current_text_widget.mark_set(tk.INSERT, end_pos) # Move cursor to end of found text
            else:
                messagebox.showinfo("查找", f"未找到 \"{search_term}\"。")
                current_text_widget.mark_set(tk.INSERT, "1.0") # Reset search to beginning

        ttk.Button(find_dialog, text="查找下一个", command=find_next_occurrence).grid(row=0, column=2, padx=5, pady=5)

        # Close dialog on window close button
        find_dialog.protocol("WM_DELETE_WINDOW", find_dialog.destroy)
        self.master.wait_window(find_dialog) # Wait until dialog is closed

    def replace_text(self):
        current_text_widget = self._get_current_editor_widget()
        if not current_text_widget:
            messagebox.showinfo("提示", "请先打开一个文件进行编辑。")
            return

        replace_dialog = tk.Toplevel(self.master)
        replace_dialog.title("查找和替换")
        replace_dialog.transient(self.master)
        replace_dialog.grab_set()
        replace_dialog.resizable(False, False)

        ttk.Label(replace_dialog, text="查找内容:").grid(row=0, column=0, padx=5, pady=5)
        search_entry = ttk.Entry(replace_dialog, width=30)
        search_entry.grid(row=0, column=1, padx=5, pady=5)
        search_entry.focus_set()

        ttk.Label(replace_dialog, text="替换为:").grid(row=1, column=0, padx=5, pady=5)
        replace_entry = ttk.Entry(replace_dialog, width=30)
        replace_entry.grid(row=1, column=1, padx=5, pady=5)

        def find_next_occurrence_replace():
            search_term = search_entry.get()
            if not search_term: return

            # Clear previous highlights
            current_text_widget.tag_remove("match", "1.0", tk.END)

            start_pos = current_text_widget.search(search_term, current_text_widget.index(tk.INSERT), stopindex=tk.END, nocase=True)
            
            if start_pos:
                end_pos = f"{start_pos}+{len(search_term)}c"
                current_text_widget.tag_add("match", start_pos, end_pos)
                current_text_widget.tag_config("match", background="yellow", foreground="black")
                current_text_widget.see(start_pos)
                current_text_widget.mark_set(tk.INSERT, end_pos) # Move cursor to end of found text
            else:
                messagebox.showinfo("查找", f"未找到 \"{search_term}\"。")
                current_text_widget.mark_set(tk.INSERT, "1.0") # Reset search to beginning
        
        def replace_current_occurrence():
            search_term = search_entry.get()
            replace_term = replace_entry.get()
            if not search_term: return
            
            # Check if there's an active selection from find_next_occurrence_replace
            current_selection = current_text_widget.tag_ranges("match")
            if current_selection:
                # If there's a selection, replace it
                start = current_selection[0]
                end = current_selection[1]
                current_text_widget.delete(start, end)
                current_text_widget.insert(start, replace_term)
                current_text_widget.tag_remove("match", "1.0", tk.END) # Clear highlight after replace
                current_text_widget.mark_set(tk.INSERT, f"{start}+{len(replace_term)}c")
                find_next_occurrence_replace() # Find next after replacing
            else:
                # If no active selection, just find the next one
                find_next_occurrence_replace()

        def replace_all_occurrences():
            search_term = search_entry.get()
            replace_term = replace_entry.get()
            if not search_term: return

            current_text_widget.tag_remove("match", "1.0", tk.END) # Clear all highlights

            # Start search from beginning of document
            start_pos = "1.0"
            count = 0
            while True:
                start_pos = current_text_widget.search(search_term, start_pos, stopindex=tk.END, nocase=True)
                if not start_pos: break

                end_pos = f"{start_pos}+{len(search_term)}c"
                current_text_widget.delete(start_pos, end_pos)
                current_text_widget.insert(start_pos, replace_term)
                
                # Move search start past the newly inserted text to avoid infinite loop
                start_pos = current_text_widget.index(f"{start_pos}+{len(replace_term)}c")
                count += 1
            messagebox.showinfo("替换完成", f"已替换 {count} 处。")

        ttk.Button(replace_dialog, text="查找下一个", command=find_next_occurrence_replace).grid(row=0, column=2, padx=5, pady=5)
        ttk.Button(replace_dialog, text="替换", command=replace_current_occurrence).grid(row=1, column=2, padx=5, pady=5)
        ttk.Button(replace_dialog, text="全部替换", command=replace_all_occurrences).grid(row=2, column=2, padx=5, pady=5)

        replace_dialog.protocol("WM_DELETE_WINDOW", replace_dialog.destroy)
        self.master.wait_window(replace_dialog)

    def _get_current_editor_widget(self):
        # Get the currently selected tab
        selected_tab_id = self.notebook.select()
        # Get the widget (frame) associated with the selected tab
        selected_tab_frame = self.notebook.nametowidget(selected_tab_id)

        # Check if the selected tab is the console frame
        if selected_tab_frame == self.console_frame:
            return None # No editor widget in console tab

        # Iterate through open_editors to find the text widget for the selected tab_frame
        for file_path, (tab_frame, text_widget) in self.open_editors.items():
            if tab_frame == selected_tab_frame:
                return text_widget
        return None # Should not happen if open_editors is managed correctly

    def insert_template(self, template_type):
        current_text_widget = self._get_current_editor_widget()
        if not current_text_widget:
            messagebox.showinfo("提示", "请先打开一个文件，然后在编辑器中插入模板。")
            return

        templates = {
            "new_module": """
module new_module (
    // Add inputs and outputs here
    input wire clk,
    input wire rst_n,
    // ...
);

// Internal signals

// Behavioral/Structural logic

endmodule
""",
            "new_testbench": """
`timescale 1ns / 1ps

module testbench_top;

    // Parameters
    parameter CLK_PERIOD = 10;

    // Signals
    reg clk;
    reg rst_n;
    // Add signals for DUT inputs/outputs

    // Instantiate the Unit Under Test (DUT)
    // Replace dut_name with your actual module name
    dut_name UUT (
        // Connect DUT ports
        .clk(clk),
        .rst_n(rst_n)
        // ...
    );

    // Clock generation
    initial begin
        clk = 0;
        forever #(CLK_PERIOD / 2) clk = ~clk;
    end

    // Test sequence
    initial begin
        $dumpfile("wave.vcd");
        $dumpvars(0, testbench_top);

        rst_n = 0; // Assert reset
        #(CLK_PERIOD * 2) rst_n = 1; // De-assert reset

        // Add your test vectors here

        #(CLK_PERIOD * 10)
        $finish;
    end

endmodule
""",
            "always_posedge_clk": """
always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        // Asynchronous reset logic
    end else begin
        // Synchronous logic
    end
end
"""
        }

        template_content = templates.get(template_type)
        if template_content:
            current_text_widget.insert(tk.INSERT, template_content)
        else:
            messagebox.showerror("错误", "未知模板类型。")

    def save_current_file(self, file_path=None, text_widget=None):
        """保存当前激活编辑器或指定编辑器的内容。"""
        if text_widget is None:
            # If no widget is provided, try to get the currently active one
            current_text_widget = self._get_current_editor_widget()
            if not current_text_widget:
                messagebox.showinfo("提示", "请先打开一个文件进行保存。")
                return
            
            # Find the file_path associated with this widget
            for f_path, (tab_frame, tw) in self.open_editors.items():
                if tw == current_text_widget:
                    file_path = f_path
                    text_widget = tw
                    break
            
            if file_path is None:
                messagebox.showerror("错误", "无法找到当前编辑器的文件路径。")
                return

        try:
            content = text_widget.get("1.0", tk.END + "-1c") # Get all text, excluding the final newline
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            text_widget.edit_modified(False) # Reset modified flag
            self._check_editor_modified_status(text_widget, file_path) # Update tab title (remove asterisk)
            self.output_log_widget.insert(tk.END, f"\n文件已保存: {os.path.basename(file_path)}\n")
        except Exception as e:
            messagebox.showerror("保存失败", f"无法保存文件 {os.path.basename(file_path)}: {e}")

    def close_current_tab(self):
        """关闭当前激活的编辑器标签页。"""
        current_text_widget = self._get_current_editor_widget()
        if current_text_widget:
            self.close_tab_by_widget(current_text_widget)
        else:
            messagebox.showinfo("提示", "当前没有活动的编辑器标签页可以关闭。")

    def close_tab_by_widget(self, text_widget_to_close):
        """查找并关闭与给定文本控件关联的标签页。"""
        file_to_close = None
        frame_to_close = None

        for f_path, (tab_frame, text_widget) in self.open_editors.items():
            if text_widget == text_widget_to_close:
                # 首先，检查文件是否已修改
                if text_widget.edit_modified():
                    response = messagebox.askyesnocancel("保存更改?", f"文件 {os.path.basename(f_path)} 已被修改。是否要保存？")
                    if response is True: # 用户选择"是"
                        self.save_current_file(f_path, text_widget)
                    elif response is None: # 用户选择"取消"
                        return # 中止关闭操作

                file_to_close = f_path
                frame_to_close = tab_frame
                break
        
        if file_to_close and frame_to_close:
            self.notebook.forget(frame_to_close) # 从 Notebook 中移除标签页
            del self.open_editors[file_to_close] # 从我们的追踪字典中删除

if __name__ == "__main__":
    root = tk.Tk()
    gui = VerilogGUI(root)
    root.mainloop() 