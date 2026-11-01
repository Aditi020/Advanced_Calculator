from interface import CalcApp

if __name__ == "__main__":
    app = CalcApp()
    try:
        app.mainloop()  # This tells Tkinter to keep the window open and listen for clicks/keys.
    except KeyboardInterrupt:
        print("\nExiting Calculator safely.")
        app.on_closing()