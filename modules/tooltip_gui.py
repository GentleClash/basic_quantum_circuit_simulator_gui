from modules.complex_ import Complex
from typing import List
import tkinter as tk
from tkinter import ttk, messagebox
import math

type _state_vector = List[Complex]

class ToolTip:
    def __init__(self, widget, text) -> None:
        self.widget = widget
        self.text = text
        self.tip_window = None
        self.schedule_id = None
        self.widget.bind('<Enter>', self.schedule_tip)
        self.widget.bind('<Leave>', self.hide_tip)
    
    def schedule_tip(self, event=None) -> None:
        self.hide_tip()
        self.schedule_id = self.widget.after(500, self.show_tip) 

    def show_tip(self, event=None) -> None:
        if self.tip_window or not self.text:
            return
        
        x = self.widget.winfo_rootx() + self.widget.winfo_width() + 5
        y = self.widget.winfo_rooty() + 5
        
        self.tip_window = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        
        label = tk.Label(tw, text=self.text, justify=tk.LEFT,
                        background="#ffffe0", relief=tk.SOLID, borderwidth=1,
                        font=("Arial", 9), padx=5, pady=3)
        label.pack()

    def hide_tip(self, event=None) -> None:
        if self.schedule_id:
            self.widget.after_cancel(self.schedule_id)
            self.schedule_id = None
        if self.tip_window:
            self.tip_window.destroy()
            self.tip_window = None

class QubitStateDialog(tk.Toplevel):
    """Dialog for setting individual qubit states"""
    def __init__(self, parent, num_qubits) -> None:
        super().__init__(parent)
        self.title("Set Qubit States")
        self.num_qubits = num_qubits
        self.result = None
        
        self.geometry("500x600")
        self.transient(parent)
        self.grab_set()
        
        # Instructions
        ttk.Label(self, text="Set Individual Qubit States", 
                 font=('Arial', 14, 'bold')).pack(pady=10)
        ttk.Label(self, text="For each qubit, set |0⟩ and |1⟩ amplitudes (real + imag*i)",
                 font=('Arial', 9)).pack(pady=5)
        
        # Scrollable frame
        canvas = tk.Canvas(self)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        self.qubit_entries = []
        
        for q in range(num_qubits):
            frame = ttk.LabelFrame(scrollable_frame, text=f"Qubit q{q}", padding=10)
            frame.pack(fill=tk.X, padx=10, pady=5)
            
            # |0⟩ amplitude
            ttk.Label(frame, text="|0⟩ amplitude:").grid(row=0, column=0, sticky=tk.W)
            real0 = ttk.Entry(frame, width=10)
            real0.insert(0, "1" if q == 0 else "0")
            real0.grid(row=0, column=1, padx=2)
            ttk.Label(frame, text="+").grid(row=0, column=2)
            imag0 = ttk.Entry(frame, width=10)
            imag0.insert(0, "0")
            imag0.grid(row=0, column=3, padx=2)
            ttk.Label(frame, text="i").grid(row=0, column=4)
            
            # |1⟩ amplitude
            ttk.Label(frame, text="|1⟩ amplitude:").grid(row=1, column=0, sticky=tk.W, pady=(5,0))
            real1 = ttk.Entry(frame, width=10)
            real1.insert(0, "0")
            real1.grid(row=1, column=1, padx=2, pady=(5,0))
            ttk.Label(frame, text="+").grid(row=1, column=2, pady=(5,0))
            imag1 = ttk.Entry(frame, width=10)
            imag1.insert(0, "0")
            imag1.grid(row=1, column=3, padx=2, pady=(5,0))
            ttk.Label(frame, text="i").grid(row=1, column=4, pady=(5,0))
            
            # Preset buttons
            preset_frame = ttk.Frame(frame)
            preset_frame.grid(row=2, column=0, columnspan=5, pady=(10,0))
            
            ttk.Button(preset_frame, text="|0⟩", 
                      command=lambda r0=real0, i0=imag0, r1=real1, i1=imag1: 
                      self.set_preset(r0, i0, r1, i1, "0")).pack(side=tk.LEFT, padx=2)
            ttk.Button(preset_frame, text="|1⟩", 
                      command=lambda r0=real0, i0=imag0, r1=real1, i1=imag1: 
                      self.set_preset(r0, i0, r1, i1, "1")).pack(side=tk.LEFT, padx=2)
            ttk.Button(preset_frame, text="|+⟩", 
                      command=lambda r0=real0, i0=imag0, r1=real1, i1=imag1: 
                      self.set_preset(r0, i0, r1, i1, "+")).pack(side=tk.LEFT, padx=2)
            ttk.Button(preset_frame, text="|-⟩", 
                      command=lambda r0=real0, i0=imag0, r1=real1, i1=imag1: 
                      self.set_preset(r0, i0, r1, i1, "-")).pack(side=tk.LEFT, padx=2)
            
            self.qubit_entries.append({
                'real0': real0, 'imag0': imag0,
                'real1': real1, 'imag1': imag1
            })
        
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Buttons
        btn_frame = ttk.Frame(self)
        btn_frame.pack(pady=10)
        
        ttk.Button(btn_frame, text="Apply", command=self.apply).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Reset to |0...0⟩", command=self.reset).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Cancel", command=self.cancel).pack(side=tk.LEFT, padx=5)
    
    def set_preset(self, real0, imag0, real1, imag1, preset) -> None:
        presets = {
            "0": ("1", "0", "0", "0"),
            "1": ("0", "0", "1", "0"),
            "+": (str(1/math.sqrt(2)), "0", str(1/math.sqrt(2)), "0"),
            "-": (str(1/math.sqrt(2)), "0", str(-1/math.sqrt(2)), "0")
        }
        
        if preset in presets:
            r0, i0, r1, i1 = presets[preset]
            real0.delete(0, tk.END)
            real0.insert(0, r0)
            imag0.delete(0, tk.END)
            imag0.insert(0, i0)
            real1.delete(0, tk.END)
            real1.insert(0, r1)
            imag1.delete(0, tk.END)
            imag1.insert(0, i1)

    def apply(self) -> None:
        try:
            # Parse all qubit states
            qubit_states = []
            for entries in self.qubit_entries:
                r0_str = entries['real0'].get().strip()
                i0_str = entries['imag0'].get().strip()
                r1_str = entries['real1'].get().strip()
                i1_str = entries['imag1'].get().strip()
                
                # Default to |0⟩ state if all fields are empty
                if not r0_str and not i0_str and not r1_str and not i1_str:
                    r0, i0, r1, i1 = 1.0, 0.0, 0.0, 0.0
                else:
                    # Parse with default values of 0 for empty fields
                    r0 = float(r0_str) if r0_str else 0.0
                    i0 = float(i0_str) if i0_str else 0.0
                    r1 = float(r1_str) if r1_str else 0.0
                    i1 = float(i1_str) if i1_str else 0.0

                # Normalize
                norm = math.sqrt(r0*r0 + i0*i0 + r1*r1 + i1*i1)
                if norm < 1e-10:
                    raise ValueError("State cannot be zero")
                
                qubit_states.append([
                    Complex(r0/norm, i0/norm),
                    Complex(r1/norm, i1/norm)
                ])
            
            # Compute tensor product
            result: _state_vector = [Complex(1, 0)]
            
            for qubit_state in qubit_states:
                new_result = []
                for amp in result:
                    for qubit_amp in qubit_state:
                        new_result.append(amp.multiply(qubit_amp))
                result = new_result
            
            self.result = result
            self.destroy()
            
        except ValueError as e:
            messagebox.showerror("Invalid Input", f"Please enter valid numbers:\n{str(e)}")

    def reset(self) -> None:
        # Reset UI fields
        for i, entries in enumerate(self.qubit_entries):
            entries['real0'].delete(0, tk.END)
            entries['real0'].insert(0, "1" if i == 0 else "0")
            entries['imag0'].delete(0, tk.END)
            entries['imag0'].insert(0, "0")
            entries['real1'].delete(0, tk.END)
            entries['real1'].insert(0, "0")
            entries['imag1'].delete(0, tk.END)
            entries['imag1'].insert(0, "0")
        
        # Actually apply the reset state (|0...0⟩)
        self.apply()

    def cancel(self) -> None:
        self.result = None
        self.destroy()
