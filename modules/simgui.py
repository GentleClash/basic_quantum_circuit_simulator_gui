import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import json
import math
from modules.complex_ import Complex
from modules.circuit import QuantumCircuit
from modules.gates import QuantumGates
from typing import Any, Dict, List, Optional

type _matrix =  List[List[Complex]]
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


class QuantumSimulatorGUI:
    """Main GUI application"""
    def __init__(self, root) -> None:
        self.root = root
        self.root.title("Quantum Circuit Simulator")
        self.qubit_selection_mode = False
        self.selected_qubits = []
        self.pending_gate = None
        self.dragging_gate = None
        self.drag_offset_x = 0
        self.drag_offset_y = 0
        self.root.geometry("1400x800")
        
        # Circuit parameters
        self.circuit = QuantumCircuit(3)
        self.circuit_gates = []
        self.gate_buttons = {}
        self.selected_gate = None
        self.dragging_gate = None
        
        # Visual parameters
        self.zoom = 1.0
        self.wire_spacing = 80
        self.gate_width = 50
        self.gate_height = 40
        self.time_step_width = 100
        self.left_margin = 80
        self.top_margin = 80
        self.canvas_offset_x = 0
        self.canvas_offset_y = 0
        
        self.setup_ui()
        self.draw_circuit()
        self.update_results()

    def setup_ui(self) -> None:
        # Configure colors
        self.root.configure(bg='#f0f0f0')
        
        # Main container
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Left panel - Gate palette
        left_panel = ttk.Frame(main_frame, width=200)
        left_panel.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        
        ttk.Label(left_panel, text="Quantum Gates", font=('Arial', 14, 'bold')).pack(pady=10)
        
        # Single-qubit gates
        ttk.Label(left_panel, text="Single-Qubit Gates", font=('Arial', 10, 'bold')).pack(pady=5)
        single_gates = ['I', 'X', 'Y', 'Z', 'H', 'S', 'T']
        self.create_gate_buttons(left_panel, single_gates)
        
        # Two-qubit gates
        ttk.Label(left_panel, text="Two-Qubit Gates", font=('Arial', 10, 'bold')).pack(pady=5)
        two_gates = ['CNOT', 'CZ', 'SWAP']
        self.create_gate_buttons(left_panel, two_gates)
        
        # Three-qubit gates
        ttk.Label(left_panel, text="Three-Qubit Gates", font=('Arial', 10, 'bold')).pack(pady=5)
        three_gates = ['CCNOT']
        self.create_gate_buttons(left_panel, three_gates)
        
        # Measurement
        ttk.Label(left_panel, text="Measurement", font=('Arial', 10, 'bold')).pack(pady=5)
        self.create_gate_buttons(left_panel, ['M'])
        
        # Initial State Control
        ttk.Separator(left_panel, orient='horizontal').pack(fill=tk.X, pady=10)
        ttk.Label(left_panel, text="Initial State", font=('Arial', 10, 'bold')).pack(pady=5)
        ttk.Button(left_panel, text="Set Qubit States", 
                  command=self.open_state_dialog).pack(pady=5, fill=tk.X, padx=5)
        ttk.Button(left_panel, text="Reset to |0...0⟩", 
                  command=self.reset_initial_state).pack(pady=5, fill=tk.X, padx=5)
        
        # Center panel - Circuit canvas
        center_panel = ttk.Frame(main_frame)
        center_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.status_label = ttk.Label(center_panel, text="", 
                              font=('Arial', 12, 'bold'),
                              foreground='#ff6b6b')
        self.status_label.pack(pady=5)
        
        # Control buttons
        control_frame = ttk.Frame(center_panel)
        control_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(control_frame, text="+ Add Qubit", command=self.add_qubit).pack(side=tk.LEFT, padx=2)
        ttk.Button(control_frame, text="- Remove Qubit", command=self.remove_qubit).pack(side=tk.LEFT, padx=2)
        ttk.Button(control_frame, text="🔬 Simulate", command=self.simulate).pack(side=tk.LEFT, padx=2)
        ttk.Button(control_frame, text="🗑️ Clear", command=self.clear_circuit).pack(side=tk.LEFT, padx=2)
        ttk.Button(control_frame, text="💾 Export", command=self.export_circuit).pack(side=tk.LEFT, padx=2)
        ttk.Button(control_frame, text="📂 Import", command=self.import_circuit).pack(side=tk.LEFT, padx=2)
        
        # Zoom controls
        ttk.Label(control_frame, text="  Zoom:").pack(side=tk.LEFT, padx=(20, 5))
        ttk.Button(control_frame, text="+", command=self.zoom_in, width=3).pack(side=tk.LEFT, padx=2)
        ttk.Button(control_frame, text="-", command=self.zoom_out, width=3).pack(side=tk.LEFT, padx=2)
        ttk.Button(control_frame, text="Reset", command=self.zoom_reset, width=6).pack(side=tk.LEFT, padx=2)
        
        # Canvas with scrollbars
        canvas_frame = ttk.Frame(center_panel)
        canvas_frame.pack(fill=tk.BOTH, expand=True)
        
        self.h_scrollbar = ttk.Scrollbar(canvas_frame, orient=tk.HORIZONTAL)
        self.h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        
        self.v_scrollbar = ttk.Scrollbar(canvas_frame, orient=tk.VERTICAL)
        self.v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.canvas = tk.Canvas(canvas_frame, bg='white', 
                               xscrollcommand=self.h_scrollbar.set,
                               yscrollcommand=self.v_scrollbar.set)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.h_scrollbar.config(command=self.canvas.xview)
        self.v_scrollbar.config(command=self.canvas.yview)
        
        # Configure scrollregion
        self.update_scroll_region()
        
        # Canvas bindings
        self.canvas.bind('<Button-1>', self.on_canvas_click)
        self.canvas.bind('<B1-Motion>', self.on_canvas_drag)
        self.canvas.bind('<ButtonRelease-1>', self.on_canvas_release)
        self.canvas.bind('<Button-3>', self.on_canvas_right_click)
        
        # Right panel - Results
        right_panel = ttk.Frame(main_frame, width=300)
        right_panel.pack(side=tk.LEFT, fill=tk.Y, padx=(10, 0))
        
        ttk.Label(right_panel, text="Simulation Results", font=('Arial', 14, 'bold')).pack(pady=10)
        
        # Initial state display
        ttk.Label(right_panel, text="Initial State:", font=('Arial', 10, 'bold')).pack(pady=5)
        self.initial_state_text = tk.Text(right_panel, height=6, width=35, wrap=tk.WORD)
        self.initial_state_text.pack(pady=5)
        
        # State vector
        ttk.Label(right_panel, text="Final State Vector:", font=('Arial', 10, 'bold')).pack(pady=5)
        self.state_text = tk.Text(right_panel, height=8, width=35, wrap=tk.WORD)
        self.state_text.pack(pady=5)
        
        # Probabilities
        ttk.Label(right_panel, text="Measurement Probabilities:", font=('Arial', 10, 'bold')).pack(pady=5)
        
        # Create canvas for probabilities with scrollbar
        prob_canvas = tk.Canvas(right_panel, height=150)
        prob_scrollbar = ttk.Scrollbar(right_panel, orient="vertical", command=prob_canvas.yview)
        self.prob_frame = ttk.Frame(prob_canvas)
        
        self.prob_frame.bind(
            "<Configure>",
            lambda e: prob_canvas.configure(scrollregion=prob_canvas.bbox("all"))
        )
        
        prob_canvas.create_window((0, 0), window=self.prob_frame, anchor="nw")
        prob_canvas.configure(yscrollcommand=prob_scrollbar.set)
        
        prob_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        prob_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Circuit info
        info_frame = ttk.Frame(right_panel)
        info_frame.pack(pady=10)
        
        ttk.Label(info_frame, text="Circuit Info:", font=('Arial', 10, 'bold')).pack()
        self.info_text = tk.Text(info_frame, height=4, width=35)
        self.info_text.pack()
    
    def create_gate_buttons(self, parent, gates) -> None:
        frame = ttk.Frame(parent)
        frame.pack(fill=tk.X, pady=5)
        
        for gate in gates:
            btn = tk.Button(frame, text=gate, width=6, height=2,
                          bg='#667eea', fg='white', font=('Arial', 10, 'bold'),
                          relief=tk.RAISED, bd=2)
            btn.pack(side=tk.LEFT, padx=2)
            btn.bind('<Button-1>', lambda e, g=gate, b=btn: self.select_gate(g, b))
            self.gate_buttons[gate] = btn

            gate_info = QuantumGates.GATES.get(gate)
            if gate_info and 'description' in gate_info:
                ToolTip(btn, f"{gate_info['name']}\n{gate_info['description']}")

    
    def select_gate(self, gate_name, button) -> None:
        for btn in self.gate_buttons.values():
            btn.config(bg='#667eea', relief=tk.RAISED)
            
        button.config(bg='#ff6b6b', relief=tk.SUNKEN)
        self.selected_gate = gate_name

    def open_state_dialog(self) -> None:
        dialog = QubitStateDialog(self.root, self.circuit.num_qubits)
        self.root.wait_window(dialog)
        
        if dialog.result:
            self.circuit.set_initial_state(dialog.result)
            self.update_initial_state_display()
            messagebox.showinfo("Success", "Initial state has been set!")
    
    def reset_initial_state(self) -> None:
        self.circuit.initial_state = []
        self.circuit.state_vector = self.circuit.initialize_state()
        self.update_initial_state_display()
        self.update_results()
        messagebox.showinfo("Reset", "Initial state reset to |0...0⟩")

    def update_initial_state_display(self) -> None:
        self.initial_state_text.delete('1.0', tk.END)
        
        state = self.circuit.initialize_state()
        state_str = '|ψ₀⟩ = '
        first = True
        
        for i, amp in enumerate(state):
            if amp.magnitude() > 1e-10:
                if not first:
                    state_str += ' + '
                label = '|' + bin(i)[2:].zfill(self.circuit.num_qubits) + '⟩'
                state_str += f"{amp}{label}\n"
                first = False
        
        if first:
            state_str += '0'
        
        self.initial_state_text.insert('1.0', state_str)

    def update_scroll_region(self) -> None:
        width = int((self.left_margin + 20 * self.time_step_width) * self.zoom)
        height = int((self.top_margin + self.circuit.num_qubits * self.wire_spacing + 100) * self.zoom)
        self.canvas.config(scrollregion=(0, 0, width, height))

    def zoom_in(self) -> None:
        if self.zoom < 2.0:
            self.zoom *= 1.2
            self.draw_circuit()
            self.update_scroll_region()

    def zoom_out(self) -> None:
        if self.zoom > 0.3:
            self.zoom /= 1.2
            self.draw_circuit()
            self.update_scroll_region()

    def zoom_reset(self) -> None:
        self.zoom = 1.0
        self.draw_circuit()
        self.update_scroll_region()

    def draw_circuit(self) -> None:
        self.canvas.delete('all')
        
        # Apply zoom
        ws = int(self.wire_spacing * self.zoom)
        gw = int(self.gate_width * self.zoom)
        gh = int(self.gate_height * self.zoom)
        tsw = int(self.time_step_width * self.zoom)
        lm = int(self.left_margin * self.zoom)
        tm = int(self.top_margin * self.zoom)
        
        # Draw grid
        for t in range(20):
            x = lm + t * tsw
            self.canvas.create_line(x, tm - 20, x, tm + self.circuit.num_qubits * ws,
                                  fill='#f0f0f0', width=1)
        
        # Draw wires
        for q in range(self.circuit.num_qubits):
            y = tm + q * ws
            self.canvas.create_line(lm, y, lm + 20 * tsw, y, fill='#333', width=2)
            self.canvas.create_text(lm - 30, y, text=f'q{q}', font=('Arial', 12, 'bold'))

        if self.qubit_selection_mode and self.pending_gate:
            x = lm + self.pending_gate['time'] * tsw
            for selected_q in self.selected_qubits:
                y = tm + selected_q * ws
                # Draw highlight circle on selected qubits
                self.canvas.create_oval(x - 20, y - 20, x + 20, y + 20,
                                    outline='#ff6b6b', width=3, dash=(5, 5))
            
            # Draw instruction text
            gate_info = QuantumGates.GATES.get(self.pending_gate['name'])
            remaining = gate_info['qubits'] - len(self.selected_qubits) #type: ignore
            instruction = f"Placing {self.pending_gate['name']}: Select {remaining} more qubit(s)"
            self.canvas.create_text(lm + 10 * tsw, tm - 40,
                                text=instruction, fill='#ff6b6b',
                                font=('Arial', int(14 * self.zoom), 'bold'),
                                anchor='center')
        # Draw gates
        for gate in self.circuit_gates:
            self.draw_gate(gate, lm, tm, ws, gw, gh, tsw)

    def get_gate_horizontal_offset(self, gate) -> float:
        """Calculate horizontal offset for gates at same time to prevent overlap"""
        same_time_gates = [g for g in self.circuit_gates if g['time'] == gate['time']]
        if len(same_time_gates) <= 1:
            return 0
        
        # Sort by first qubit to determine order
        same_time_gates.sort(key=lambda g: min(g['qubits']))
        
        try:
            index = same_time_gates.index(gate)
            num_gates = len(same_time_gates)
            offset = (index - (num_gates - 1) / 2) * 0.15
            return offset
        except ValueError:
            return 0

    def draw_gate(self, gate, lm, tm, ws, gw, gh, tsw) -> None:
        x = lm + (gate['time'])* tsw 
        y = tm + gate['qubits'][0] * ws
        
        color = '#ff6b6b' if gate.get('selected', False) else '#667eea'
        
        if gate['gate'] in ['CNOT', 'CZ']:
            offset = self.get_gate_horizontal_offset(gate)
            x += offset * tsw
            self.draw_cnot_gate(gate, x, y, ws, color)
        elif gate['gate'] == 'SWAP':
            offset = self.get_gate_horizontal_offset(gate)
            x += offset * tsw
            self.draw_swap_gate(gate, x, y, ws)
        elif gate['gate'] == 'CCNOT':
            offset = self.get_gate_horizontal_offset(gate)
            x += offset * tsw
            self.draw_ccnot_gate(gate, x, y, ws)
        elif gate['gate'] == 'M':
            self.draw_measurement_gate(gate, x, y, gw, gh)
        else:
            # Single qubit gate
            self.canvas.create_rectangle(x - gw//2, y - gh//2, x + gw//2, y + gh//2,
                                        fill=color, outline='#333', width=2,
                                        tags=f"gate_{gate['id']}")
            self.canvas.create_text(x, y, text=gate['gate'], fill='white',
                                font=('Arial', int(12 * self.zoom), 'bold'))

    def draw_cnot_gate(self, gate, x, y, ws, color) -> None:
        control_y = y
        target_y = y + ws * (gate['qubits'][1] - gate['qubits'][0])
        
        # Connecting line
        self.canvas.create_line(x, control_y, x, target_y, fill='#333', width=2)
        
        # Control dot
        self.canvas.create_oval(x - 6, control_y - 6, x + 6, control_y + 6,
                               fill='#333', outline='#333')
        
        # Target circle
        r = int(15 * self.zoom)
        self.canvas.create_oval(x - r, target_y - r, x + r, target_y + r,
                               outline='#333', width=2, tags=f"gate_{gate['id']}")
        self.canvas.create_line(x - 10, target_y, x + 10, target_y, fill='#333', width=2)
        self.canvas.create_line(x, target_y - 10, x, target_y + 10, fill='#333', width=2)

    def draw_swap_gate(self, gate, x, y, ws) -> None:
        y1 = y
        y2 = y + ws * (gate['qubits'][1] - gate['qubits'][0])
        
        # Connecting line
        self.canvas.create_line(x, y1, x, y2, fill='#333', width=2)
        
        # X symbols
        size = int(8 * self.zoom)
        for yy in [y1, y2]:
            self.canvas.create_line(x - size, yy - size, x + size, yy + size,
                                   fill='#333', width=3, tags=f"gate_{gate['id']}")
            self.canvas.create_line(x + size, yy - size, x - size, yy + size,
                                   fill='#333', width=3)

    def draw_ccnot_gate(self, gate, x, y, ws) -> None:
        # Last qubit in the list is target, first two are controls
        qubits = gate['qubits']
        control1_qubit = qubits[0]
        control2_qubit = qubits[1]
        target_qubit = qubits[2]
        
        # Calculate actual y positions relative to the base y (first qubit's position)
        base_qubit = gate['qubits'][0]
        control1_y = y + ws * (control1_qubit - base_qubit)
        control2_y = y + ws * (control2_qubit - base_qubit)
        target_y = y + ws * (target_qubit - base_qubit)
        
        # Connecting line from topmost to bottommost
        min_y = min(control1_y, control2_y, target_y)
        max_y = max(control1_y, control2_y, target_y)
        self.canvas.create_line(x, min_y, x, max_y, fill='#333', width=2)
        
        # Control dots
        for cy in [control1_y, control2_y]:
            self.canvas.create_oval(x - 6, cy - 6, x + 6, cy + 6,
                                fill='#333', outline='#333')
        
        # Target
        r = int(15 * self.zoom)
        self.canvas.create_oval(x - r, target_y - r, x + r, target_y + r,
                            outline='#333', width=2, tags=f"gate_{gate['id']}")
        self.canvas.create_line(x - 10, target_y, x + 10, target_y, fill='#333', width=2)
        self.canvas.create_line(x, target_y - 10, x, target_y + 10, fill='#333', width=2)

    def draw_measurement_gate(self, gate, x, y, gw, gh) -> None:
        self.canvas.create_rectangle(x - gw//2, y - gh//2, x + gw//2, y + gh//2,
                                    fill='#ffd700', outline='#333', width=2,
                                    tags=f"gate_{gate['id']}")
        
        # Measurement symbol
        r = int(8 * self.zoom)
        self.canvas.create_arc(x - r, y - r//2, x + r, y + r//2,
                              start=180, extent=180, style=tk.ARC,
                              outline='#333', width=2)
        self.canvas.create_line(x, y, x + r, y - r, fill='#333', width=2)

    def on_canvas_click(self, event) -> None:
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)
        
        # Check if clicking on existing gate
        clicked_gate = self.get_gate_at_position(x, y)
        
        if clicked_gate:
            # Start dragging existing gate
            self.dragging_gate = clicked_gate
            lm = int(self.left_margin * self.zoom)
            tm = int(self.top_margin * self.zoom)
            ws = int(self.wire_spacing * self.zoom)
            tsw = int(self.time_step_width * self.zoom)
            
            gate_x = lm + clicked_gate['time'] * tsw
            gate_y = tm + clicked_gate['qubits'][0] * ws
            
            self.drag_offset_x = x - gate_x
            self.drag_offset_y = y - gate_y
            
        elif self.selected_gate:
            lm = int(self.left_margin * self.zoom)
            tm = int(self.top_margin * self.zoom)
            ws = int(self.wire_spacing * self.zoom)
            tsw = int(self.time_step_width * self.zoom)
            
            qubit = round((y - tm) / ws)
            time = round((x - lm) / tsw)
            
            if 0 <= qubit < self.circuit.num_qubits and time >= 0:
                gate_info = QuantumGates.GATES.get(self.selected_gate)
                if gate_info is None:
                    messagebox.showerror("Error", f"Unknown gate: {self.selected_gate}")
                    return
                
                if gate_info['qubits'] == 1: 
                    # Single qubit gate - place immediately
                    self.add_gate_to_circuit(self.selected_gate, qubit, time)
                else:
                    # Multi-qubit gate - start selection mode
                    if not self.qubit_selection_mode:
                        self.qubit_selection_mode = True
                        self.selected_qubits = [qubit]
                        self.pending_gate = {'name': self.selected_gate, 'time': time}
                        remaining = gate_info['qubits'] - 1
                        self.status_label.config(text=f"Select {remaining} more qubit(s) for {self.selected_gate}")
                        self.draw_circuit()  # Redraw to show highlight
                    else:
                        # Add qubit to selection
                        if qubit not in self.selected_qubits:
                            self.selected_qubits.append(qubit)
                            remaining = gate_info['qubits'] - len(self.selected_qubits)
                            if remaining > 0:
                                self.status_label.config(text=f"Select {remaining} more qubit(s) for {self.selected_gate}")
                            self.draw_circuit()  # Redraw to show new highlight
                        
                        # Check if we have enough qubits
                        if len(self.selected_qubits) == gate_info['qubits']:
                            self.add_gate_to_circuit(
                                self.pending_gate['name'], #type: ignore
                                self.selected_qubits, 
                                self.pending_gate['time'] #type: ignore
                            )
                            self.qubit_selection_mode = False
                            self.selected_qubits = []
                            self.pending_gate = None
                            self.status_label.config(text="")  # Clear status

    def on_canvas_right_click(self, event) -> None:
        # Remove gate at click position
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)
        
        for gate in self.circuit_gates[:]:
            gate_items = self.canvas.find_withtag(f"gate_{gate['id']}")
            for item in gate_items:
                bbox = self.canvas.bbox(item)
                if bbox and bbox[0] <= x <= bbox[2] and bbox[1] <= y <= bbox[3]:
                    self.circuit_gates.remove(gate)
                    self.draw_circuit()
                    self.update_circuit_info()
                    return

    def get_gate_at_position(self, x, y) -> Optional[Dict[str, Any]]:
        """Find gate at given canvas position"""
        lm = int(self.left_margin * self.zoom)
        tm = int(self.top_margin * self.zoom)
        ws = int(self.wire_spacing * self.zoom)
        tsw = int(self.time_step_width * self.zoom)
        gw = int(self.gate_width * self.zoom)
        gh = int(self.gate_height * self.zoom)
        
        for gate in self.circuit_gates:
            gate_x = lm + gate['time'] * tsw
            
            # For multi-qubit gates, check all qubits
            for qubit in gate['qubits']:
                gate_y = tm + qubit * ws
                
                # Larger hit box for easier clicking
                hit_margin = 10
                if (gate_x - gw//2 - hit_margin <= x <= gate_x + gw//2 + hit_margin and 
                    gate_y - gh//2 - hit_margin <= y <= gate_y + gh//2 + hit_margin):
                    return gate
        
        return None

    def on_canvas_drag(self, event) -> None:
        if self.dragging_gate:
            x = self.canvas.canvasx(event.x)
            y = self.canvas.canvasy(event.y)
            
            lm = int(self.left_margin * self.zoom)
            tm = int(self.top_margin * self.zoom)
            ws = int(self.wire_spacing * self.zoom)
            tsw = int(self.time_step_width * self.zoom)
            
            # Calculate offset from first qubit
            first_qubit = self.dragging_gate['qubits'][0]
            qubit_offsets = [q - first_qubit for q in self.dragging_gate['qubits']]
            
            # Calculate new position for first qubit
            new_first_qubit = round((y - tm - self.drag_offset_y) / ws)
            new_time = max(0, round((x - lm - self.drag_offset_x) / tsw))
            
            # Apply offsets to get new qubit positions
            new_qubits = [new_first_qubit + offset for offset in qubit_offsets]
            
            # Validate all qubits are within bounds and no collision
            if all(0 <= q < self.circuit.num_qubits for q in new_qubits):
                if not self.check_gate_collision(new_qubits, new_time, self.dragging_gate['id']):
                    self.dragging_gate['qubits'] = new_qubits
                    self.dragging_gate['time'] = new_time
                    self.draw_circuit()

    def on_canvas_release(self, event) -> None:
        """Handle mouse button release"""
        self.dragging_gate = None
        self.update_circuit_info()
    
    def check_gate_collision(self, qubits, time, exclude_gate_id=None) -> bool:
        """Check if placing a gate would collide with existing gates"""
        for gate in self.circuit_gates:
            if exclude_gate_id and gate['id'] == exclude_gate_id:
                continue
            if gate['time'] == time:
                # Check if any qubits overlap
                if set(qubits) & set(gate['qubits']):
                    return True
        return False

    def add_gate_to_circuit(self, gate_name, qubits, time) -> None:
        gate_info = QuantumGates.GATES.get(gate_name)
        if not gate_info:
            return
        
        # Ensure qubits is a list
        if isinstance(qubits, int):
            qubits = [qubits]
        
        # Validate qubit count
        if len(qubits) != gate_info['qubits']:
            messagebox.showwarning("Invalid Placement", 
                f"{gate_name} requires {gate_info['qubits']} qubit(s)")
            return
        
        # Check for collision
        if self.check_gate_collision(qubits, time):
            messagebox.showwarning("Invalid Placement", 
                "A gate already exists at this position")
            return
        
        gate = {
            'id': len(self.circuit_gates) + 1,
            'gate': gate_name,
            'qubits': qubits,
            'time': time,
            'selected': False
        }
        
        self.circuit_gates.append(gate)
        if gate_name in self.gate_buttons:
            self.gate_buttons[gate_name].config(bg='#667eea', relief=tk.RAISED)
        self.selected_gate = None
        self.draw_circuit()
        self.update_circuit_info()

    def add_qubit(self) -> None:
        if self.circuit.num_qubits < 10:
            self.circuit.num_qubits += 1
            self.circuit = QuantumCircuit(self.circuit.num_qubits)
            self.draw_circuit()
            self.update_scroll_region()
            self.update_circuit_info()
            self.update_initial_state_display()

    def remove_qubit(self) -> None:
        if self.circuit.num_qubits > 1:
            self.circuit_gates = [g for g in self.circuit_gates 
                                 if max(g['qubits']) < self.circuit.num_qubits - 1]
            self.circuit.num_qubits -= 1
            self.circuit = QuantumCircuit(self.circuit.num_qubits)
            self.draw_circuit()
            self.update_scroll_region()
            self.update_circuit_info()
            self.update_initial_state_display()

    def simulate(self) -> None:
        # Preserve initial state if set
        temp_circuit = QuantumCircuit(self.circuit.num_qubits)
        if self.circuit.initial_state is not None:
            temp_circuit.set_initial_state(self.circuit.initial_state)
        
        for gate in self.circuit_gates:
            temp_circuit.add_gate(gate['gate'], gate['qubits'], gate['time'])

        try:
            results, measurement_results = temp_circuit.simulate()
            
            # Update display circuit
            self.circuit = temp_circuit
            self.update_results()
            
            # Show measurement results if any
            if measurement_results:
                msg = "Measurement Results:\n"
                for qubit, result in sorted(measurement_results.items()):
                    msg += f"q{qubit}: |{result}⟩\n"
                messagebox.showinfo("Simulation Complete", msg)
            else:
                messagebox.showinfo("Simulation", "Circuit simulation completed!")
        except IndexError as e:
            messagebox.showerror("Simulation Error", f"Please set initial states for all qubits.")

        except Exception as e:
            messagebox.showerror("Simulation Error", f"Error during simulation:\n{str(e)}")

    def update_results(self) -> None:
        results = self.circuit.get_results()
        if isinstance(results, tuple):
            results, _ = results

        # Update state vector
        self.state_text.delete('1.0', tk.END)
        state_str = '|ψ⟩ = '
        first = True
        
        for i, amp in enumerate(results['state_vector']):
            if results['probabilities'][i] > 1e-10:
                if not first:
                    state_str += ' + '
                state_str += f"{amp}{results['state_labels'][i]}\n"
                first = False
        
        if first:
            state_str += '0'
        
        self.state_text.insert('1.0', state_str)
        
        # Update initial state display
        self.update_initial_state_display()
        
        # Update probabilities
        for widget in self.prob_frame.winfo_children():
            widget.destroy()
        
        for i, prob in enumerate(results['probabilities']):
            if prob > 1e-10:
                frame = ttk.Frame(self.prob_frame)
                frame.pack(fill=tk.X, pady=2)
                
                label = ttk.Label(frame, text=f"{results['state_labels'][i]}:")
                label.pack(side=tk.LEFT)
                
                canvas = tk.Canvas(frame, height=20, width=150, bg='#e9ecef')
                canvas.pack(side=tk.LEFT, padx=5)
                
                bar_width = int(150 * prob)
                canvas.create_rectangle(0, 0, bar_width, 20, fill='#28a745', outline='')
                
                percent_label = ttk.Label(frame, text=f"{prob*100:.1f}%")
                percent_label.pack(side=tk.LEFT)

    def update_circuit_info(self) -> None:
        max_time = max([g['time'] for g in self.circuit_gates], default=0) + 1 if self.circuit_gates else 0
        
        info_str = f"Qubits: {self.circuit.num_qubits}\n"
        info_str += f"Gates: {len(self.circuit_gates)}\n"
        info_str += f"Depth: {max_time}\n"
        info_str += f"Zoom: {self.zoom:.2f}x"
        
        self.info_text.delete('1.0', tk.END)
        self.info_text.insert('1.0', info_str)
    
    def clear_circuit(self) -> None:
        self.circuit_gates = []
        temp_initial = self.circuit.initial_state
        self.circuit = QuantumCircuit(self.circuit.num_qubits)
        if temp_initial is not None:
            self.circuit.set_initial_state(temp_initial)
        self.draw_circuit()
        self.update_results()
        self.update_circuit_info()

    def export_circuit(self) -> None:
        filename = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if filename:
            # Convert initial state to serializable format
            initial_state_data = None
            if self.circuit.initial_state is not None:
                initial_state_data = [[amp.r, amp.i] for amp in self.circuit.initial_state]
            
            circuit_data = {
                'num_qubits': self.circuit.num_qubits,
                'gates': self.circuit_gates,
                'initial_state': initial_state_data
            }
            
            with open(filename, 'w') as f:
                json.dump(circuit_data, f, indent=2)
            
            messagebox.showinfo("Export", "Circuit exported successfully!")

    def import_circuit(self) -> None:
        filename = filedialog.askopenfilename(
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                with open(filename, 'r') as f:
                    circuit_data = json.load(f)
                
                self.circuit = QuantumCircuit(circuit_data['num_qubits'])
                
                # Restore initial state if present
                if circuit_data.get('initial_state'):
                    initial_state = [Complex(amp[0], amp[1]) for amp in circuit_data['initial_state']]
                    self.circuit.set_initial_state(initial_state)
                
                self.circuit_gates = circuit_data.get('gates', [])
                self.draw_circuit()
                self.update_scroll_region()
                self.update_circuit_info()
                self.update_initial_state_display()
                
                messagebox.showinfo("Import", "Circuit imported successfully!")
            except Exception as e:
                messagebox.showerror("Import Error", f"Failed to import circuit:\n{str(e)}")
