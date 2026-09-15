from ui.app import MedCallApp
import time

if __name__ == "__main__":
    # print("Starting app...")

    app = MedCallApp()

    app.update()
    time.sleep(2)

    app.mainloop()