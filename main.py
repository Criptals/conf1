import argparse
import json
import os
import shutil
import sys
import tkinter as tk
from zipfile import ZipFile
import errno, stat


def handleRemoveReadonly(func, path, exc):
    excvalue = exc[1]
    if func in (os.rmdir, os.remove) and excvalue.errno == errno.EACCES:
        os.chmod(path, stat.S_IRWXU| stat.S_IRWXG| stat.S_IRWXO) # 0777
        func(path)
    else:
        raise


class Emulator:
    def __init__(self, filesystem: ZipFile, user: str):
        self.current_dir = "/"
        self.filesystem = filesystem
        self.user = user

        self.log = []

    def __del__(self):
        self.logger("exit", f"Closing filesystem...")
        self.filesystem.close()
        self.dump_log()

    def ls(self) -> str:
        output = ""
        for i in self.filesystem.namelist():
            if ("/" + i).startswith(self.current_dir):
                output = output + "/" + i + "\n"
        output = output.strip()

        self.logger("ls")
        return output

    def cd(self, command: str) -> str:
        try:
            path = command.split()[1]
        except IndexError:
            self.logger("cd", "Error: Provide additional arguments")

            return "cd: Provide additional arguments"

        files = ["/" + file for file in self.filesystem.namelist()]
        files.append("/")
        print(files)
        print(path)
        if path[0] != "/":
            # Relative
            to_path = self.current_dir + path
        else:
            # Absolute
            to_path = path
        if to_path != "/":
            to_path += "/"

        if to_path not in files:
            self.logger("cd", "Error: No such file or directory: " + to_path)
            output = "cd: No such file or directory: " + to_path
        elif to_path.removesuffix("/") in files:
            self.logger("cd", "Not a directory: " + to_path.removesuffix("/"))

            output = "cd: Not a directory: " + to_path.removesuffix("/")
        else:
            output = ""

            self.logger("cd", f"From: {self.current_dir} To: {to_path}")

            self.current_dir = to_path


        return output

    def chmod(self, command) -> str:
        try:
            new_permissions = command.split()[1]
            path_to_file = command.split()[2]
            if path_to_file[0] != "/":
                path_to_file = self.current_dir.removeprefix("/") + path_to_file
            path_to_file = path_to_file.removeprefix("/")
        except IndexError:
            self.logger("chown", f"Error: Provide additional arguments")

            return "chown: Provide additional arguments"

        output = ""

        self.logger("chown", f"File: {path_to_file} New permissions: {new_permissions}")

        self.filesystem.close()
        try:
            temp_dir = "tmp"
            # Извлечение файлов во временную директорию
            with ZipFile(self.filesystem.filename, 'w') as zip_ref:
                zip_ref.extractall(temp_dir)

            # Изменение атрибутов файла
            path_to_file = os.path.join(temp_dir, path_to_file)

            # Обновление атрибутов файла
            os.chmod(path_to_file, int(new_permissions, 8))

            # Создание нового архива с обновленными файлами
            new_archive_path = "updated_archive"
            shutil.make_archive(new_archive_path, 'zip', "tmp")
            # Удаление временной директории после завершения
            shutil.rmtree("tmp", ignore_errors=False, onerror=handleRemoveReadonly)

            name = self.filesystem.filename
            os.rmdir(name)
            os.rename("updated_archive.zip", name)
            self.filesystem = ZipFile(name, 'a')

        except KeyError:
             output = "Error reading a file: " + path_to_file
        return output

    def mv(self, command) -> str:
        try:
            old_path = command.split()[1]
            new_path = command.split()[2]
            if old_path[0] != "/":
                old_path = self.current_dir.removeprefix("/") + old_path
            old_path = old_path.removeprefix("/")

            if new_path[0] != "/":
                new_path = self.current_dir.removeprefix("/") + new_path
            new_path = new_path.removeprefix("/")
        except IndexError:
            self.logger("mv", f"Error: Provide additional arguments")
            return "mv: Provide additional arguments"


        output = ""

        self.logger("mv", f"File: {old_path} New path: {new_path}")

        self.filesystem.close()
        try:
            temp_dir = "tmp"
            # Извлечение файлов во временную директорию
            with ZipFile(self.filesystem.filename, 'r') as zip_ref:
                zip_ref.extractall(temp_dir)

            old_path = os.path.join(temp_dir, old_path)
            new_path = os.path.join(temp_dir, new_path)

            shutil.move(old_path, new_path)

            # Создание нового архива с обновленными файлами
            new_archive_path = "updated_archive"
            shutil.make_archive(new_archive_path, 'zip', "tmp")
            # Удаление временной директории после завершения
            shutil.rmtree("tmp", ignore_errors=False, onerror=handleRemoveReadonly)

            name = self.filesystem.filename
            os.remove(name)
            os.rename("updated_archive.zip", name)
            self.filesystem = ZipFile(name, 'a')
        except FileNotFoundError:
             output = "No such file or directory: " + new_path
        return output

    def pwd(self) -> str:
        output = self.current_dir
        self.logger("pwd", f"Current dir: {self.current_dir}")
        return output

    def command_parse(self, command: str) -> str:
        output = ""

        self.logger("command_parse", f"Parsing command: {command}")

        if command == 'ls':
            self.logger("command_parse", f"Detected command: ls")

            output = self.ls()

        elif command.split()[0] == "mv":
            self.logger("command_parse", f"Detected command: mv")

            output = self.mv(command)

        elif command.split()[0] == "cd":
            self.logger("command_parse", f"Detected command: cd")

            output = self.cd(command)

        elif command.split()[0] == "chmod":
            self.logger("command_parse", f"Detected command: chmod")

            output = self.chmod(command)

        elif command == "pwd":
            self.logger("command_parse", f"Detected command: pwd")

            output = self.pwd()

        elif command == "exit":
            self.logger("command_parse", f"Detected command: exit")
            self.logger("exit", f"Exiting...")

            self.dump_log()
            sys.exit()
        else:
            self.logger("command_parse", f"Detected unknown command")
            output = "Unknown command: " + command.split()[0]
        return output

    def dump_log(self):
        with open(parse_args().log, 'w') as f:
            json.dump(self.log, f, indent=2)

    def logger(self, command, message=""):
        log = {
            "user": self.user,
            "command": command
        }
        if message != "":
            log["message"] = message

        self.log.append(log)


class ConsoleText(tk.Text):
    def __init__(self, master=None, **kw):
        tk.Text.__init__(self, master, **kw)
        self.insert('1.0', '') # first prompt
        # create input mark
        self.mark_set('input', 'insert')
        self.mark_gravity('input', 'left')
        # create proxy
        self._orig = self._w + "_orig"
        self.tk.call("rename", self._w, self._orig)
        self.tk.createcommand(self._w, self._proxy)
        # binding to Enter key
        self.bind("<Return>", self.enter)

        args = parse_args()
        self.emulator = Emulator(ZipFile(args.archive, 'a'), args.user)
        self.setup()

    def setup(self):
        args = parse_args()

        self.display(f"Добро пожаловать в эмулятор, {args.user}\n$")

        # Execute startup script
        with open(args.script) as f:
            for line in f.readlines():
                self.display(line.strip())
                self.display(self.emulator.command_parse(line.strip()))

    def _proxy(self, *args):
        largs = list(args)

        if args[0] == 'insert':
            if self.compare('insert', '<', 'input'):
                # move insertion cursor to the editable part
                self.mark_set('insert', 'end')  # you can change 'end' with 'input'
        elif args[0] == "delete":
            if self.compare(largs[1], '<', 'input'):
                if len(largs) == 2:
                    return # don't delete anything
                largs[1] = 'input'  # move deletion start at 'input'
        result = self.tk.call((self._orig,) + tuple(largs))
        return result

    def enter(self, event):
        command = self.get('input', 'end').strip()
        output = self.emulator.command_parse(command)
        return self.display(output)

    def display(self, message):

        self.insert('end', f"\n{message}\n$ ")
        # move input mark
        self.mark_set('input', 'insert')
        return "break" # don't execute class method that inserts a newline


def parse_args():
    parser = argparse.ArgumentParser(description="Эмулятор командной строки")
    parser.add_argument('-u', '--user', required=True, help='Имя пользователя')
    parser.add_argument('-a', '--archive', required=True, help='Путь к архиву виртуальной файловой системы')
    parser.add_argument('-l', '--log', required=True, help='Путь к лог файлу')
    parser.add_argument('-s', '--script', required=True, help='Путь к стартовому скрипту')
    return parser.parse_args()


def lscheck():
    ot = ["/filesys/", "/filesys/bff/", "/filesys/vfg/", "/filesys/1.txt", "/filesys/2.txt", "/filesys/bff/3g4.txt",
          "/filesys/bff/sfv2.txt", "/filesys/vfg/conf.conf"]
    t = ""
    for i in ot:
        t = t + i + "\n"
    t = t.strip()
    print("Check ls: ", tfield.emulator.ls()==t)
def checkcd():
    tfield.emulator.cd("cd /filesys/bff")
    pw = tfield.emulator.pwd()
    print("Check cd: ", pw == "/filesys/bff/")
def checkmv():
    tfield.emulator.mv("mv /filesys/1.txt /filesys/bff")
    l = tfield.emulator.ls()
    ot = ["/filesys/", "/filesys/bff/", "/filesys/vfg/", "/filesys/2.txt", "/filesys/bff/1.txt", "/filesys/bff/3g4.txt",
          "/filesys/bff/sfv2.txt", "/filesys/vfg/conf.conf"]
    t = ""
    for i in ot:
        t = t + i + "\n"
    t = t.strip()
    print("Check ls: ", l == t)
    tfield.emulator.mv("mv /filesys/bff/1.txt /filesys")
    return 0


#def checkcmod():
#    return 0


if __name__ == "__main__":
    root = tk.Tk()
    tfield = ConsoleText(root, bg='gray10', fg='white', insertbackground='white')
    tfield.pack()
    #lscheck()
    #checkcd()
    #checkmv()
    root.mainloop()