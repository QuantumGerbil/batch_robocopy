# -*- coding: utf-8 -*-

import tkinter.messagebox as messagebox

class ExceptionHandler:
    """
    A class used to handle exceptions and display an error message to the user.
    """
    @staticmethod
    def handle_exception(e, title="Error"):
        """
        Handles the given exception by printing an error message and showing a message box with the error message.
        """
        print(f"{title}: {e}")
        messagebox.showerror(title, str(e))
