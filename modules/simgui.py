import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import json
from modules.tooltip_gui import ToolTip, QubitStateDialog
from modules.complex_ import Complex
from modules.circuit import QuantumCircuit
from modules.gates import QuantumGates
from typing import Any, Dict, List, Optional

type _matrix =  List[List[Complex]]
type _state_vector = List[Complex]

class QuantumSimulatorGUI:
    """Main GUI application"""
    def __init__(self, root, time_steps=30) -> None:
        self.root = root
        self.root.title("Quantum Circuit Simulator")
        self.qubit_selection_mode = False
        self.selected_qubits = []
        self.pending_gate = None
        self.dragging_gate = None
        self.drag_offset_x = 0
        self.drag_offset_y = 0
        self.prob_maximized = False
        self.maximize_window = None
        self.time_steps = time_steps
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
        prob_header_frame = ttk.Frame(right_panel)
        prob_header_frame.pack(pady=5, fill=tk.X)
        ttk.Label(prob_header_frame, text="Measurement Probabilities:", font=('Arial', 10, 'bold')).pack(side=tk.LEFT)
        maximize_btn = ttk.Button(prob_header_frame, text="⤢", width=3, command=self.toggle_maximize_probabilities)
        maximize_btn.pack(side=tk.RIGHT)
        ToolTip(maximize_btn, "Maximize probability view")

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

    def maximize_zoom_in(self) -> None:
        if self.maximize_zoom < 2.0:
            self.maximize_zoom *= 1.2
            self.draw_circuit_on_maximize_canvas()

    def maximize_zoom_out(self) -> None:
        if self.maximize_zoom > 0.3:
            self.maximize_zoom /= 1.2
            self.draw_circuit_on_maximize_canvas()

    def maximize_zoom_reset(self) -> None:
        self.maximize_zoom = 0.7
        self.draw_circuit_on_maximize_canvas()

    def toggle_maximize_probabilities(self) -> None:
        """Toggle maximized view of probabilities with circuit canvas"""
        if self.prob_maximized:
            # Close maximize window if open
            if self.maximize_window:
                self.maximize_window.destroy()
                self.maximize_window = None
            self.prob_maximized = False
        else:
            # Create maximize window
            self.maximize_window = tk.Toplevel(self.root)
            self.maximize_window.title("Probability Distribution")
            self.maximize_window.geometry("1200x800")

            # Store current zoom for restoration
            self.saved_zoom = self.zoom
            self.maximize_zoom = 0.7

            # Circuit canvas at top with scrollbars
            circuit_frame = ttk.Frame(self.maximize_window)
            circuit_frame.pack(fill=tk.BOTH, expand=False, pady=(10, 5))

            # Header with zoom controls
            header_frame = ttk.Frame(circuit_frame)
            header_frame.pack(fill=tk.X, padx=10, pady=5)

            ttk.Label(header_frame, text="Circuit Diagram",
                    font=('Arial', 12, 'bold')).pack(side=tk.LEFT)

            ttk.Label(header_frame, text="  Zoom:").pack(side=tk.RIGHT, padx=(20, 5))
            ttk.Button(header_frame, text="+", command=self.maximize_zoom_in,
                    width=3).pack(side=tk.RIGHT, padx=2)
            ttk.Button(header_frame, text="-", command=self.maximize_zoom_out,
                    width=3).pack(side=tk.RIGHT, padx=2)
            ttk.Button(header_frame, text="Reset", command=self.maximize_zoom_reset,
                    width=6).pack(side=tk.RIGHT, padx=2)

            # Create scrollable canvas for circuit
            circuit_canvas_frame = ttk.Frame(circuit_frame)
            circuit_canvas_frame.pack(fill=tk.BOTH, expand=True, padx=10)

            h_scroll = ttk.Scrollbar(circuit_canvas_frame, orient=tk.HORIZONTAL)
            h_scroll.pack(side=tk.BOTTOM, fill=tk.X)

            v_scroll = ttk.Scrollbar(circuit_canvas_frame, orient=tk.VERTICAL)
            v_scroll.pack(side=tk.RIGHT, fill=tk.Y)

            self.maximize_canvas = tk.Canvas(circuit_canvas_frame, bg='white', height=250,
                                            xscrollcommand=h_scroll.set,
                                            yscrollcommand=v_scroll.set)
            self.maximize_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

            h_scroll.config(command=self.maximize_canvas.xview)
            v_scroll.config(command=self.maximize_canvas.yview)

            # Draw circuit
            self.draw_circuit_on_maximize_canvas()

            # Probabilities section below
            prob_frame = ttk.Frame(self.maximize_window)
            prob_frame.pack(fill=tk.BOTH, expand=True, pady=(5, 10))

            ttk.Label(prob_frame, text="Measurement Probabilities",
                    font=('Arial', 12, 'bold')).pack(pady=5)

            # Scrollable frame for probabilities
            canvas = tk.Canvas(prob_frame)
            scrollbar = ttk.Scrollbar(prob_frame, orient="vertical", command=canvas.yview)
            scrollable_frame = ttk.Frame(canvas)

            scrollable_frame.bind(
                "<Configure>",
                lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
            )

            canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
            canvas.configure(yscrollcommand=scrollbar.set)

            # Create grid layout for probabilities
            results = self.circuit.get_results()
            if isinstance(results, tuple):
                results, _ = results

            col_count = 4  # Number of columns
            row = 0
            col = 0

            for i, prob in enumerate(results['probabilities']):
                if prob > 1e-10:
                    frame = ttk.LabelFrame(scrollable_frame, text=results['state_labels'][i],
                                        padding=10)
                    frame.grid(row=row, column=col, padx=10, pady=10, sticky='ew')

                    # Probability bar
                    bar_canvas = tk.Canvas(frame, height=30, width=200, bg='#e9ecef')
                    bar_canvas.pack(pady=5)

                    bar_width = int(200 * prob)
                    bar_canvas.create_rectangle(0, 0, bar_width, 30, fill='#28a745', outline='')

                    # Percentage text
                    percent_label = ttk.Label(frame, text=f"{prob*100:.2f}%",
                                            font=('Arial', 11, 'bold'))
                    percent_label.pack()

                    col += 1
                    if col >= col_count:
                        col = 0
                        row += 1

            canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

            # Close button
            ttk.Button(self.maximize_window, text="Close",
                    command=self.toggle_maximize_probabilities).pack(pady=10)

            self.prob_maximized = True

            def on_close():
                self.zoom = self.saved_zoom
                self.toggle_maximize_probabilities()

            self.maximize_window.protocol("WM_DELETE_WINDOW", on_close)

    def draw_circuit_on_maximize_canvas(self) -> None:
        """Draw circuit on maximize canvas"""
        canvas = self.maximize_canvas
        canvas.delete('all')

        # Apply zoom
        ws = int(self.wire_spacing * self.maximize_zoom)
        gw = int(self.gate_width * self.maximize_zoom)
        gh = int(self.gate_height * self.maximize_zoom)
        tsw = int(self.time_step_width * self.maximize_zoom)
        lm = int(self.left_margin * self.maximize_zoom)
        tm = int(self.top_margin * self.maximize_zoom)

        # Update scroll region
        width = int((lm + self.time_steps * tsw) * 1.0)
        height = int((tm + self.circuit.num_qubits * ws + 100) * 1.0)
        canvas.config(scrollregion=(0, 0, width, height))

        # Draw grid
        for t in range(self.time_steps + 1):
            x = lm + t * tsw
            canvas.create_line(x, tm - 20, x, tm + self.circuit.num_qubits * ws,
                            fill='#f0f0f0', width=1)

        # Draw wires
        for q in range(self.circuit.num_qubits):
            y = tm + q * ws
            canvas.create_line(lm, y, lm + self.time_steps * tsw, y, fill='#333', width=2)
            canvas.create_text(lm - 30, y, text=f'q{q}', font=('Arial', 12, 'bold'))

        # Draw gates - reuse existing methods
        for gate in self.circuit_gates:
            self.draw_gate_on_maximize_canvas(gate, lm, tm, ws, gw, gh, tsw, canvas)

    def draw_gate_on_maximize_canvas(self, gate, lm, tm, ws, gw, gh, tsw, canvas) -> None:
        """Draw individual gate on maximize canvas"""
        x = lm + gate['time'] * tsw
        y = tm + gate['qubits'][0] * ws

        color = '#667eea'

        if gate['gate'] in ['CNOT', 'CZ']:
            offset = self.get_gate_horizontal_offset(gate)
            x += offset * tsw
            control_y = y
            target_y = y + ws * (gate['qubits'][1] - gate['qubits'][0])

            canvas.create_line(x, control_y, x, target_y, fill='#333', width=2)
            canvas.create_oval(x - 6, control_y - 6, x + 6, control_y + 6,
                            fill='#333', outline='#333')

            r = int(15 * self.maximize_zoom)
            canvas.create_oval(x - r, target_y - r, x + r, target_y + r,
                            outline='#333', width=2)
            canvas.create_line(x - 10, target_y, x + 10, target_y, fill='#333', width=2)
            canvas.create_line(x, target_y - 10, x, target_y + 10, fill='#333', width=2)

        elif gate['gate'] == 'SWAP':
            offset = self.get_gate_horizontal_offset(gate)
            x += offset * tsw
            y1 = y
            y2 = y + ws * (gate['qubits'][1] - gate['qubits'][0])

            canvas.create_line(x, y1, x, y2, fill='#333', width=2)

            size = int(8 * self.maximize_zoom)
            for yy in [y1, y2]:
                canvas.create_line(x - size, yy - size, x + size, yy + size,
                                fill='#333', width=3)
                canvas.create_line(x + size, yy - size, x - size, yy + size,
                                fill='#333', width=3)

        elif gate['gate'] == 'CCNOT':
            offset = self.get_gate_horizontal_offset(gate)
            x += offset * tsw
            qubits = gate['qubits']
            base_qubit = qubits[0]
            control1_y = y + ws * (qubits[0] - base_qubit)
            control2_y = y + ws * (qubits[1] - base_qubit)
            target_y = y + ws * (qubits[2] - base_qubit)

            min_y = min(control1_y, control2_y, target_y)
            max_y = max(control1_y, control2_y, target_y)
            canvas.create_line(x, min_y, x, max_y, fill='#333', width=2)

            for cy in [control1_y, control2_y]:
                canvas.create_oval(x - 6, cy - 6, x + 6, cy + 6,
                                fill='#333', outline='#333')

            r = int(15 * self.maximize_zoom)
            canvas.create_oval(x - r, target_y - r, x + r, target_y + r,
                            outline='#333', width=2)
            canvas.create_line(x - 10, target_y, x + 10, target_y, fill='#333', width=2)
            canvas.create_line(x, target_y - 10, x, target_y + 10, fill='#333', width=2)

        elif gate['gate'] == 'M':
            canvas.create_rectangle(x - gw//2, y - gh//2, x + gw//2, y + gh//2,
                                fill='#ffd700', outline='#333', width=2)

            r = int(8 * self.maximize_zoom)
            canvas.create_arc(x - r, y - r//2, x + r, y + r//2,
                            start=180, extent=180, style=tk.ARC,
                            outline='#333', width=2)
            canvas.create_line(x, y, x + r, y - r, fill='#333', width=2)
        else:
            # Single qubit gate
            canvas.create_rectangle(x - gw//2, y - gh//2, x + gw//2, y + gh//2,
                                fill=color, outline='#333', width=2)
            canvas.create_text(x, y, text=gate['gate'], fill='white',
                            font=('Arial', int(12 * self.maximize_zoom), 'bold'))
    
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
        width = int((self.left_margin + self.time_steps * self.time_step_width) * self.zoom)
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
        for t in range(self.time_steps + 1):
            x = lm + t * tsw
            self.canvas.create_line(x, tm - 30, x, tm + self.circuit.num_qubits * ws,
                                  fill='#f0f0f0', width=1)
        
        # Draw wires
        for q in range(self.circuit.num_qubits):
            y = tm + q * ws
            self.canvas.create_line(lm, y, lm + self.time_steps * tsw, y, fill='#333', width=2)
            self.canvas.create_text(lm - 30, y, text=f'q{q}', font=('Arial', 12, 'bold'))

        if self.qubit_selection_mode and self.pending_gate:
            x = lm + self.pending_gate['time'] * tsw
            for selected_q in self.selected_qubits:
                y = tm + selected_q * ws
                # Draw highlight circle on selected qubits
                self.canvas.create_oval(x - 20, y - 20, x + 20, y + 20,
                                    outline='#ff6b6b', width=3, dash=(5, 5))
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
        """Export circuit as JSON, PNG, or SVG"""
        # Create custom dialog for format selection
        format_dialog = tk.Toplevel(self.root)
        format_dialog.title("Export Format")
        format_dialog.geometry("300x200")
        format_dialog.transient(self.root)
        format_dialog.grab_set()
        
        result = {'format': None}
        
        ttk.Label(format_dialog, text="Select Export Format:", 
                font=('Arial', 12, 'bold')).pack(pady=20)
        
        def select_format(fmt) -> None:
            result['format'] = fmt
            format_dialog.destroy()
        
        ttk.Button(format_dialog, text="SVG (Vector - Best Quality)", 
                command=lambda: select_format('svg')).pack(pady=5, fill=tk.X, padx=40)
        ttk.Button(format_dialog, text="PNG (Raster Image)", 
                command=lambda: select_format('png')).pack(pady=5, fill=tk.X, padx=40)
        ttk.Button(format_dialog, text="JSON (Data Only)", 
                command=lambda: select_format('json')).pack(pady=5, fill=tk.X, padx=40)
        ttk.Button(format_dialog, text="Cancel", 
                command=format_dialog.destroy).pack(pady=10)
        
        self.root.wait_window(format_dialog)
        
        if result['format'] == 'svg':
            self.export_circuit_svg()
        elif result['format'] == 'png':
            self.export_circuit_png()
        elif result['format'] == 'json':
            self.export_circuit_json()

    def export_circuit_json(self) -> None:
        """Export circuit as JSON"""
        filename = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if filename:
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

    def export_circuit_png(self) -> None:
        """Export circuit as high-quality PNG with states and probabilities"""
        filename = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG files", "*.png"), ("All files", "*.*")]
        )
        
        if not filename:
            return
        
        try:
            from PIL import Image, PngImagePlugin

            # Calculate circuit dimensions
            max_time = max([g['time'] for g in self.circuit_gates], default=2) + 2
            
            zoom = 2.0  
            ws = int(self.wire_spacing * zoom)
            gw = int(self.gate_width * zoom)
            gh = int(self.gate_height * zoom)
            tsw = int(self.time_step_width * zoom)

            # Calculate circuit dimensions
            circuit_width = max_time * tsw + 100
            circuit_height = self.circuit.num_qubits * ws + 80
            
            # Layout dimensions
            state_width = 350
            padding = 30
            
            # Total dimensions
            export_width = state_width + circuit_width + state_width + padding * 4
            prob_height = 600
            total_height = circuit_height + prob_height + padding * 3
            
            # Create hidden window
            export_window = tk.Toplevel(self.root)
            export_window.withdraw()
            
            # Create canvas
            export_canvas = tk.Canvas(export_window, 
                                    width=export_width, 
                                    height=total_height,
                                    bg='white')
            export_canvas.pack()
            
            # --- Draw Initial State Section ---
            y_offset = padding
            export_canvas.create_text(padding, y_offset, 
                                    text="Initial State", 
                                    font=('Arial', 16, 'bold'),
                                    anchor='nw')
            y_offset += 30
            
            initial_state = self.circuit.initialize_state()
            state_str = ''
            for i, amp in enumerate(initial_state):
                if amp.magnitude() > 1e-10:
                    label = '|' + bin(i)[2:].zfill(self.circuit.num_qubits) + '⟩'
                    state_str += f"{amp}{label}\n"
            
            export_canvas.create_text(padding, y_offset,
                                    text=state_str if state_str else '|0⟩',
                                    font=('Arial', 12),
                                    anchor='nw')
            
            # --- Draw Circuit Section ---
            circuit_y = padding
            circuit_x = state_width
            
            export_canvas.create_text(circuit_x, circuit_y,
                                    text="Circuit Diagram",
                                    font=('Arial', 16, 'bold'),
                                    anchor='nw')
            circuit_y += 40
            
            lm = circuit_x + 50
            tm = circuit_y + 20
            
            # Draw wires
            for q in range(self.circuit.num_qubits):
                y = tm + q * ws
                export_canvas.create_line(lm, y, lm + max_time * tsw, y, 
                                        fill='#333', width=2)
                export_canvas.create_text(lm - 30, y, text=f'q{q}', 
                                        font=('Arial', 12, 'bold'))
            
            # Draw gates
            for gate in self.circuit_gates:
                self.draw_gate_on_export_canvas(gate, lm, tm, ws, gw, gh, tsw, 
                                            export_canvas, zoom)
            
            # --- Draw Final State Section ---
            final_x = circuit_x + max_time * tsw + 150
            export_canvas.create_text(final_x, padding,
                                    text="Final State",
                                    font=('Arial', 16, 'bold'),
                                    anchor='nw')
            
            results = self.circuit.get_results()
            if isinstance(results, tuple):
                results, _ = results
            
            final_state_str = ''
            for i, amp in enumerate(results['state_vector']):
                if results['probabilities'][i] > 1e-10:
                    final_state_str += f"{amp}{results['state_labels'][i]}\n"
            
            export_canvas.create_text(final_x, padding + 30,
                                    text=final_state_str if final_state_str else '|0⟩',
                                    font=('Arial', 12),
                                    anchor='nw')
            
            # --- Draw Probabilities Section ---
            prob_y = circuit_height + padding * 2
            export_canvas.create_text(padding, prob_y,
                                    text="Measurement Probabilities",
                                    font=('Arial', 16, 'bold'),
                                    anchor='nw')
            prob_y += 40
            
            col_count = 4
            col_width = (export_width - padding * 2) // col_count
            row = 0
            col = 0
            
            for i, prob in enumerate(results['probabilities']):
                if prob > 1e-10:
                    x = padding + col * col_width
                    y = prob_y + row * 120
                    
                    export_canvas.create_text(x + 10, y,
                                            text=results['state_labels'][i],
                                            font=('Arial', 14, 'bold'),
                                            anchor='nw')
                    
                    bar_width = 180
                    bar_height = 30
                    bar_x = x + 10
                    bar_y = y + 30
                    
                    export_canvas.create_rectangle(bar_x, bar_y,
                                                bar_x + bar_width, bar_y + bar_height,
                                                fill='#e9ecef', outline='#ccc')
                    
                    filled_width = int(bar_width * prob)
                    export_canvas.create_rectangle(bar_x, bar_y,
                                                bar_x + filled_width, bar_y + bar_height,
                                                fill='#28a745', outline='')
                    
                    export_canvas.create_text(bar_x + bar_width//2, bar_y + bar_height//2,
                                            text=f"{prob*100:.2f}%",
                                            font=('Arial', 12, 'bold'))
                    
                    col += 1
                    if col >= col_count:
                        col = 0
                        row += 1
            
            export_window.update()
            
            # Save to PostScript
            ps_file = filename.replace('.png', '_temp.ps')
            export_canvas.postscript(file=ps_file, colormode='color',
                                    width=export_width, height=total_height)
            
            # Convert to PNG with metadata
            img = Image.open(ps_file)
            
            # Create circuit JSON for metadata
            initial_state_data = None
            if self.circuit.initial_state is not None:
                initial_state_data = [[amp.r, amp.i] for amp in self.circuit.initial_state]
            
            circuit_data = {
                'num_qubits': self.circuit.num_qubits,
                'gates': self.circuit_gates,
                'initial_state': initial_state_data
            }
            
            # Encode to base64
            import base64
            circuit_json = json.dumps(circuit_data)
            circuit_b64 = base64.b64encode(circuit_json.encode('utf-8')).decode('ascii')
            
            # Add metadata
            metadata = PngImagePlugin.PngInfo()
            metadata.add_text("QuantumCircuit", circuit_b64)
            metadata.add_text("Description", "Quantum Circuit Simulator Export")
            
            # Save 
            img.save(filename, 'PNG', pnginfo=metadata, dpi=(500, 500))
            
            # Cleanup
            import os
            os.remove(ps_file)
            
            export_window.destroy()
            messagebox.showinfo("Export", "Circuit exported as PNG with embedded data!")
            
        except ImportError:
            messagebox.showerror("Export Error", 
                "Pillow library required for PNG export.\nInstall with: pip install pillow")
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export PNG:\n{str(e)}")


    def draw_gate_on_export_canvas(self, gate, lm, tm, ws, gw, gh, tsw, canvas, zoom) -> None:
        """Draw gate on export canvas"""
        x = lm + gate['time'] * tsw
        y = tm + gate['qubits'][0] * ws
        
        if gate['gate'] in ['CNOT', 'CZ']:
            offset = self.get_gate_horizontal_offset(gate)
            x += offset * tsw
            control_y = y
            target_y = y + ws * (gate['qubits'][1] - gate['qubits'][0])
            
            canvas.create_line(x, control_y, x, target_y, fill='#333', width=2)
            canvas.create_oval(x - 6, control_y - 6, x + 6, control_y + 6,
                            fill='#333', outline='#333')
            
            r = int(15 * zoom)
            canvas.create_oval(x - r, target_y - r, x + r, target_y + r,
                            outline='#333', width=2)
            canvas.create_line(x - 10, target_y, x + 10, target_y, fill='#333', width=2)
            canvas.create_line(x, target_y - 10, x, target_y + 10, fill='#333', width=2)
            
        elif gate['gate'] == 'SWAP':
            offset = self.get_gate_horizontal_offset(gate)
            x += offset * tsw
            y1 = y
            y2 = y + ws * (gate['qubits'][1] - gate['qubits'][0])
            
            canvas.create_line(x, y1, x, y2, fill='#333', width=2)
            
            size = int(8 * zoom)
            for yy in [y1, y2]:
                canvas.create_line(x - size, yy - size, x + size, yy + size,
                                fill='#333', width=3)
                canvas.create_line(x + size, yy - size, x - size, yy + size,
                                fill='#333', width=3)
                                
        elif gate['gate'] == 'CCNOT':
            offset = self.get_gate_horizontal_offset(gate)
            x += offset * tsw
            qubits = gate['qubits']
            base_qubit = qubits[0]
            control1_y = y + ws * (qubits[0] - base_qubit)
            control2_y = y + ws * (qubits[1] - base_qubit)
            target_y = y + ws * (qubits[2] - base_qubit)
            
            min_y = min(control1_y, control2_y, target_y)
            max_y = max(control1_y, control2_y, target_y)
            canvas.create_line(x, min_y, x, max_y, fill='#333', width=2)
            
            for cy in [control1_y, control2_y]:
                canvas.create_oval(x - 6, cy - 6, x + 6, cy + 6,
                                fill='#333', outline='#333')
            
            r = int(15 * zoom)
            canvas.create_oval(x - r, target_y - r, x + r, target_y + r,
                            outline='#333', width=2)
            canvas.create_line(x - 10, target_y, x + 10, target_y, fill='#333', width=2)
            canvas.create_line(x, target_y - 10, x, target_y + 10, fill='#333', width=2)
            
        elif gate['gate'] == 'M':
            canvas.create_rectangle(x - gw//2, y - gh//2, x + gw//2, y + gh//2,
                                fill='#ffd700', outline='#333', width=2)
            
            r = int(8 * zoom)
            canvas.create_arc(x - r, y - r//2, x + r, y + r//2,
                            start=180, extent=180, style=tk.ARC,
                            outline='#333', width=2)
            canvas.create_line(x, y, x + r, y - r, fill='#333', width=2)
        else:
            # Single qubit gate
            canvas.create_rectangle(x - gw//2, y - gh//2, x + gw//2, y + gh//2,
                                fill='#667eea', outline='#333', width=2)
            canvas.create_text(x, y, text=gate['gate'], fill='white',
                            font=('Arial', int(12 * zoom), 'bold'))
            
    def export_circuit_svg(self) -> None:
        """Export circuit as SVG with embedded circuit data"""
        filename = filedialog.asksaveasfilename(
            defaultextension=".svg",
            filetypes=[("SVG files", "*.svg"), ("All files", "*.*")]
        )
        
        if not filename:
            return
        
        try:
            import base64
            
            # Calculate dimensions
            max_time = max([g['time'] for g in self.circuit_gates], default=2) + 2
            
            # SVG uses absolute coordinates
            ws = 80  # wire spacing
            gw = 50  # gate width
            gh = 40  # gate height
            tsw = 100  # time step width
            
            circuit_width = max_time * tsw + 100
            circuit_height = self.circuit.num_qubits * ws + 80
            
            state_width = 350
            padding = 30
            
            export_width = max(1800, state_width + circuit_width + state_width + padding * 4)
            prob_height = 600
            total_height = circuit_height + prob_height + padding * 3
            
            lm = state_width + 50  # left margin for circuit
            tm = padding + 60  # top margin for circuit
            
            # Start SVG
            svg_lines = []
            svg_lines.append(f'<?xml version="1.0" encoding="UTF-8"?>')
            svg_lines.append(f'<svg xmlns="http://www.w3.org/2000/svg" '
                            f'width="{export_width}" height="{total_height}" '
                            f'viewBox="0 0 {export_width} {total_height}">')
            
            # White background
            svg_lines.append(f'<rect width="{export_width}" height="{total_height}" fill="white"/>')
            
            # Embed circuit data as metadata
            initial_state_data = None
            if self.circuit.initial_state is not None:
                initial_state_data = [[amp.r, amp.i] for amp in self.circuit.initial_state]
            
            circuit_data = {
                'num_qubits': self.circuit.num_qubits,
                'gates': self.circuit_gates,
                'initial_state': initial_state_data
            }
            
            circuit_json = json.dumps(circuit_data)
            circuit_b64 = base64.b64encode(circuit_json.encode('utf-8')).decode('ascii')
            
            svg_lines.append(f'<metadata>')
            svg_lines.append(f'  <quantum-circuit>{circuit_b64}</quantum-circuit>')
            svg_lines.append(f'</metadata>')
            
            # --- Initial State Section ---
            y_offset = padding
            svg_lines.append(f'<text x="{padding}" y="{y_offset + 16}" '
                            f'font-family="Arial" font-size="16" font-weight="bold" fill="black">'
                            f'Initial State</text>')
            y_offset += 30
            
            initial_state = self.circuit.initialize_state()
            line_y = y_offset
            for i, amp in enumerate(initial_state):
                if amp.magnitude() > 1e-10:
                    label = '|' + bin(i)[2:].zfill(self.circuit.num_qubits) + '⟩'
                    text = f"{amp}{label}"
                    svg_lines.append(f'<text x="{padding}" y="{line_y + 12}" '
                                f'font-family="Arial" font-size="12" fill="black">{self._escape_xml(text)}</text>')
                    line_y += 20
            
            # --- Circuit Section ---
            circuit_y = padding
            circuit_x = state_width
            
            svg_lines.append(f'<text x="{circuit_x}" y="{circuit_y + 16}" '
                            f'font-family="Arial" font-size="16" font-weight="bold" fill="black">'
                            f'Circuit Diagram</text>')
            
            # Draw wires
            for q in range(self.circuit.num_qubits):
                y = tm + q * ws
                svg_lines.append(f'<line x1="{lm}" y1="{y}" x2="{lm + max_time * tsw}" y2="{y}" '
                            f'stroke="#333" stroke-width="2"/>')
                svg_lines.append(f'<text x="{lm - 30}" y="{y + 5}" '
                            f'font-family="Arial" font-size="12" font-weight="bold" '
                            f'text-anchor="middle" fill="black">q{q}</text>')
            
            # Draw gates
            for gate in self.circuit_gates:
                svg_lines.extend(self.draw_gate_svg(gate, lm, tm, ws, gw, gh, tsw))
            
            # --- Final State Section ---
            final_x = circuit_x + max_time * tsw + 150
            svg_lines.append(f'<text x="{final_x}" y="{padding + 16}" '
                            f'font-family="Arial" font-size="16" font-weight="bold" fill="black">'
                            f'Final State</text>')
            
            results = self.circuit.get_results()
            if isinstance(results, tuple):
                results, _ = results
            
            line_y = padding + 30
            for i, amp in enumerate(results['state_vector']):
                if results['probabilities'][i] > 1e-10:
                    text = f"{amp}{results['state_labels'][i]}"
                    svg_lines.append(f'<text x="{final_x}" y="{line_y + 12}" '
                                f'font-family="Arial" font-size="12" fill="black">{self._escape_xml(text)}</text>')
                    line_y += 20
            
            # --- Probabilities Section ---
            prob_y = circuit_height + padding * 2
            svg_lines.append(f'<text x="{padding}" y="{prob_y + 16}" '
                            f'font-family="Arial" font-size="16" font-weight="bold" fill="black">'
                            f'Measurement Probabilities</text>')
            prob_y += 40
            
            col_count = 4
            col_width = (export_width - padding * 2) // col_count
            row = 0
            col = 0
            
            for i, prob in enumerate(results['probabilities']):
                if prob > 1e-10:
                    x = padding + col * col_width
                    y = prob_y + row * 120
                    
                    # State label
                    svg_lines.append(f'<text x="{x + 10}" y="{y + 14}" '
                                f'font-family="Arial" font-size="14" font-weight="bold" fill="black">'
                                f'{self._escape_xml(results["state_labels"][i])}</text>')
                    
                    # Probability bar
                    bar_width = 180
                    bar_height = 30
                    bar_x = x + 10
                    bar_y = y + 30
                    
                    svg_lines.append(f'<rect x="{bar_x}" y="{bar_y}" width="{bar_width}" height="{bar_height}" '
                                f'fill="#e9ecef" stroke="#ccc"/>')
                    
                    filled_width = int(bar_width * prob)
                    svg_lines.append(f'<rect x="{bar_x}" y="{bar_y}" width="{filled_width}" height="{bar_height}" '
                                f'fill="#28a745"/>')
                    
                    # Percentage text
                    svg_lines.append(f'<text x="{bar_x + bar_width//2}" y="{bar_y + bar_height//2 + 5}" '
                                f'font-family="Arial" font-size="12" font-weight="bold" '
                                f'text-anchor="middle" fill="black">{prob*100:.2f}%</text>')
                    
                    col += 1
                    if col >= col_count:
                        col = 0
                        row += 1
            
            # Close SVG
            svg_lines.append('</svg>')
            
            # Write file
            with open(filename, 'w', encoding='utf-8') as f:
                f.write('\n'.join(svg_lines))
            
            messagebox.showinfo("Export", "Circuit exported as SVG successfully!")
            
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export SVG:\n{str(e)}")

    def _escape_xml(self, text) -> str:
        """Escape special XML characters"""
        return (text.replace('&', '&amp;')
                    .replace('<', '&lt;')
                    .replace('>', '&gt;')
                    .replace('"', '&quot;')
                    .replace("'", '&apos;'))

    def draw_gate_svg(self, gate, lm, tm, ws, gw, gh, tsw) -> list:
        """Generate SVG elements for a gate"""
        svg_elements = []
        x = lm + gate['time'] * tsw
        y = tm + gate['qubits'][0] * ws
        
        if gate['gate'] in ['CNOT', 'CZ']:
            offset = self.get_gate_horizontal_offset(gate)
            x += offset * tsw
            control_y = y
            target_y = y + ws * (gate['qubits'][1] - gate['qubits'][0])
            
            # Connecting line
            svg_elements.append(f'<line x1="{x}" y1="{control_y}" x2="{x}" y2="{target_y}" '
                            f'stroke="#333" stroke-width="2"/>')
            
            # Control dot
            svg_elements.append(f'<circle cx="{x}" cy="{control_y}" r="6" fill="#333"/>')
            
            # Target circle
            r = 15
            svg_elements.append(f'<circle cx="{x}" cy="{target_y}" r="{r}" '
                            f'fill="none" stroke="#333" stroke-width="2"/>')
            svg_elements.append(f'<line x1="{x - 10}" y1="{target_y}" x2="{x + 10}" y2="{target_y}" '
                            f'stroke="#333" stroke-width="2"/>')
            svg_elements.append(f'<line x1="{x}" y1="{target_y - 10}" x2="{x}" y2="{target_y + 10}" '
                            f'stroke="#333" stroke-width="2"/>')
            
        elif gate['gate'] == 'SWAP':
            offset = self.get_gate_horizontal_offset(gate)
            x += offset * tsw
            y1 = y
            y2 = y + ws * (gate['qubits'][1] - gate['qubits'][0])
            
            # Connecting line
            svg_elements.append(f'<line x1="{x}" y1="{y1}" x2="{x}" y2="{y2}" '
                            f'stroke="#333" stroke-width="2"/>')
            
            # X symbols
            size = 8
            for yy in [y1, y2]:
                svg_elements.append(f'<line x1="{x - size}" y1="{yy - size}" '
                                f'x2="{x + size}" y2="{yy + size}" '
                                f'stroke="#333" stroke-width="3"/>')
                svg_elements.append(f'<line x1="{x + size}" y1="{yy - size}" '
                                f'x2="{x - size}" y2="{yy + size}" '
                                f'stroke="#333" stroke-width="3"/>')
        
        elif gate['gate'] == 'CCNOT':
            offset = self.get_gate_horizontal_offset(gate)
            x += offset * tsw
            qubits = gate['qubits']
            base_qubit = qubits[0]
            control1_y = y + ws * (qubits[0] - base_qubit)
            control2_y = y + ws * (qubits[1] - base_qubit)
            target_y = y + ws * (qubits[2] - base_qubit)
            
            min_y = min(control1_y, control2_y, target_y)
            max_y = max(control1_y, control2_y, target_y)
            
            # Connecting line
            svg_elements.append(f'<line x1="{x}" y1="{min_y}" x2="{x}" y2="{max_y}" '
                            f'stroke="#333" stroke-width="2"/>')
            
            # Control dots
            for cy in [control1_y, control2_y]:
                svg_elements.append(f'<circle cx="{x}" cy="{cy}" r="6" fill="#333"/>')
            
            # Target
            r = 15
            svg_elements.append(f'<circle cx="{x}" cy="{target_y}" r="{r}" '
                            f'fill="none" stroke="#333" stroke-width="2"/>')
            svg_elements.append(f'<line x1="{x - 10}" y1="{target_y}" x2="{x + 10}" y2="{target_y}" '
                            f'stroke="#333" stroke-width="2"/>')
            svg_elements.append(f'<line x1="{x}" y1="{target_y - 10}" x2="{x}" y2="{target_y + 10}" '
                            f'stroke="#333" stroke-width="2"/>')
        
        elif gate['gate'] == 'M':
            # Measurement gate
            svg_elements.append(f'<rect x="{x - gw//2}" y="{y - gh//2}" '
                            f'width="{gw}" height="{gh}" '
                            f'fill="#ffd700" stroke="#333" stroke-width="2"/>')
            
            # Measurement symbol (arc + arrow)
            r = 8
            svg_elements.append(f'<path d="M {x - r} {y} A {r} {r//2} 0 0 1 {x + r} {y}" '
                            f'fill="none" stroke="#333" stroke-width="2"/>')
            svg_elements.append(f'<line x1="{x}" y1="{y}" x2="{x + r}" y2="{y - r}" '
                            f'stroke="#333" stroke-width="2"/>')
        
        else:
            # Single qubit gate
            svg_elements.append(f'<rect x="{x - gw//2}" y="{y - gh//2}" '
                            f'width="{gw}" height="{gh}" '
                            f'fill="#667eea" stroke="#333" stroke-width="2"/>')
            svg_elements.append(f'<text x="{x}" y="{y + 5}" '
                            f'font-family="Arial" font-size="12" font-weight="bold" '
                            f'text-anchor="middle" fill="white">{gate["gate"]}</text>')
        
        return svg_elements

    def import_circuit(self) -> None:
        """Import circuit from JSON, PNG, or SVG"""
        filename = filedialog.askopenfilename(
            filetypes=[("Circuit files", "*.json *.png *.svg"), 
                    ("JSON files", "*.json"),
                    ("PNG files", "*.png"),
                    ("SVG files", "*.svg"),
                    ("All files", "*.*")]
        )
        
        if not filename:
            return
        
        try:
            if filename.lower().endswith('.png'):
                self.import_circuit_png(filename)
            elif filename.lower().endswith('.svg'):
                self.import_circuit_svg(filename)
            else:
                self.import_circuit_json(filename)
        except Exception as e:
            messagebox.showerror("Import Error", f"Failed to import circuit:\n{str(e)}")


    def import_circuit_json(self, filename) -> None:
        """Import circuit from JSON file"""
        with open(filename, 'r') as f:
            circuit_data = json.load(f)
        
        self.circuit = QuantumCircuit(circuit_data['num_qubits'])
        
        if circuit_data.get('initial_state'):
            initial_state = [Complex(amp[0], amp[1]) for amp in circuit_data['initial_state']]
            self.circuit.set_initial_state(initial_state)
        
        self.circuit_gates = circuit_data.get('gates', [])
        self.draw_circuit()
        self.update_scroll_region()
        self.update_circuit_info()
        self.update_initial_state_display()
        
        messagebox.showinfo("Import", "Circuit imported successfully!")

    def import_circuit_png(self, filename) -> None:
        """Import circuit from PNG file with embedded metadata"""
        try:
            from PIL import Image
            import base64
            
            img = Image.open(filename)
            
            # Check for circuit metadata
            if 'QuantumCircuit' not in img.info:
                messagebox.showerror("Import Error", 
                    "This PNG does not contain quantum circuit data.\n"
                    "Only PNGs exported by this simulator can be imported.")
                return
            
            # Decode circuit data
            circuit_b64 = img.info['QuantumCircuit']
            circuit_json = base64.b64decode(circuit_b64.encode('ascii')).decode('utf-8')
            circuit_data = json.loads(circuit_json)
            
            # Load circuit
            self.circuit = QuantumCircuit(circuit_data['num_qubits'])
            
            if circuit_data.get('initial_state'):
                initial_state = [Complex(amp[0], amp[1]) for amp in circuit_data['initial_state']]
                self.circuit.set_initial_state(initial_state)
            
            self.circuit_gates = circuit_data.get('gates', [])
            self.draw_circuit()
            self.update_scroll_region()
            self.update_circuit_info()
            self.update_initial_state_display()
            
            messagebox.showinfo("Import", "Circuit imported from PNG successfully!")
            
        except ImportError:
            messagebox.showerror("Import Error",
                "Pillow library required for PNG import.\nInstall with: pip install pillow")
        except KeyError:
            messagebox.showerror("Import Error",
                "This PNG does not contain valid quantum circuit data.")
            
    def import_circuit_svg(self, filename) -> None:
        """Import circuit from SVG file with embedded metadata"""
        try:
            import base64
            import xml.etree.ElementTree as ET
            
            # Parse the SVG file
            tree = ET.parse(filename)
            root = tree.getroot()
            
            circuit_b64 = None
            
            for elem in root.iter():
                if elem.tag.endswith('quantum-circuit') or elem.tag == 'quantum-circuit':
                    if elem.text:
                        circuit_b64 = elem.text
                        break
            
            if not circuit_b64:
                messagebox.showerror("Import Error",
                    "This SVG does not contain quantum circuit data.\n"
                    "Only SVGs exported by this simulator can be imported.")
                return
        
        except Exception as e:
            messagebox.showerror("Import Error", f"Failed to import SVG:\n{str(e)}")
            
        # Decode circuit data
        try:
            circuit_json = base64.b64decode(circuit_b64.strip().encode('ascii')).decode('utf-8') #type: ignore
            circuit_data = json.loads(circuit_json)
        except Exception:
            messagebox.showerror("Import Error",
                "Failed to decode circuit data from SVG metadata.")
            return
            
        # Load circuit
        self.circuit = QuantumCircuit(circuit_data['num_qubits'])
        
        if circuit_data.get('initial_state'):
            initial_state = [Complex(amp[0], amp[1]) for amp in circuit_data['initial_state']]
            self.circuit.set_initial_state(initial_state)
        
        self.circuit_gates = circuit_data.get('gates', [])
        self.draw_circuit()
        self.update_scroll_region()
        self.update_circuit_info()
        self.update_initial_state_display()
        
        messagebox.showinfo("Import", "Circuit imported from SVG successfully!")