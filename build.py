import os.path
import subprocess
import shutil

venv_dir = ".venv"
exe_name = "DNF魔界人跳一跳半自动工具_by风之凌殇.exe"
icon = "mo_jie_ren.ico"
source_file = "mo_jie_ren.py"

# 初始化venv
subprocess.call(f"python -m venv {venv_dir}")

# 计算相关文件的绝对路径
venv_scripts_path = os.path.realpath(f"{venv_dir}/Scripts")
python_path = os.path.join(venv_scripts_path, "python.exe")
pip_path = os.path.join(venv_scripts_path, "pip.exe")
pyinstaller_path = os.path.join(venv_scripts_path, "pyinstaller.exe")

# 安装依赖
subprocess.call(f"{python_path} -m pip install -i https://pypi.tuna.tsinghua.edu.cn/simple --upgrade pip setuptools wheel")
subprocess.call(f"{pip_path} install -i https://pypi.tuna.tsinghua.edu.cn/simple --upgrade -r requirements.txt")

# 准备打包
subprocess.call(f"{python_path} -m pip install -i https://pypi.tuna.tsinghua.edu.cn/simple --upgrade pyinstaller")
subprocess.call(f"{pyinstaller_path} --name {exe_name} --icon {icon} -F {source_file}")

# 将打包结果复制出来
shutil.copy(f"dist/{exe_name}", exe_name)

# 移除临时文件
shutil.rmtree("dist")
shutil.rmtree("build")
os.remove(f"{exe_name}.spec")
