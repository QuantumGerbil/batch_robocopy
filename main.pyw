# -*- coding: utf-8 -*-
"""
Created on Tue Feb 13 10:23:08 2024
"""
import os
import subprocess
import uuid
import threading
import tkinter as tk
import tkinter.ttk as ttk
from tkinter import filedialog
from exception import ExceptionHandler
from timer import Timer
from csvfile import CSVFile
import win32api
import win32con
import win32file
import ctypes


class CopyWorker:
    """
    A class that represents a worker that copies files.
    """
    EXIT_CODES = {
        0: ("No Change", True, ValueError),
        1: ("OKCOPY", False, None),
        2: ("XTRA", False, None),
        3: ("OKCOPY + XTRA", False, None),
        4: ("MISMATCHES", True, ValueError),
        5: ("OKCOPY + MISMATCHES", True, ValueError),
        6: ("MISMATCHES + XTRA", True, ValueError),
        7: ("OKCOPY + MISMATCHES + XTRA", True, ValueError),
        8: ("FAIL", True, ValueError),
        9: ("OKCOPY + FAIL", False, None),
        10: ("FAIL + XTRA", True, ValueError),
        11: ("OKCOPY + FAIL + XTRA", False, None),
        12: ("FAIL + MISMATCHES", True, ValueError),
        13: ("OKCOPY + FAIL + MISMATCHES", True, ValueError),
        14: ("FAIL + MISMATCHES + XTRA", True, ValueError),
        15: ("OKCOPY + FAIL + MISMATCHES + XTRA", True, ValueError),
        16: ("***FATAL ERROR***", True, ValueError)
    }
    
    def __init__(self, name):
        """
        Initializes a new instance of the CopyWorker class.
        """
        self.timer = Timer()
        self.name = name
        self.source = tk.StringVar()
        self.destination = tk.StringVar()
        self.content = tk.StringVar()
        self.location = tk.StringVar()
        self.UUID = None
        self.timestamp = None
        self.csvFile = None
        self.classification = tk.StringVar()
        self.eject_on_completion = tk.BooleanVar()
        self.robocopy = "/j /e /R:1 /W:5 /v"
        
    def get_directory_size(self, directory):
        print(f"{self.name}: Calculating transfer size")
        total = 0
        for path, dirs, files in os.walk(directory):
            for f in files:
                fp = os.path.join(path, f)
                total += os.path.getsize(fp)
        units = ['bytes', 'KB', 'MB', 'GB', 'TB', 'PB']
        index = 0
        while total > 1024 and index < len(units) - 1:
            total /= 1024
            index += 1
        self.filesize = round(total, 2)
        print(f"{self.name}: {self.filesize} {units[index]}")

    def copy_data(self, source, destination):
        """
        Copies data from the source directory to the destination directory.
        """
        command = f'robocopy {source} {destination} {self.robocopy} /log+:{destination}\log.txt'
        #command = f'start-process powershell robocopy {source} {destination} {self.robocopy}'
        if not os.path.exists(source):
            raise ValueError("Source directory does not exist.")
        try:
            self.timer.start()
            process = subprocess.run(command, shell=True)
            #process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            #stdout, stderr = process.communicate()
            self.handle_exit_code(process.returncode)
        except Exception as e:
            print(f"Error copying files: {e}")
        finally: self.timer.stop()
            
    def handle_exit_code(self, exit_code):
        """
        Handles the exit code of the copy command.
        """
        message, stop_timer, exception_class = self.EXIT_CODES.get(exit_code, ("Unknown exit code", True, ValueError))
        print(f'{self.name}: Exit Code:{exit_code} - {message}')
        if stop_timer:
            self.timer.stop()
        if exception_class is not None:
            raise exception_class(message)
            
    def finalize_destination(self):
        """
        Finalizes the destination directory.
        """
        # Generate UUID
        self.UUID = str(uuid.uuid5(uuid.NAMESPACE_DNS, self.source.get() + self.destination.get() + self.location.get() + self.content.get()))
        # Create destination directory
        self.full_destination = os.path.join(self.destination.get(), self.UUID)
        try:
            os.makedirs(self.full_destination, exist_ok=True)
        except OSError as e:
            ExceptionHandler.handle_exception(e, "Error creating directory")
            
    def write_to_csv(self):
        self.csvFile.write_to_csv(self.classification.get(), self.location.get(), self.content.get(), self.UUID, self.timer.elapsed_time())
            
    def eject(self):
        drive = self.source.get()
        if drive == "A:\\" or drive == "B:\\":
            print ("Eject Floppy disks manually")
        else:
            print(f"Eject drive: {drive}")
            ctypes.windll.winmm.mciSendStringW(f"open {drive} type cdaudio alias drive", None, 0, None)
            ctypes.windll.winmm.mciSendStringW("set drive door open", None, 0, None)
        
class FileCopyApp:
    """
    A class that represents a file copy application.
    """
    def __init__(self):
        """
        Initializes a new instance of the FileCopyApp class.
        """
        self.window = tk.Tk()
        self.window.title('File Copy App')
        
        # Create a menubar
        self.menubar = tk.Menu(self.window)
        self.window.config(menu=self.menubar)
        
        self.menubar.add_command(label="Add Worker", command=self.add_worker)
        self.menubar.add_command(label="Remove Worker", command=self.remove_worker)

        self.workers_frame = tk.Frame(self.window)
        self.workers_frame.pack()
        
        #self.robocopy_frame = tk.Frame(self.window)
        #self.robocopy_frame.pack()
        
        self.tree = ttk.Treeview(self.window)
        self.tree["columns"] = ("Source", "Destination")
        self.tree.column("#0", width=100)
        self.tree.column("Source", width=150)
        self.tree.column("Destination", width=150)
        self.tree.heading("#0", text="Worker")
        self.tree.heading("Source", text="Source Directory")
        self.tree.heading("Destination", text="Destination Directory")
        self.tree.pack()
        
        self.workers = []
        self.frames = []

    def run(self):
        """
        Runs the application.
        """
        self.window.mainloop()
        
    def get_directory(self):
        """
        Gets a directory selected by the user.
        """
        directory = filedialog.askdirectory()
        return directory if directory else "Select Directory"
    
    def select_source_folder(self, worker):
        """
        Selects the source folder.
        """
        directory = self.get_directory()
        print(f"Drive available: {worker.testDrive(directory)}")
        worker.source.set(directory)

    def select_destination_folder(self, destination_entry, worker):
        """
        Selects the destination folder.
        """
        directory = self.get_directory()
        if directory and os.path.isdir(directory):
            worker.destination.set(directory)
            worker.csvFile = CSVFile(directory, 'README.csv')
        else:
            raise ValueError("Invalid directory selected.")

    def add_worker(self):
        """
        Adds a worker.
        """
        worker = CopyWorker(f"Worker {len(self.workers) + 1}")
        self.workers.append(worker)
        
        # Calculate the row and column for the new worker
        row = (len(self.workers) - 1) % 5
        column = (len(self.workers) - 1) // 5

        frame = tk.LabelFrame(self.workers_frame, text=f"Worker {len(self.workers)}", padx=5, pady=5)
        frame.grid(row=row, column=column, padx=10, pady=10)
        
        # Add a dropdown menu for removable drives
        removable_drives = tk.StringVar(frame)
        removable_drives.set("Select Drive")
        drives_dropdown = tk.OptionMenu(frame, worker.source, *self.get_removable_drives())
        drives_dropdown.grid(row=0, column=0)
        
        def eject_toggle(*args):
            if worker.source.get() == "A:\\" or worker.source.get() == "B:\\":
                eject_button.config(state=tk.DISABLED)
            else:
                eject_button.config(state=tk.NORMAL)
        
        worker.source.trace("w", eject_toggle)

        #source_entry = tk.Entry(frame, textvariable=worker.source)
        destination_entry = tk.Entry(frame, textvariable=worker.destination)
        physical_location_entry = tk.Entry(frame, textvariable=worker.location)
        content_entry = tk.Entry(frame, textvariable=worker.content)
        classification_entry = tk.Entry(frame, textvariable=worker.classification)
        classification_entry.insert(0, "UNCLASS")

        #source_button = tk.Button(frame, text="Select Source", command=lambda: self.select_source_folder(worker))
        destination_button = tk.Button(frame, text="Select Destination", command=lambda: self.select_destination_folder(destination_entry, worker))

        '''source_button.grid(row=0, column=0)
        source_entry.grid(row=0, column=1)'''
        destination_button.grid(row=0, column=2)
        destination_entry.grid(row=0, column=3)

        tk.Label(frame, text='Physical Location:').grid(row=1, column=0)
        physical_location_entry.grid(row=1, column=1)
        tk.Label(frame, text='Content:').grid(row=1, column=2)
        content_entry.grid(row=1, column=3)
        
        tk.Label(frame, text='Classification:').grid(row=2, column=0)
        classification_entry.grid(row=2, column=1)
        
        eject_button = tk.Button(frame, text='Eject Drive', command=worker.eject)
        eject_button.grid(row=2, column=3)
        
        copy_button = tk.Button(frame, text='Copy', command=lambda: self.copy_files_for_worker(worker, copy_button, eject_button, drives_dropdown, destination_button, destination_entry, classification_entry, physical_location_entry, content_entry))
        copy_button.grid(row=2, column=2)
        
        self.frames.append(frame)
        
        
    def get_removable_drives(self):
        """Returns a list of all removable drives on the system."""
        drives = []
        for drive in win32api.GetLogicalDriveStrings().split('\000'):
            drive_type = win32file.GetDriveType(drive)
            if drive_type != win32con.DRIVE_FIXED and drive_type != win32con.DRIVE_REMOTE:
                drives.append(drive)
        return drives

    def remove_worker(self):
        if self.workers:
            self.workers.pop()
            frame = self.frames.pop()
            frame.destroy()
        
    def copy_files_for_worker(self, worker, copy_button, eject_button, drives_dropdown, destination_button, destination_entry, classification_entry, physical_location_entry, content_entry):
        copy_button.config(state=tk.DISABLED)
        eject_button.config(state=tk.DISABLED)
        drives_dropdown.config(state=tk.DISABLED)
        destination_button.config(state=tk.DISABLED)
        destination_entry.config(state=tk.DISABLED)
        classification_entry.config(state=tk.DISABLED)
        physical_location_entry.config(state=tk.DISABLED)
        content_entry.config(state=tk.DISABLED)
        #worker.get_directory_size(worker.source.get())
        item_id = self.tree.insert("", "end", text=worker.name, values=(worker.source.get(), worker.destination.get()))
        threading.Thread(target=self.copy_files_thread_for_worker, args=(worker, copy_button, eject_button, drives_dropdown, destination_button, destination_entry, classification_entry, physical_location_entry, content_entry, item_id)).start()

    def copy_files_thread_for_worker(self, worker, copy_button, eject_button, drives_dropdown, destination_button, destination_entry, classification_entry, physical_location_entry, content_entry, item_id):
        print(f"--Started Copy Job for {worker.name}--")
        try:
            worker.finalize_destination()
            worker.copy_data(worker.source.get(), worker.full_destination)
            worker.write_to_csv()
            print(f"--Finished Copy Job for {worker.name}--")
        except ValueError as e:
            print(f"Error copying files: {e}")
        except Exception as e:
            print(f"Error copying files: {e}")
        finally:
            copy_button.config(state=tk.NORMAL)
            eject_button.config(state=tk.NORMAL)
            drives_dropdown.config(state=tk.NORMAL)
            destination_button.config(state=tk.NORMAL)
            destination_entry.config(state=tk.NORMAL)
            classification_entry.config(state=tk.NORMAL)
            physical_location_entry.config(state=tk.NORMAL)
            content_entry.config(state=tk.NORMAL)
            self.tree.delete(item_id)      

if __name__ == "__main__":
    app = FileCopyApp()
    app.run()
