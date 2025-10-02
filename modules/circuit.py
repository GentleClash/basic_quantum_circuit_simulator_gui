from modules.complex_ import Complex
from typing import List, Dict
from modules.gates import QuantumGates
import random
import math

type _matrix =  List[List[Complex]]
type _state_vector = List[Complex]


class QuantumCircuit:

    """Quantum circuit implementation"""
    def __init__(self, num_qubits=3) -> None:
        self.num_qubits: int = num_qubits
        self.gates: List[Dict] = []
        self.initial_state: _state_vector = []
        self.state_vector: _state_vector = self.initialize_state()

    def initialize_state(self) -> _state_vector:
        if self.initial_state is not None:
            return self.initial_state[:]
        
        size = 2 ** self.num_qubits
        state = [Complex(0, 0) for _ in range(size)]
        state[0] = Complex(1, 0)  # |000...0⟩
        return state
    
    def set_initial_state(self, state_vector) -> None:
        """Set custom initial state"""
        if len(state_vector) == 2 ** self.num_qubits:
            self.initial_state = state_vector[:]
            self.state_vector = self.initialize_state()

    def add_gate(self, gate, qubits, time=0) -> None:
        self.gates.append({
            'gate': gate,
            'qubits': qubits if isinstance(qubits, list) else [qubits],
            'time': time
        })

    def measure_qubit(self, qubit_index) -> int:
        """Perform a measurement on a specific qubit, collapsing the state"""
        # Calculate probability of measuring |0⟩
        prob_0 = 0
        size = 2 ** self.num_qubits
        
        for i in range(size):
            # Check if this basis state has qubit_index in |0⟩ state
            # For n qubits, each basis state i represents a binary string of length n
            # where bit positions are numbered from 0 (rightmost/LSB) to n-1 (leftmost/MSB)
            # 
            # To check if qubit_index is in |0⟩ state in basis state i:
            # 1. Create a bitmask: 1 << (num_qubits - 1 - qubit_index)
            #    This shifts 1 to the bit position corresponding to qubit_index
            #    Example: for 3 qubits, qubit 1 -> mask = 1 << (3-1-1) = 1 << 1 = 2 (binary: 010)
            # 
            # 2. Apply bitwise AND: i & mask
            #    If the result is 0, then qubit_index is in |0⟩ state
            #    If the result is non-zero, then qubit_index is in |1⟩ state
            #    Example: i=5 (binary 101), mask=2 (binary 010) -> 101 & 010 = 000 = 0
            #    So qubit 1 is in |0⟩ state in basis state |101⟩
            #
            # 3. The 'not' operator inverts the boolean result:
            #    - If qubit is in |0⟩: (i & mask) = 0 -> not 0 = True
            #    - If qubit is in |1⟩: (i & mask) ≠ 0 -> not (non-zero) = False
            if not (i & (1 << (self.num_qubits - 1 - qubit_index))):
                
            # Add the probability amplitude squared (Born rule) to total |0⟩ probability
            # |amplitude|² gives the probability of measuring this basis state
                prob_0 += self.state_vector[i].magnitude() ** 2
        
        # Randomly collapse based on probability
        measurement_result = 0 if random.random() < prob_0 else 1
        
        # Collapse the state vector
        new_state: _state_vector = [Complex(0, 0) for _ in range(size)]
        norm = 0
        
        for i in range(size):
            # Extract the bit value for the specified qubit from state index i
            # For n qubits, bit positions are numbered from 0 (rightmost) to n-1 (leftmost)
            # We shift i right by (num_qubits - 1 - qubit_index) positions to move
            # the target qubit's bit to the least significant position, then mask with 1
            # Example: for 3 qubits, qubit 0 is at position 2, qubit 1 at position 1, qubit 2 at position 0
            # If i = 5 (binary 101) and qubit_index = 1:
            #   - Shift right by (3-1-1) = 1 position: 101 >> 1 = 10 (binary)
            #   - Mask with 1: 10 & 1 = 0, so qubit 1 is in state |0⟩
            qubit_bit = (i >> (self.num_qubits - 1 - qubit_index)) & 1
            
            if qubit_bit == measurement_result:
                new_state[i] = self.state_vector[i]
                norm += new_state[i].magnitude() ** 2
        
        # Renormalize
        if norm > 1e-10:
            norm_factor = 1.0 / math.sqrt(norm)
            for i in range(size):
                new_state[i] = Complex(
                    new_state[i].r * norm_factor,
                    new_state[i].i * norm_factor
                )
        
        self.state_vector = new_state
        return measurement_result

    def simulate(self) -> tuple[Dict[str, List], Dict[int, int]]:
        self.state_vector = self.initialize_state()       
        sorted_gates = sorted(self.gates, key=lambda g: g['time'])        
        measurement_results = {}
        
        for gate_op in sorted_gates:
            if gate_op['gate'] == 'M':
                # Perform measurement
                qubit = gate_op['qubits'][0]
                result = self.measure_qubit(qubit)
                measurement_results[qubit] = result
            else:
                self.apply_gate(gate_op['gate'], gate_op['qubits'])
        
        results = self.get_results()
        return results, measurement_results

    def apply_gate(self, gate_name, qubits) -> None:
        gate = QuantumGates.GATES.get(gate_name)
        if not gate or 'matrix' not in gate:
            return
        
        matrix = self.expand_gate_matrix(gate['matrix'], qubits)
        self.state_vector = self.multiply_matrix_vector(matrix, self.state_vector)

    def expand_gate_matrix(self, gate_matrix, qubits) -> _matrix:
        size = 2 ** self.num_qubits
        expanded = [[Complex(0, 0) for _ in range(size)] for _ in range(size)]
        
        for i in range(size):
            for j in range(size):
                expanded[i][j] = self.get_matrix_element(gate_matrix, qubits, i, j)
        
        return expanded
    
    def get_matrix_element(self, gate_matrix, qubits, row, col) -> Complex:
        gate_size = len(gate_matrix)
        gate_bits = int(math.log2(gate_size))
        
        gate_row = 0
        gate_col = 0
        non_gate_bits_match = True
        
        for i in range(self.num_qubits):
            # Extract the i-th qubit state from the row and column indices
            # For n qubits, bit position is counted from right (LSB) to left (MSB)
            row_bit = (row >> (self.num_qubits - 1 - i)) & 1
            col_bit = (col >> (self.num_qubits - 1 - i)) & 1
            
            # Construct the row/column indices for the gate matrix
            # by placing this qubit's bit at the correct position
            # in the smaller gate matrix coordinate system
            if i in qubits:
                gate_qubit_index = qubits.index(i)
                gate_row |= (row_bit << (gate_bits - 1 - gate_qubit_index))
                gate_col |= (col_bit << (gate_bits - 1 - gate_qubit_index))

            # This qubit is affected by the gate operation
            # Map this qubit's position to its position in the gate matrix
            else:
                if row_bit != col_bit:
                    non_gate_bits_match = False
                    break
        
        if not non_gate_bits_match:
            return Complex(0, 0)
        
        matrix_val = gate_matrix[gate_row][gate_col]
        if isinstance(matrix_val, complex):
            return Complex(matrix_val.real, matrix_val.imag)
        return Complex(matrix_val, 0)

    def multiply_matrix_vector(self, matrix, vector) -> _state_vector:
        result: _state_vector = [Complex(0, 0) for _ in range(len(vector))]

        for i in range(len(matrix)):
            for j in range(len(vector)):
                result[i] = result[i].add(matrix[i][j].multiply(vector[j]))
        
        return result
    
    
    def get_results(self) -> Dict[str, List]:
        probabilities: List[float] = [amp.magnitude() ** 2 for amp in self.state_vector]
        state_labels: List[str] = ['|' + bin(i)[2:].zfill(self.num_qubits) + '⟩' 
                       for i in range(len(self.state_vector))]
        
        return {
            'state_vector': self.state_vector,
            'probabilities': probabilities,
            'state_labels': state_labels
        }
