import math

class QuantumGates:
    """Quantum gate definitions"""
    GATES = {
        'I': {
            'name': 'Identity',
            'matrix': [[1, 0], [0, 1]],
            'qubits': 1,
            'description': 'Identity gate - no operation'
        },
        'X': {
            'name': 'Pauli-X',
            'matrix': [[0, 1], [1, 0]],
            'qubits': 1,
            'description': 'NOT gate - flips qubit state'
        },
        'Y': {
            'name': 'Pauli-Y',
            'matrix': [[0, complex(0, -1)], [complex(0, 1), 0]],
            'qubits': 1,
            'description': 'Pauli-Y gate'
        },
        'Z': {
            'name': 'Pauli-Z',
            'matrix': [[1, 0], [0, -1]],
            'qubits': 1,
            'description': 'Phase flip gate'
        },
        'H': {
            'name': 'Hadamard',
            'matrix': [[1/math.sqrt(2), 1/math.sqrt(2)], [1/math.sqrt(2), -1/math.sqrt(2)]],
            'qubits': 1,
            'description': 'Creates superposition'
        },
        'S': {
            'name': 'S Gate',
            'matrix': [[1, 0], [0, complex(0, 1)]],
            'qubits': 1,
            'description': 'Phase gate (90° rotation)'
        },
        'T': {
            'name': 'T Gate',
            'matrix': [[1, 0], [0, complex(math.cos(math.pi/4), math.sin(math.pi/4))]],
            'qubits': 1,
            'description': 'T gate (45° rotation)'
        },
        'CNOT': {
            'name': 'Controlled-NOT',
            'matrix': [[1,0,0,0], [0,1,0,0], [0,0,0,1], [0,0,1,0]],
            'qubits': 2,
            'description': 'Controlled NOT gate'
        },
        'CZ': {
            'name': 'Controlled-Z',
            'matrix': [[1,0,0,0], [0,1,0,0], [0,0,1,0], [0,0,0,-1]],
            'qubits': 2,
            'description': 'Controlled Z gate'
        },
        'SWAP': {
            'name': 'SWAP',
            'matrix': [[1,0,0,0], [0,0,1,0], [0,1,0,0], [0,0,0,1]],
            'qubits': 2,
            'description': 'Swaps two qubits'
        },
        'CCNOT': {
            'name': 'Toffoli',
            'matrix': [
                [1,0,0,0,0,0,0,0], [0,1,0,0,0,0,0,0], [0,0,1,0,0,0,0,0], [0,0,0,1,0,0,0,0],
                [0,0,0,0,1,0,0,0], [0,0,0,0,0,1,0,0], [0,0,0,0,0,0,0,1], [0,0,0,0,0,0,1,0]
            ],
            'qubits': 3,
            'description': 'Controlled-Controlled-NOT gate'
        },
        'M': {
            'name': 'Measurement',
            'qubits': 1,
            'description': 'Measurement operation'
        }
    }