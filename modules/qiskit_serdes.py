import json
import ast
from typing import List, Optional, Dict, Any

try:
    ast_num = ast.Num
except AttributeError:
    ast_num = type(None)


class QiskitCircuitExporter:
    """Converts JSON quantum circuit data to Qiskit Python code."""

    def __init__(self, json_data: Optional[str] = None, json_file: Optional[str] = None) -> None:
        """
        Initialize with either JSON string or file path.
        
        Args:
            json_data: JSON string containing circuit data
            json_file: Path to JSON file containing circuit data
        """
        if json_file:
            with open(json_file, 'r') as f:
                self.circuit_data = json.load(f)
        elif json_data:
            self.circuit_data = json.loads(json_data)
        else:
            raise ValueError("Either json_data or json_file must be provided")
    
    def _gate_to_qiskit(self, gate: str, qubits: List[int]) -> str:
        """
        Convert gate specification to Qiskit method call.
        For multi-qubit gates, order matters:
        - CNOT: [control, target]
        - CCNOT: [control1, control2, target]
        - CZ: [control, target]
        - SWAP: [qubit1, qubit2]
        
        Args:
            gate: Gate name (I, H, X, Y, Z, S, T, CNOT, CZ, SWAP, CCNOT, M)
            qubits: List of qubit indices in the order specified
        
        Returns:
            Qiskit method call string
        """
        gate_upper = gate.upper()
        
        # Single qubit gates
        if gate_upper == 'I':
            return f"qc.id({qubits[0]})"
        elif gate_upper == 'H':
            return f"qc.h({qubits[0]})"
        elif gate_upper == 'X':
            return f"qc.x({qubits[0]})"
        elif gate_upper == 'Y':
            return f"qc.y({qubits[0]})"
        elif gate_upper == 'Z':
            return f"qc.z({qubits[0]})"
        elif gate_upper == 'S':
            return f"qc.s({qubits[0]})"
        elif gate_upper == 'T':
            return f"qc.t({qubits[0]})"
        
        # Two qubit gates
        elif gate_upper == 'CNOT' or gate_upper == 'CX':
            # qubits[0] is control, qubits[1] is target
            control = qubits[0]
            target = qubits[1]
            return f"qc.cx({control}, {target})  # control: {control}, target: {target}"
        
        elif gate_upper == 'CZ':
            # qubits[0] is control, qubits[1] is target
            control = qubits[0]
            target = qubits[1]
            return f"qc.cz({control}, {target})  # control: {control}, target: {target}"
        
        elif gate_upper == 'SWAP':
            # qubits[0] and qubits[1] are swapped
            return f"qc.swap({qubits[0]}, {qubits[1]})"
        
        # Three qubit gate
        elif gate_upper == 'CCNOT' or gate_upper == 'CCX' or gate_upper == 'TOFFOLI':
            # qubits[0] is control1, qubits[1] is control2, qubits[2] is target
            control1 = qubits[0]
            control2 = qubits[1]
            target = qubits[2]
            return f"qc.ccx({control1}, {control2}, {target})  # controls: [{control1}, {control2}], target: {target}"
        
        # Measurement
        elif gate_upper == 'M':
            return f"qc.measure({qubits[0]}, {qubits[0]})"
        
        else:
            raise ValueError(f"Unsupported gate: {gate}. Only I, H, X, Y, Z, S, T, CNOT, CZ, SWAP, CCNOT, M are supported.")
    
    def _format_initial_state(self, state: List[List[float]]) -> str:
        """
        Format initial state vector for Qiskit initialize method.
        
        Args:
            state: State vector as list of [real, imag] pairs
        
        Returns:
            Formatted string representation
        """
        complex_amplitudes = []
        for amplitude in state:
            real, imag = amplitude
            if imag >= 0:
                complex_amplitudes.append(f"{real}+{imag}j")
            else:
                complex_amplitudes.append(f"{real}{imag}j")
        
        return "[" + ", ".join(complex_amplitudes) + "]"

    def generate_qiskit_code(self, output_file: Optional[str] = None, include_visualization: bool = True) -> str:
        """
        Generate Qiskit Python code from JSON circuit data.
        
        Args:
            output_file: Optional file path to write the generated code
            include_visualization: Whether to include circuit drawing code
        
        Returns:
            Generated Python code as string
        """
        num_qubits = self.circuit_data['num_qubits']
        gates = self.circuit_data['gates']
        initial_state = self.circuit_data.get('initial_state', None)
        
        # Sort gates by time to ensure proper execution order
        sorted_gates = sorted(gates, key=lambda g: g['time'])
        
        # Check if measurements are needed
        has_measurement = any(g['gate'].upper() == 'M' for g in sorted_gates)
        
        # Generate code
        code_lines = [
            "from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister, transpile",
            "from qiskit_aer import AerSimulator",
            "from numpy import pi",
            "",
            "# Create quantum circuit"
        ]
        
        if has_measurement:
            code_lines.append(f"qr = QuantumRegister({num_qubits}, 'q')")
            code_lines.append(f"cr = ClassicalRegister({num_qubits}, 'c')")
            code_lines.append("qc = QuantumCircuit(qr, cr)")
        else:
            code_lines.append(f"qc = QuantumCircuit({num_qubits})")
        
        code_lines.append("")
        
        # Add initial state if provided
        if initial_state:
            code_lines.append("# Initialize custom state")
            state_str = self._format_initial_state(initial_state)
            code_lines.append(f"initial_state = {state_str}")
            code_lines.append(f"qc.initialize(initial_state, range({num_qubits}))")
            code_lines.append("")
        
        # Add gates
        code_lines.append("# Apply gates (in order of execution time)")
        for gate in sorted_gates:
            gate_name = gate['gate']
            qubits = gate['qubits']
            time = gate['time']
            
            # Skipping identity gates (they don't change the state)
            if gate_name.upper() == 'I':
                code_lines.append(f"# Time {time}: Identity gate on qubit(s) {qubits} - no operation")
                continue
            
            try:
                gate_code = self._gate_to_qiskit(gate_name, qubits)
                code_lines.append(f"{gate_code}  # Time: {time}")
            except ValueError as e:
                code_lines.append(f"# ERROR at time {time}: {str(e)}")
        
        code_lines.append("")
        
        # Add visualization and execution
        if not has_measurement:
            code_lines.append("qc.save_statevector()")

        if include_visualization:
            code_lines.extend([
                "# Visualize circuit",
                "print(qc.draw())",
                "",
                "# Execute circuit",
                "simulator = AerSimulator()",
                "qc_t = transpile(qc, simulator)",
            ])
            
        if has_measurement:
            code_lines.append("result = simulator.run(qc_t, shots=1024).result()")
            code_lines.append("counts = result.get_counts()")
            code_lines.append("print('Measurement results:')\nprint(counts)")
        else:
            code_lines.append("result = simulator.run(qc_t).result()")
            code_lines.append("statevector = result.get_statevector(qc_t)")
            code_lines.append("probabilities = statevector.probabilities_dict()")
            code_lines.append("print('Final statevector:')\nprint(statevector)")
            code_lines.append("print('Probabilities:')\nprint(probabilities)")
        
        generated_code = "\n".join(code_lines)
        
        # Write to file if specified
        if output_file:
            with open(output_file, 'w') as f:
                f.write(generated_code)
            print(f"Qiskit code written to {output_file}")
        
        return generated_code
    
    def export(self, output_file: str, include_visualization: bool = True):
        """
        Convenience method to export directly to file.
        
        Args:
            output_file: File path to write the generated code
            include_visualization: Whether to include circuit drawing code
        """
        return self.generate_qiskit_code(output_file, include_visualization)
    


class QiskitCircuitImporter:
    """Parses Qiskit Python code and converts it back to JSON format."""
    
    def __init__(self) -> None:
        self.num_qubits = 0
        self.gates = []
        self.initial_state = None
        self.time_counter = 1
        self.gate_id_counter = 1
        self.errors = []
        
    
    def _extract_qubit_count(self, tree: ast.AST) -> Optional[int]:
        """Extract the number of qubits from QuantumCircuit initialization."""
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                # Check for QuantumCircuit(n) or QuantumCircuit(QuantumRegister(n))
                if isinstance(node.func, ast.Name) and node.func.id == 'QuantumCircuit':
                    if node.args:
                        arg = node.args[0]
                        # Direct number: QuantumCircuit(5)
                        if isinstance(arg, ast.Constant):
                            return arg.value #type: ignore
                        elif isinstance(arg, ast_num):  # Python 3.7 compatibility
                            return arg.n #type: ignore
                
                # Check for QuantumRegister(n)
                elif isinstance(node.func, ast.Name) and node.func.id == 'QuantumRegister':
                    if node.args:
                        arg = node.args[0]
                        if isinstance(arg, ast.Constant):
                            return arg.value #type: ignore
                        elif isinstance(arg, ast_num):
                            return arg.n #type: ignore
        return None
    
    def _extract_initial_state(self, tree: ast.AST) -> Optional[List[List[float]]]:
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign) and isinstance(node.value, ast.List):
                # Look for: initial_state = [...]
                for t in node.targets:
                    if isinstance(t, ast.Name) and t.id == 'initial_state':
                        return self._parse_state_vector(node.value)
            if isinstance(node, ast.Expr) and isinstance(node.value, ast.Call):
                call = node.value
                if (isinstance(call.func, ast.Attribute) and 
                    call.func.attr == 'initialize'):
                    state_arg = call.args[0]
                    if isinstance(state_arg, ast.Name) and state_arg.id == 'initial_state':
                        # Already handled by assign above
                        continue
                    elif isinstance(state_arg, ast.List):
                        return self._parse_state_vector(state_arg)
        return None
    
    def _parse_state_vector(self, list_node: ast.List) -> List[List[float]]:
        """Convert AST list of complex numbers to [[real, imag], ...] format."""
        state = []
        for element in list_node.elts:
            # Handle complex number expressions like 0.0+0.0j, -1.0+0.5j, etc.
            if isinstance(element, ast.BinOp):
                real = self._extract_number(element.left)
                imag = self._extract_imaginary(element.right)
                
                # Handle subtraction (negative imaginary part)
                if isinstance(element.op, ast.Sub):
                    imag = -imag
                
                state.append([real, imag])
            
            # Handle pure real or imaginary constants
            elif isinstance(element, (ast.Constant, ast_num)):
                val = element.value if isinstance(element, ast.Constant) else element.n
                if isinstance(val, complex):
                    state.append([val.real, val.imag])
                else:
                    state.append([float(val), 0.0]) #type: ignore
            
            # Handle negative numbers like -1.0
            elif isinstance(element, ast.UnaryOp) and isinstance(element.op, ast.USub):
                val = self._extract_number(element.operand)
                state.append([-val, 0.0])
        
        return state

    def _extract_number(self, node) -> float:
        """Extract a float from an AST node, handling UnaryOp for negatives."""
        if isinstance(node, ast.Constant):
            return float(node.value) #type: ignore
        elif isinstance(node, ast_num) and hasattr(node, 'n'):
            return float(node.n) #type: ignore
        elif isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
            # Handle negative numbers like -0.5
            return -self._extract_number(node.operand)
        return 0.0

    def _extract_imaginary(self, node) -> float:
        """Extract imaginary part from a complex number node."""
        if isinstance(node, ast.Constant):
            val = node.value
            if isinstance(val, complex):
                return val.imag
            return float(val) #type: ignore
        elif isinstance(node, ast_num) and hasattr(node, 'n'):
            return float(node.n) #type: ignore
        elif isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
            return -self._extract_imaginary(node.operand)
        return 0.0

    
    def _parse_gate_call(self, node: ast.Call, gate_method: str) -> Optional[Dict]:
        """Parse a single gate method call and extract gate information."""
        # Map Qiskit method names to gate names
        method_to_gate = {
            'h': 'H',
            'x': 'X',
            'y': 'Y',
            'z': 'Z',
            'id': 'I',
            's': 'S',
            't': 'T',
            'cx': 'CNOT',
            'cz': 'CZ',
            'swap': 'SWAP',
            'ccx': 'CCNOT',
            'measure': 'M'
        }
        
        gate_name = method_to_gate.get(gate_method)
        if not gate_name:
            self.errors.append(f"Unsupported gate method: {gate_method}")
            return None
        
        # Extract qubit arguments
        qubits = []
        for arg in node.args:
            if isinstance(arg, ast.Constant):
                qubits.append(arg.value)
            elif isinstance(arg, ast_num):
                qubits.append(arg.n)
            elif isinstance(arg, ast.UnaryOp) and isinstance(arg.op, ast.USub):
                # Handle negative numbers
                if isinstance(arg.operand, (ast.Constant, ast_num)):
                    val = arg.operand.value if isinstance(arg.operand, ast.Constant) else arg.operand.n
                    qubits.append(-val) #type: ignore
        
        if not qubits:
            self.errors.append(f"No qubits found for gate {gate_name}")
            return None
        
        # Create gate dictionary
        gate_dict = {
            "id": self.gate_id_counter,
            "gate": gate_name,
            "qubits": qubits,
            "time": self.time_counter,
            "selected": False
        }
        
        self.gate_id_counter += 1
        self.time_counter += 1
        
        return gate_dict
    
    def _extract_gates_from_tree(self, tree: ast.AST):
        """Walk through AST and extract all gate operations."""
        skip_methods = {'draw', 'transpile', 'run', 'result', 'get_counts', 'get_statevector', 'print'}
        for node in ast.walk(tree):
            if isinstance(node, ast.Expr) and isinstance(node.value, ast.Call):
                call = node.value
                
                # Check if it's a method call on qc
                if (isinstance(call.func, ast.Attribute) and
                    isinstance(call.func.value, ast.Name) and
                    call.func.value.id == 'qc' and
                    call.func.attr not in skip_methods):
                    
                    method_name = call.func.attr
                    
                    # Skip non-gate methods
                    if method_name in ['draw', 'initialize']:
                        continue
                    
                    gate_dict = self._parse_gate_call(call, method_name)
                    if gate_dict:
                        self.gates.append(gate_dict)
    
    def parse_file(self, file_path: str) -> Dict[str, Any]:
        """
        Parse a Qiskit Python file and convert to JSON format.
        
        Args:
            file_path: Path to the .py file containing Qiskit code
        
        Returns:
            Dictionary in the JSON format compatible with the simulator
        """
        with open(file_path, 'r') as f:
            source_code = f.read()
        
        return self.parse_code(source_code)
    
    def parse_code(self, source_code: str) -> Dict[str, Any]:
        """
        Parse Qiskit Python code string and convert to JSON format.
        
        Args:
            source_code: String containing Qiskit Python code
        
        Returns:
            Dictionary in the JSON format compatible with the simulator
        """
        # Reset state
        self.num_qubits = 0
        self.gates = []
        self.initial_state = None
        self.time_counter = 1
        self.gate_id_counter = 1
        self.errors = []
        
        try:
            # Parse the Python code into AST
            tree = ast.parse(source_code)
        except SyntaxError as e:
            raise ValueError(f"Invalid Python syntax: {e}")
        
        # Extract number of qubits
        self.num_qubits = self._extract_qubit_count(tree)
        if self.num_qubits is None:
            raise ValueError("Could not determine number of qubits from QuantumCircuit initialization")
        
        # Extract initial state if present
        self.initial_state = self._extract_initial_state(tree)
        
        # Extract all gate operations
        self._extract_gates_from_tree(tree)
        
        if self.errors:
            print(f"Warning: Encountered {len(self.errors)} errors during parsing:")
            for error in self.errors:
                print(f"  - {error}")
        
        # Build the JSON structure
        result = {
            "num_qubits": self.num_qubits,
            "gates": self.gates
        }
        
        if self.initial_state is not None:
            result["initial_state"] = self.initial_state
        
        return result
    
    def import_to_json(self, file_path: str, output_file: Optional[str] = None) -> Dict[str, Any]:
        """
        Import a Qiskit Python file and convert to JSON.
        
        Args:
            file_path: Path to the .py file
            output_file: Optional path to save the JSON output
        
        Returns:
            Dictionary in JSON format
        """
        result = self.parse_file(file_path)
        
        if output_file:
            with open(output_file, 'w') as f:
                json.dump(result, f, indent=2)
            print(f"JSON output written to {output_file}")
        
        return result
    
    def validate_and_import(self, file_path: str, output_file: Optional[str] = None) -> Dict[str, Any]:
        """
        Validate Qiskit Python code and import to JSON format.
        
        Args:
            file_path: Path to the .py file
            output_file: Optional path to save the JSON output
        
        Returns:
            Dictionary in JSON format
        
        Raises:
            ValueError: If validation fails
        """
        result = self.import_to_json(file_path, output_file)
        
        # Basic validation
        if result["num_qubits"] <= 0:
            raise ValueError("Invalid number of qubits")
        
        # Check qubit indices are valid
        for gate in result["gates"]:
            for qubit in gate["qubits"]:
                if qubit < 0 or qubit >= result["num_qubits"]:
                    raise ValueError(f"Invalid qubit index {qubit} for gate {gate['gate']} "
                                   f"(circuit has {result['num_qubits']} qubits)")
        
        # Check initial state dimensions if present
        if "initial_state" in result:
            expected_size = 2 ** result["num_qubits"]
            actual_size = len(result["initial_state"])
            if actual_size != expected_size:
                raise ValueError(f"Initial state size {actual_size} does not match "
                               f"expected size {expected_size} for {result['num_qubits']} qubits")
        return result
    
if __name__=="__main__":

    exporter = QiskitCircuitExporter(json_file="test/test.json")
    exporter.export("circuit.py")

    importer = QiskitCircuitImporter()
    json_data = importer.validate_and_import("circuit.py", "imported.json")

