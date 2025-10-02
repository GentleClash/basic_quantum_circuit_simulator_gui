import tkinter as tk
from modules.simgui import QuantumSimulatorGUI


def main() -> None:
    root = tk.Tk()
    app = QuantumSimulatorGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()