#!/usr/bin/env python
# coding: utf-8

# 提取exe中的pyc
import os
import sys
import pyinstxtractor
try:
    from uncompyle6.bin import uncompile
except:
    print("没有安装uncompyle6，尝试pip install uncompyle6")
    sys.exit()
import shutil


# 读取校验头
def find_magic(pyc_dir):
    struct_file = os.path.join(pyc_dir,"struct.pyc")
    if not os.path.exists(struct_file):
        print(f"没有找到{struct_file}")
        sys.exit()
    with open(struct_file,"rb") as f:
        magic = f.read(16)

    return magic
	
#获取文件名
def find_pyc(pyc_dir):
    for pyc_file in os.listdir(pyc_dir):
        #print(f"遍历文件:{pyc_file}")
        if not pyc_file.startswith("pyi-") and not pyc_file.startswith("_") and pyc_file.endswith("manifest"):
            main_file = pyc_file.replace(".exe.manifest", ".pyc")
            result = f"{pyc_dir}/{main_file}"
            print(f"找到文件:{result}")
            return main_file


# 找到程序中的pyc文件
def find_pyc_path(path,pyc_name):
    files = os.listdir(path)
    for file in files:
        file_path = os.path.join(path, file)
        print(f"遍历{path}:{file} diff {pyc_name} diff :{file == pyc_name}")
        if file == pyc_name:
            return file_path
        if os.path.isdir(file_path):
            ret = find_pyc_path(file_path,pyc_name)
            if ret:
                return ret

def exe2py(exe_file, complie_child=False):
    # 先执行pyinstxtractor将exe转化为pyc文件
    sys.argv = ['pyinstxtractor.py', exe_file]
    pyinstxtractor.main()


    # 恢复当前目录位置
    os.chdir("..")

    # 下面解析pyc文件
    # 1. 先找到文件头
    pyc_dir = os.path.basename(exe_file) + "_extracted"
    magic = find_magic(pyc_dir)
    print(f"找到文件头:{magic.hex()}")

    # 然后遍历pyc文件加上文件头
    if os.path.exists("pycfile_tmp"):
        shutil.rmtree("pycfile_tmp")
    os.mkdir("pycfile_tmp")

    main_file = find_pyc(pyc_dir)

    main_path_file = find_pyc_path(pyc_dir,main_file)

    if not main_path_file:
        print(f"没有找到主程序pyc文件:{main_path_file}")
        sys.exit()
    print(f"找到主程序pyc文件:{main_path_file}")
    main_file_result = f"pycfile_tmp/{main_file}.pyc"
    with open(f"{main_path_file}", "rb") as read, open(main_file_result, "wb") as write:

        magic_ = read.read(4)
        if magic_ == magic[:4]:
            print(f"{main_path_file}已经存在文件头")
            pass
        else:
            write.write(magic)
        write.write(magic_)
        write.write(read.read())

    if os.path.exists("py_result"):
        shutil.rmtree("py_result")
    os.mkdir("py_result")
    sys.argv = ['uncompyle6', '-o',
                f'py_result/{main_file}.py', main_file_result]
    uncompile.main_bin()

    # 下面开始反编译 引用的包里面的pyc文件
    pyz_dir = f"{pyc_dir}/PYZ-00.pyz_extracted"
    for pyc_file in os.listdir(pyz_dir):
        if not pyc_file.endswith(".pyc"):
            continue
        pyc_file_src = f"{pyz_dir}/{pyc_file}"
        pyc_file_dest = f"pycfile_tmp/{pyc_file}"
        print(pyc_file_src, pyc_file_dest)
        with open(pyc_file_src, "rb") as read, open(pyc_file_dest, "wb") as write:
            magic_ = read.read(4)
            if magic_ == magic[:4]:
                # print(f"{pyc_dir}/{main_file}已经存在文件头")
                pass
            else:
                write.write(magic)
            write.write(magic_)
            write.write(read.read())

    os.mkdir("py_result/other")
    for pyc_file in os.listdir("pycfile_tmp"):
        if pyc_file == main_file + ".pyc":
            continue
        sys.argv = ['uncompyle6', '-o',
                    f'py_result/other/{pyc_file[:-1]}', f'pycfile_tmp/{pyc_file}']
        uncompile.main_bin()

if __name__=="__main__":
    if len(sys.argv) < 2:
        print('[+] Usage: exe2py.py <filename>')
    exe2py(exe_file=sys.argv[1])
