"""
The entry point for the application. 
Run this file to start the calculator.
"""
from interface import CalcApp

if __name__ == "__main__":
    app = CalcApp()
    app.mainloop() # This tells Tkinter to keep the window open and listen for clicks/keys.