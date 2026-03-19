#!/usr/bin/env python3
"""
RagHubMCP 安装向导原型 - 仅用于验证菜单逻辑
不执行任何实际操作

跨平台支持: Windows / Linux / macOS
"""

import sys
import os
import random
from typing import Dict, Any, List

# ANSI 颜色码
class Color:
    GREEN = '\033[92m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    YELLOW = '\033[93m'
    CYAN = '\033[96m'
    BOLD = '\033[1m'
    RESET = '\033[0m'

def colorize(text: str, color: str) -> str:
    """添加颜色"""
    return f"{color}{text}{Color.RESET}"

# 跨平台键盘输入
def get_key():
    """跨平台获取单个按键"""
    if os.name == 'nt':  # Windows
        import msvcrt
        key = msvcrt.getch()
        if key == b'\xe0':  # 方向键前缀
            key = msvcrt.getch()
            if key == b'H':
                return 'UP'
            elif key == b'P':
                return 'DOWN'
        elif key == b'\r':
            return 'ENTER'
        elif key == b'\x1b':
            return 'ESC'
        return None
    else:  # Linux / macOS
        import termios
        import tty
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            ch = sys.stdin.read(1)
            if ch == '\x1b':  # ESC or arrow key
                ch2 = sys.stdin.read(1)
                if ch2 == '[':
                    ch3 = sys.stdin.read(1)
                    if ch3 == 'A':
                        return 'UP'
                    elif ch3 == 'B':
                        return 'DOWN'
                return 'ESC'
            elif ch == '\r' or ch == '\n':
                return 'ENTER'
            return None
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

def clear_screen():
    """清屏"""
    os.system('cls' if os.name == 'nt' else 'clear')

def print_header():
    """打印固定的项目头部"""
    print()
    print(colorize("  RagHubMCP 安装向导", Color.BOLD + Color.CYAN))
    print("  " + "─" * 46)
    print()

def print_status_line():
    """打印状态行：必须项 + 组件 + 端口（水平排列）"""
    # 硬件信息
    gpu = "RTX 3080" if random.choice([True, False]) else "无"
    mem = random.choice([4, 8, 16, 32])
    disk = random.choice([50, 100, 200, 500])
    
    print(f"  硬件: GPU: {gpu} | 内存: {mem}GB | 磁盘: {disk}GB可用")
    print()
    
    # 必须项（水平）
    must_items = []
    must_items.append(colorize("✓", Color.GREEN) + " Python")
    must_items.append(colorize("✓", Color.GREEN) + " Node")
    must_items.append(colorize("✓", Color.GREEN) + " Git")
    
    # 组件（水平）
    comp_items = []
    comp_items.append((colorize("✓", Color.GREEN) if env_status['docker'] else colorize("✗", Color.RED)) + " Docker")
    comp_items.append((colorize("✓", Color.GREEN) if env_status['ollama'] else colorize("✗", Color.RED)) + " Ollama")
    comp_items.append((colorize("✓", Color.GREEN) if env_status['chroma'] else colorize("✗", Color.RED)) + " Chroma")
    comp_items.append((colorize("✓", Color.GREEN) if env_status['qdrant'] else colorize("✗", Color.RED)) + " Qdrant")
    
    # 端口（水平）- 显示实际端口状态
    port_items = []
    backend_ok = check_port(ports['backend'])
    frontend_ok = check_port(ports['frontend'])
    port_items.append((colorize("✓", Color.GREEN) if backend_ok else colorize("✗", Color.RED)) + f" 后端:{ports['backend']}")
    port_items.append((colorize("✓", Color.GREEN) if frontend_ok else colorize("✗", Color.RED)) + f" 前端:{ports['frontend']}")
    
    print(f"  必须项: {'  '.join(must_items)}")
    print(f"  组件:   {'  '.join(comp_items)}")
    print(f"  端口:   {'  '.join(port_items)}")
    
    # 端口冲突提示
    if not backend_ok or not frontend_ok:
        print()
        print("  " + colorize("⚠ 端口冲突，请修改 config.yaml", Color.YELLOW))
    
    print()
    print("  " + "─" * 46)

def select_menu(options: List[str], history_lines: List[str]):
    """
    交互式菜单：上下键选择，回车确认
    返回: 选项索引 (0-based) 或 None(ESC)
    """
    selected = 0
    
    while True:
        clear_screen()
        
        # 固定头部
        print_header()
        
        # 状态行
        print_status_line()
        
        print()
        
        # 历史记录
        for line in history_lines:
            print(line)
        print()
        
        # 菜单选项
        for i, option in enumerate(options):
            if i == selected:
                prefix = colorize("  ► ", Color.BLUE + Color.BOLD)
            else:
                prefix = "    "
            print(f"{prefix}{option}")
        
        key = get_key()
        
        if key == 'UP':
            selected = (selected - 1) % len(options)
        elif key == 'DOWN':
            selected = (selected + 1) % len(options)
        elif key == 'ENTER':
            return selected
        elif key == 'ESC':
            return None

def simulate_install():
    """模拟安装: 80%成功率"""
    return random.choice([True, True, True, True, False])

def get_install_error():
    """模拟安装失败原因"""
    errors = [
        "端口冲突 (11434 已被占用)",
        "进程冲突 (已有实例运行中)",
        "权限不足 (需要管理员权限)",
        "网络超时 (下载失败)"
    ]
    return random.choice(errors)

# 环境状态
env_status = {
    'python': True,
    'nodejs': True,
    'git': True,
    'docker': False,
    'ollama': False,
    'chroma': True,
    'qdrant': False
}

# 端口配置（通过配置文件修改）
ports = {
    'backend': 8818,
    'frontend': 3315,
    'ollama': 11434,
    'qdrant': 6333
}

# 用户选择
user_choices: Dict[str, Any] = {
    'model_type': None,
    'api_provider': None
}

def check_port(port: int) -> bool:
    """检查端口是否可用"""
    import socket
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('127.0.0.1', port))
            return True  # 端口可用
    except:
        return False  # 端口被占用

def step1_detection(history: List[str]):
    """步骤1: 环境检测"""
    # 直接返回继续
    choice = select_menu(["继续"], history)
    return None if choice is None else []

def step2_select_mode(history: List[str]):
    """步骤2: 选择安装方式"""
    options = [
        "集成安装（推荐）",
        "Docker部署",
        "单独服务配置"
    ]
    
    return select_menu(options, history)

def integrated_install(history: List[str]) -> bool:
    """集成安装流程"""
    missing = []
    if not env_status['qdrant']:
        missing.append('Qdrant')
    
    if not missing:
        return True
    
    for component in missing:
        choice = select_menu(["自动安装", "手动安装"], history)
        if choice is None:
            return False
        
        if choice == 0:
            success = simulate_install()
            if not success:
                choice = select_menu(["我已手动安装"], history)
                if choice is None:
                    return False
        env_status[component.lower()] = True
    
    return True

def docker_install(history: List[str]) -> bool:
    """Docker安装流程"""
    if not env_status['docker']:
        choice = select_menu(["自动安装Docker", "手动安装Docker"], history)
        if choice is None:
            return False
        
        if choice == 0:
            success = simulate_install()
            if not success:
                choice = select_menu(["我已手动安装"], history)
                if choice is None:
                    return False
        env_status['docker'] = True
    
    return True

def manual_config(history: List[str]) -> bool:
    """单独服务配置"""
    if not env_status['chroma'] and not env_status['qdrant']:
        choice = select_menu(["跳过", "安装Chroma", "安装Qdrant"], history)
        
        if choice is None:
            return False
        elif choice == 1:
            success = simulate_install()
            if success:
                env_status['chroma'] = True
        elif choice == 2:
            success = simulate_install()
            if success:
                env_status['qdrant'] = True
    return True

def model_config(history: List[str]):
    """模型配置"""
    choice = select_menu([
        "跳过（稍后配置）",
        "本地Ollama（推荐有GPU）",
        "API方式（云端，无需GPU）"
    ], history)
    
    if choice is None:
        return None
    elif choice == 0:
        user_choices['model_type'] = 'skip'
        return 'skip'
    elif choice == 1:
        user_choices['model_type'] = 'ollama'
        
        if not env_status['ollama']:
            choice = select_menu(["安装Ollama", "跳过"], history)
            if choice is None:
                return None
            elif choice == 0:
                success = simulate_install()
                if not success:
                    choice = select_menu(["我已手动安装", "跳过"], history)
                    if choice is None:
                        return None
                    elif choice == 0:
                        env_status['ollama'] = True
            else:
                return 'ollama-skip'
        return 'ollama'
    else:
        user_choices['model_type'] = 'api'
        
        choice = select_menu(["OpenAI", "其他兼容服务"], history)
        if choice is None:
            return None
        user_choices['api_provider'] = 'openai' if choice == 0 else 'other'
        return 'api'

def step5_mcp_import(history: List[str]):
    """MCP导入"""
    choice = select_menu(["跳过", "OpenCode", "CherryStudio", "Claude Desktop", "其他"], history)
    
    if choice is None:
        return None
    elif choice == 0:
        return "skip"
    
    platforms = {1: "OpenCode", 2: "CherryStudio", 3: "Claude Desktop", 4: "其他"}
    return platforms[choice]

def show_final_report(history: List[str], mcp, model):
    """最终报告"""
    clear_screen()
    
    print_header()
    print_status_line()
    print()
    
    # 打印选择结果
    for line in history:
        print(line)
    
    print()
    print(colorize("  🎉 RagHubMCP 配置完成！", Color.BOLD + Color.YELLOW))
    print()
    print("  启动: npm run dev")
    print("        python main.py")
    print(f"  控制台: http://localhost:{ports['frontend']}")
    print(f"  API: http://localhost:{ports['backend']}")
    print()

def main():
    history = []
    
    # 步骤1: 环境检测（不记录）
    if step1_detection(history) is None:
        print("\n  已取消")
        return
    
    # 步骤2: 选择安装方式
    mode = step2_select_mode(history)
    if mode is None:
        print("\n  已取消")
        return
    
    modes = {0: "集成安装", 1: "Docker部署", 2: "单独服务配置"}
    history.append("  1. → " + colorize(modes[mode], Color.GREEN))
    history.append("  " + "─" * 46)
    
    # 步骤3: 组件安装
    success = integrated_install(history) if mode == 0 else \
              docker_install(history) if mode == 1 else \
              manual_config(history)
    
    if not success:
        print("\n  已取消")
        return
    
    # 记录数据库/组件选择
    if mode == 0:
        history.append("  2. → " + colorize("Qdrant", Color.GREEN))
    elif mode == 1:
        history.append("  2. → " + colorize("Docker", Color.GREEN))
    else:
        if env_status['chroma']:
            history.append("  2. → " + colorize("Chroma", Color.GREEN))
        elif env_status['qdrant']:
            history.append("  2. → " + colorize("Qdrant", Color.GREEN))
        else:
            history.append("  2. → 跳过")
    history.append("  " + "─" * 46)
    
    # 步骤4: 模型配置
    model = model_config(history)
    if model is None:
        print("\n  已取消")
        return
    
    if model == 'skip':
        history.append("  3. → 跳过")
    elif model == 'ollama':
        history.append("  3. → " + colorize("本地Ollama", Color.GREEN))
    elif model == 'ollama-skip':
        history.append("  3. → Ollama (未安装)")
    elif model == 'api':
        provider = user_choices.get('api_provider', 'unknown')
        history.append("  3. → " + colorize(f"API ({provider})", Color.GREEN))
    history.append("  " + "─" * 46)
    
    # 步骤5: MCP导入
    mcp = step5_mcp_import(history)
    if mcp is None:
        print("\n  已取消")
        return
    
    if mcp == "skip":
        history.append("  4. → 跳过")
    else:
        history.append("  4. → " + colorize(mcp, Color.GREEN))
    
    # 完成
    show_final_report(history, mcp, model)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n  已取消")
        sys.exit(0)