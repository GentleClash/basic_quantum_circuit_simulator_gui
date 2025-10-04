
import json
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from modules.circuit import QuantumCircuit
from modules.complex_ import Complex
import base64
import xml.etree.ElementTree as ET

class ExportImportManager:
    """Utility class for circuit export/import operations"""
    
    def __init__(self, gui_ref) -> None:
        """
        Args:
            gui_ref: Reference to QuantumSimulatorGUI instance
        """
        self.gui = gui_ref
    
    def export_circuit(self) -> None:
        """Show format selection dialog and export"""
        format_dialog = tk.Toplevel(self.gui.root)
        format_dialog.title("Export Format")
        format_dialog.geometry("300x200")
        format_dialog.transient(self.gui.root)
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
        
        self.gui.root.wait_window(format_dialog)
        
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
            if self.gui.circuit.initial_state is not None:
                initial_state_data = [[amp.r, amp.i] for amp in self.gui.circuit.initial_state]
            
            circuit_data = {
                'num_qubits': self.gui.circuit.num_qubits,
                'gates': self.gui.circuit_gates,
                'initial_state': initial_state_data
            }
            
            with open(filename, 'w') as f:
                json.dump(circuit_data, f, indent=2)
            
            messagebox.showinfo("Export", "Circuit exported successfully!")
    
    def export_circuit_svg(self) -> None:
        """Export circuit as SVG with embedded circuit data"""
        filename = filedialog.asksaveasfilename(
            defaultextension=".svg",
            filetypes=[("SVG files", "*.svg"), ("All files", "*.*")]
        )
        
        if not filename:
            return
        
        try:
            max_time = max([g['time'] for g in self.gui.circuit_gates], default=2) + 2
            
            ws = 80
            gw = 50
            gh = 40
            tsw = 100
            
            circuit_width = max_time * tsw + 100
            circuit_height = self.gui.circuit.num_qubits * ws + 80
            
            state_width = 350
            padding = 30
            
            export_width = max(1800, state_width + circuit_width + state_width + padding * 4)
            prob_height = 600
            total_height = circuit_height + prob_height + padding * 3
            
            lm = state_width + 50
            tm = padding + 60
            
            svg_lines = []
            svg_lines.append(f'<?xml version="1.0" encoding="UTF-8"?>')
            svg_lines.append(f'<svg xmlns="http://www.w3.org/2000/svg" '
                            f'width="{export_width}" height="{total_height}" '
                            f'viewBox="0 0 {export_width} {total_height}">')
            
            svg_lines.append(f'<rect width="{export_width}" height="{total_height}" fill="white"/>')
            
            # Embed metadata
            initial_state_data = None
            if self.gui.circuit.initial_state is not None:
                initial_state_data = [[amp.r, amp.i] for amp in self.gui.circuit.initial_state]
            
            circuit_data = {
                'num_qubits': self.gui.circuit.num_qubits,
                'gates': self.gui.circuit_gates,
                'initial_state': initial_state_data
            }
            
            circuit_json = json.dumps(circuit_data)
            circuit_b64 = base64.b64encode(circuit_json.encode('utf-8')).decode('ascii')
            
            svg_lines.append(f'<metadata>')
            svg_lines.append(f'  <quantum-circuit>{circuit_b64}</quantum-circuit>')
            svg_lines.append(f'</metadata>')
            
            # Initial State
            y_offset = padding
            svg_lines.append(f'<text x="{padding}" y="{y_offset + 16}" '
                            f'font-family="Arial" font-size="16" font-weight="bold" fill="black">'
                            f'Initial State</text>')
            y_offset += 30
            
            initial_state = self.gui.circuit.initialize_state()
            line_y = y_offset
            for i, amp in enumerate(initial_state):
                if amp.magnitude() > 1e-10:
                    label = '|' + bin(i)[2:].zfill(self.gui.circuit.num_qubits) + '⟩'
                    text = f"{amp}{label}"
                    svg_lines.append(f'<text x="{padding}" y="{line_y + 12}" '
                                   f'font-family="Arial" font-size="12" fill="black">{self._escape_xml(text)}</text>')
                    line_y += 20
            
            # Circuit Diagram
            circuit_y = padding
            circuit_x = state_width
            
            svg_lines.append(f'<text x="{circuit_x}" y="{circuit_y + 16}" '
                            f'font-family="Arial" font-size="16" font-weight="bold" fill="black">'
                            f'Circuit Diagram</text>')
            
            # Draw wires
            for q in range(self.gui.circuit.num_qubits):
                y = tm + q * ws
                svg_lines.append(f'<line x1="{lm}" y1="{y}" x2="{lm + max_time * tsw}" y2="{y}" '
                               f'stroke="#333" stroke-width="2"/>')
                svg_lines.append(f'<text x="{lm - 30}" y="{y + 5}" '
                               f'font-family="Arial" font-size="12" font-weight="bold" '
                               f'text-anchor="middle" fill="black">q{q}</text>')
            
            # Draw gates
            for gate in self.gui.circuit_gates:
                svg_lines.extend(self._draw_gate_svg(gate, lm, tm, ws, gw, gh, tsw))
            
            # Final State
            final_x = circuit_x + max_time * tsw + 150
            svg_lines.append(f'<text x="{final_x}" y="{padding + 16}" '
                            f'font-family="Arial" font-size="16" font-weight="bold" fill="black">'
                            f'Final State</text>')
            
            results = self.gui.circuit.get_results()
            if isinstance(results, tuple):
                results, _ = results
            
            line_y = padding + 30
            for i, amp in enumerate(results['state_vector']):
                if results['probabilities'][i] > 1e-10:
                    text = f"{amp}{results['state_labels'][i]}"
                    svg_lines.append(f'<text x="{final_x}" y="{line_y + 12}" '
                                   f'font-family="Arial" font-size="12" fill="black">{self._escape_xml(text)}</text>')
                    line_y += 20
            
            # Probabilities
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
                    
                    svg_lines.append(f'<text x="{x + 10}" y="{y + 14}" '
                                   f'font-family="Arial" font-size="14" font-weight="bold" fill="black">'
                                   f'{self._escape_xml(results["state_labels"][i])}</text>')
                    
                    bar_width = 180
                    bar_height = 30
                    bar_x = x + 10
                    bar_y = y + 30
                    
                    svg_lines.append(f'<rect x="{bar_x}" y="{bar_y}" width="{bar_width}" height="{bar_height}" '
                                   f'fill="#e9ecef" stroke="#ccc"/>')
                    
                    filled_width = int(bar_width * prob)
                    svg_lines.append(f'<rect x="{bar_x}" y="{bar_y}" width="{filled_width}" height="{bar_height}" '
                                   f'fill="#28a745"/>')
                    
                    svg_lines.append(f'<text x="{bar_x + bar_width//2}" y="{bar_y + bar_height//2 + 5}" '
                                   f'font-family="Arial" font-size="12" font-weight="bold" '
                                   f'text-anchor="middle" fill="black">{prob*100:.2f}%</text>')
                    
                    col += 1
                    if col >= col_count:
                        col = 0
                        row += 1
            
            svg_lines.append('</svg>')
            
            with open(filename, 'w', encoding='utf-8') as f:
                f.write('\n'.join(svg_lines))
            
            messagebox.showinfo("Export", "Circuit exported as SVG successfully!\n"
                              "SVG maintains quality at any zoom level.")
            
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export SVG:\n{str(e)}")
    
    def _escape_xml(self, text) -> str:
        """Escape XML special characters"""
        return (text.replace('&', '&amp;')
                    .replace('<', '&lt;')
                    .replace('>', '&gt;')
                    .replace('"', '&quot;')
                    .replace("'", '&apos;'))
    
    def _draw_gate_svg(self, gate, lm, tm, ws, gw, gh, tsw) -> list:
        """Generate SVG for gate"""
        svg_elements = []
        x = lm + gate['time'] * tsw
        y = tm + gate['qubits'][0] * ws
        
        if gate['gate'] in ['CNOT', 'CZ']:
            offset = self.gui.get_gate_horizontal_offset(gate)
            x += offset * tsw
            control_y = y
            target_y = y + ws * (gate['qubits'][1] - gate['qubits'][0])
            
            svg_elements.append(f'<line x1="{x}" y1="{control_y}" x2="{x}" y2="{target_y}" '
                              f'stroke="#333" stroke-width="2"/>')
            svg_elements.append(f'<circle cx="{x}" cy="{control_y}" r="6" fill="#333"/>')
            
            r = 15
            svg_elements.append(f'<circle cx="{x}" cy="{target_y}" r="{r}" '
                              f'fill="none" stroke="#333" stroke-width="2"/>')
            svg_elements.append(f'<line x1="{x - 10}" y1="{target_y}" x2="{x + 10}" y2="{target_y}" '
                              f'stroke="#333" stroke-width="2"/>')
            svg_elements.append(f'<line x1="{x}" y1="{target_y - 10}" x2="{x}" y2="{target_y + 10}" '
                              f'stroke="#333" stroke-width="2"/>')
        
        elif gate['gate'] == 'SWAP':
            offset = self.gui.get_gate_horizontal_offset(gate)
            x += offset * tsw
            y1 = y
            y2 = y + ws * (gate['qubits'][1] - gate['qubits'][0])
            
            svg_elements.append(f'<line x1="{x}" y1="{y1}" x2="{x}" y2="{y2}" '
                              f'stroke="#333" stroke-width="2"/>')
            
            size = 8
            for yy in [y1, y2]:
                svg_elements.append(f'<line x1="{x - size}" y1="{yy - size}" '
                                  f'x2="{x + size}" y2="{yy + size}" '
                                  f'stroke="#333" stroke-width="3"/>')
                svg_elements.append(f'<line x1="{x + size}" y1="{yy - size}" '
                                  f'x2="{x - size}" y2="{yy + size}" '
                                  f'stroke="#333" stroke-width="3"/>')
        
        elif gate['gate'] == 'CCNOT':
            offset = self.gui.get_gate_horizontal_offset(gate)
            x += offset * tsw
            qubits = gate['qubits']
            base_qubit = qubits[0]
            control1_y = y + ws * (qubits[0] - base_qubit)
            control2_y = y + ws * (qubits[1] - base_qubit)
            target_y = y + ws * (qubits[2] - base_qubit)
            
            min_y = min(control1_y, control2_y, target_y)
            max_y = max(control1_y, control2_y, target_y)
            
            svg_elements.append(f'<line x1="{x}" y1="{min_y}" x2="{x}" y2="{max_y}" '
                              f'stroke="#333" stroke-width="2"/>')
            
            for cy in [control1_y, control2_y]:
                svg_elements.append(f'<circle cx="{x}" cy="{cy}" r="6" fill="#333"/>')
            
            r = 15
            svg_elements.append(f'<circle cx="{x}" cy="{target_y}" r="{r}" '
                              f'fill="none" stroke="#333" stroke-width="2"/>')
            svg_elements.append(f'<line x1="{x - 10}" y1="{target_y}" x2="{x + 10}" y2="{target_y}" '
                              f'stroke="#333" stroke-width="2"/>')
            svg_elements.append(f'<line x1="{x}" y1="{target_y - 10}" x2="{x}" y2="{target_y + 10}" '
                              f'stroke="#333" stroke-width="2"/>')
        
        elif gate['gate'] == 'M':
            svg_elements.append(f'<rect x="{x - gw//2}" y="{y - gh//2}" '
                              f'width="{gw}" height="{gh}" '
                              f'fill="#ffd700" stroke="#333" stroke-width="2"/>')
            
            r = 8
            svg_elements.append(f'<path d="M {x - r} {y} A {r} {r//2} 0 0 1 {x + r} {y}" '
                              f'fill="none" stroke="#333" stroke-width="2"/>')
            svg_elements.append(f'<line x1="{x}" y1="{y}" x2="{x + r}" y2="{y - r}" '
                              f'stroke="#333" stroke-width="2"/>')
        
        else:
            svg_elements.append(f'<rect x="{x - gw//2}" y="{y - gh//2}" '
                              f'width="{gw}" height="{gh}" '
                              f'fill="#667eea" stroke="#333" stroke-width="2"/>')
            svg_elements.append(f'<text x="{x}" y="{y + 5}" '
                              f'font-family="Arial" font-size="12" font-weight="bold" '
                              f'text-anchor="middle" fill="white">{gate["gate"]}</text>')
        
        return svg_elements
    
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
            max_time = max([g['time'] for g in self.gui.circuit_gates], default=2) + 2
            
            zoom = 2.0  
            ws = int(self.gui.wire_spacing * zoom)
            gw = int(self.gui.gate_width * zoom)
            gh = int(self.gui.gate_height * zoom)
            tsw = int(self.gui.time_step_width * zoom)

            # Calculate circuit dimensions
            circuit_width = max_time * tsw + 100
            circuit_height = self.gui.circuit.num_qubits * ws + 80
            
            # Layout dimensions
            state_width = 350
            padding = 30
            
            # Total dimensions
            export_width = state_width + circuit_width + state_width + padding * 4
            prob_height = 600
            total_height = circuit_height + prob_height + padding * 3
            
            # Create hidden window
            export_window = tk.Toplevel(self.gui.root)
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

            initial_state = self.gui.circuit.initialize_state()
            state_str = ''
            for i, amp in enumerate(initial_state):
                if amp.magnitude() > 1e-10:
                    label = '|' + bin(i)[2:].zfill(self.gui.circuit.num_qubits) + '⟩'
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
            for q in range(self.gui.circuit.num_qubits):
                y = tm + q * ws
                export_canvas.create_line(lm, y, lm + max_time * tsw, y, 
                                        fill='#333', width=2)
                export_canvas.create_text(lm - 30, y, text=f'q{q}', 
                                        font=('Arial', 12, 'bold'))
            
            # Draw gates
            for gate in self.gui.circuit_gates:
                self.draw_gate_on_export_canvas(gate, lm, tm, ws, gw, gh, tsw, 
                                            export_canvas, zoom)
            
            # --- Draw Final State Section ---
            final_x = circuit_x + max_time * tsw + 150
            export_canvas.create_text(final_x, padding,
                                    text="Final State",
                                    font=('Arial', 16, 'bold'),
                                    anchor='nw')
            
            results = self.gui.circuit.get_results()
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
            if self.gui.circuit.initial_state is not None:
                initial_state_data = [[amp.r, amp.i] for amp in self.gui.circuit.initial_state]
            
            circuit_data = {
                'num_qubits': self.gui.circuit.num_qubits,
                'gates': self.gui.circuit_gates,
                'initial_state': initial_state_data
            }
            
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
            offset = self.gui.get_gate_horizontal_offset(gate)
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
            offset = self.gui.get_gate_horizontal_offset(gate)
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
            offset = self.gui.get_gate_horizontal_offset(gate)
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
        
    def import_circuit(self) -> None:
        """Import circuit from file"""
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
    
    def _load_circuit_data(self, circuit_data) -> None:
        """Load circuit data into GUI"""
        
        self.gui.circuit = QuantumCircuit(circuit_data['num_qubits'])
        
        if circuit_data.get('initial_state'):
            initial_state = [Complex(amp[0], amp[1]) for amp in circuit_data['initial_state']]
            self.gui.circuit.set_initial_state(initial_state)
        
        self.gui.circuit_gates = circuit_data.get('gates', [])
        self.gui.draw_circuit()
        self.gui.update_scroll_region()
        self.gui.update_circuit_info()
        self.gui.update_initial_state_display()
    
    def import_circuit_json(self, filename) -> None:
        """Import circuit from JSON file"""
        with open(filename, 'r') as f:
            circuit_data = json.load(f)

        self._load_circuit_data(circuit_data)
        messagebox.showinfo("Import", "Circuit imported successfully!")

    def import_circuit_png(self, filename) -> None:
        """Import circuit from PNG file with embedded metadata"""
        try:
            from PIL import Image
            
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
            
            self._load_circuit_data(circuit_data)
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
            
        self._load_circuit_data(circuit_data)
        messagebox.showinfo("Import", "Circuit imported from SVG successfully!")

    