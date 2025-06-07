import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
from tkinter import ttk # Import ttk module
import shutil
import subprocess
import os
import json

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

        # --- GUI Elements ---
        self.create_widgets()

        # --- Environment Check on startup ---
        self.check_dependencies()

    def create_widgets(self):
        # Frame for file selection
        file_frame = ttk.LabelFrame(self.master, text="Verilog Source Files")
        file_frame.pack(fill="x")

        # Use Treeview for file list
        self.file_listbox = ttk.Treeview(file_frame, columns=("Filename"), show="headings", height=5)
        self.file_listbox.heading("Filename", text="Filename")
        self.file_listbox.pack(side=tk.LEFT, fill="both", expand=True)
        
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
        output_frame = ttk.LabelFrame(self.master, text="Output Settings")
        output_frame.pack(fill="x")

        ttk.Label(output_frame, text="Compiled Output (.vvp):").grid(row=0, column=0, sticky="w", pady=2)
        self.vvp_output_entry = ttk.Entry(output_frame, width=40)
        self.vvp_output_entry.insert(0, "design.vvp")
        self.vvp_output_entry.grid(row=0, column=1, sticky="ew", pady=2)

        ttk.Label(output_frame, text="Waveform Output (.vcd):").grid(row=1, column=0, sticky="w", pady=2)
        self.vcd_output_entry = ttk.Entry(output_frame, width=40)
        self.vcd_output_entry.insert(0, "wave.vcd")
        self.vcd_output_entry.grid(row=1, column=1, sticky="ew", pady=2)
        output_frame.grid_columnconfigure(1, weight=1)

        # Frame for command buttons
        cmd_frame = ttk.Frame(self.master)
        cmd_frame.pack(fill="x")

        self.compile_btn = ttk.Button(cmd_frame, text="Compile (iverilog)", command=self.compile_verilog)
        self.compile_btn.pack(side=tk.LEFT, expand=True, fill="x", padx=5)

        self.simulate_btn = ttk.Button(cmd_frame, text="Simulate (vvp)", command=self.simulate_verilog)
        self.simulate_btn.pack(side=tk.LEFT, expand=True, fill="x", padx=5)

        self.view_wave_btn = ttk.Button(cmd_frame, text="View Wave (GTKWave)", command=self.view_waveform)
        self.view_wave_btn.pack(side=tk.LEFT, expand=True, fill="x", padx=5)

        self.clean_btn = ttk.Button(cmd_frame, text="Clean Project", command=self.clean_project)
        self.clean_btn.pack(side=tk.LEFT, expand=True, fill="x", padx=5)

        # Frame for information output
        log_frame = ttk.LabelFrame(self.master, text="Command Output & Log")
        log_frame.pack(fill="both", expand=True)

        self.output_log_widget = scrolledtext.ScrolledText(log_frame, wrap=tk.WORD, height=15)
        self.output_log_widget.pack(fill="both", expand=True)

        # Menu Bar for project management
        menubar = tk.Menu(self.master)
        self.master.config(menu=menubar)

        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Open Project...", command=self.open_project)
        file_menu.add_command(label="Save Project As...", command=self.save_project_as)
        file_menu.add_separator()
        file_menu.add_command(label="New Project", command=self.new_project)
        file_menu.add_command(label="Exit", command=self.master.quit)

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
        self.output_log_widget.insert(tk.END, f"正在执行命令: {' '.join(command_list)}\n\n")
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

        self.output_log_widget.insert(tk.END, f"\n正在启动 GTKWave 加载 {vcd_file_path}...\n")
        try:
            # 使用Popen启动一个独立的进程，我们的GUI不用等它
            subprocess.Popen([gtkwave_path, vcd_file_path],
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

        compile_cmd = [self.tool_paths['iverilog'], '-o', output_vvp] + self.verilog_files
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
                "output_vcd": self.vcd_output_entry.get()
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
        self.file_listbox.delete(0, tk.END)
        self.vvp_output_entry.delete(0, tk.END)
        self.vvp_output_entry.insert(0, "design.vvp")
        self.vcd_output_entry.delete(0, tk.END)
        self.vcd_output_entry.insert(0, "wave.vcd")
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
        """窗口关闭时的回调函数，用于保存状态并退出"""
        self.save_window_state()
        self.master.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    gui = VerilogGUI(root)
    root.mainloop() 