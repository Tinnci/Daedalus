# Verilog GUI Wrapper

中文: 这是一个用于Icarus Verilog和GTKWave的GUI Wrapper，旨在简化Verilog的编译、仿真和波形查看流程，尤其对初学者非常友好。
English: This is a GUI Wrapper for Icarus Verilog and GTKWave, designed to simplify the Verilog compilation, simulation, and waveform viewing process, especially user-friendly for beginners.

## 功能特点 / Features

*   **工具定位 / Tool Location**: 自动检测 `iverilog`, `vvp`, `gtkwave` 的安装路径。 / Automatically detects the installation paths of `iverilog`, `vvp`, and `gtkwave`.
*   **命令构建 / Command Construction**: 根据用户输入动态生成编译和仿真命令。 / Dynamically generates compilation and simulation commands based on user input.
*   **命令执行 / Command Execution**: 在后台执行Verilog编译和仿真。 / Executes Verilog compilation and simulation in the background.
*   **实时反馈 / Real-time Feedback**: 在GUI界面实时显示编译和仿真日志。 / Displays compilation and simulation logs in real-time on the GUI interface.
*   **波形查看 / Waveform Viewing**: 一键启动GTKWave查看仿真波形。 / One-click launch of GTKWave to view simulation waveforms.
*   **项目管理 / Project Management**: 保存和加载项目配置。 / Saves and loads project configurations.

## 技术栈 / Tech Stack

*   **Python**
*   **Tkinter** (GUI)

## 使用说明 / Usage

### 环境准备 / Environment Setup

中文: 请确保您的系统已安装以下工具，并已将其添加到系统环境变量PATH中：
English: Please ensure that the following tools are installed on your system and added to your system's PATH environment variable:

*   **Icarus Verilog**: 用于编译和仿真Verilog代码。 / Used for compiling and simulating Verilog code.
*   **GTKWave**: 用于查看VCD波形文件。 / Used for viewing VCD waveform files.

### 运行程序 / Running the Program

1.  中文: 克隆或下载本项目。 / English: Clone or download this project.
2.  中文: 运行 `python verilog_gui.py` 启动GUI Wrapper。 / English: Run `python verilog_gui.py` to start the GUI Wrapper.

## 开发者 / Developer

[Driezy]

## 许可证 / License

中文: 本项目使用 GNU General Public License v3.0 (GPLv3) 许可证。更多详情请参阅根目录下的 `LICENSE` 文件。
English: This project is licensed under the GNU General Public License v3.0 (GPLv3). For more details, please see the `LICENSE` file in the root directory.
