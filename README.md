# Basic Quantum Simulator with GUI

A quantum circuit simulator with an interactive graphical user interface built using Python and Tkinter. This simulator allows you to design, simulate, and visualize quantum circuits with multiple qubits and various quantum gates.

## Features

- **Interactive Circuit Design**: Visual circuit builder with drag-and-drop gate placement
- **Multiple Quantum Gates**: Support for single-qubit, two-qubit, and three-qubit gates
- **Custom Initial States**: Set arbitrary initial quantum states for qubits
- **State Visualization**: Real-time visualization of quantum state vectors and probabilities
- **Measurement Operations**: Perform quantum measurements with state collapse
- **Circuit Import/Export**: Save and load circuits in JSON format

## Installation

### Prerequisites

- Python 3.10 or higher
- Tkinter (usually included with Python)

### Running the Simulator

```bash
python basic_quantum_sim.py
```

## Quantum Gates Implemented

### Single-Qubit Gates

#### 1. **Identity Gate (I)**
The identity gate leaves the qubit unchanged.

**Matrix representation:**
$$
\begin{pmatrix} 1 & 0 \\ 0 & 1 \end{pmatrix}
$$

#### 2. **Pauli-X Gate (X)**
The Pauli-X gate is the quantum equivalent of the classical NOT gate. It flips the state of a qubit.

**Matrix representation:**
$$
\begin{pmatrix} 0 & 1 \\ 1 & 0 \end{pmatrix}
$$

**Action:**
$$
X|0\rangle = |1\rangle, \quad X|1\rangle = |0\rangle
$$

**Why:** Fundamental for bit-flip operations in quantum algorithms.

#### 3. **Pauli-Y Gate (Y)**
The Pauli-Y gate performs a rotation around the Y-axis of the Bloch sphere.

**Matrix representation:**
$$
\begin{pmatrix} 0 & -i \\ i & 0 \end{pmatrix}
$$

**Action:**
$$
Y|0\rangle = i|1\rangle, \quad Y|1\rangle = -i|0\rangle
$$

**Why:** Combines bit-flip and phase-flip operations, useful for creating specific superpositions with complex amplitudes.

#### 4. **Pauli-Z Gate (Z)**
The Pauli-Z gate is a phase-flip gate that leaves $|0\rangle$ unchanged but applies a phase of $-1$ to $|1\rangle$.

**Matrix representation:**
$$
 \begin{pmatrix} 1 & 0 \\ 0 & -1 \end{pmatrix}
$$

**Action:**
$$
Z|0\rangle = |0\rangle, \quad Z|1\rangle = -|1\rangle
$$

**Why:** Essential for phase operations and quantum error correction.

#### 5. **Hadamard Gate (H)**
The Hadamard gate creates an equal superposition from basis states.

**Matrix representation:**
$$
\frac{1}{\sqrt{2}} \begin{pmatrix} 1 & 1 \\ 1 & -1 \end{pmatrix}
$$

**Action:**
$$
H|0\rangle = \frac{|0\rangle + |1\rangle}{\sqrt{2}} = |+\rangle
$$
$$
H|1\rangle = \frac{|0\rangle - |1\rangle}{\sqrt{2}} = |-\rangle
$$

**Why:** Fundamental for creating superpositions; us in almost every quantum algorithm including quantum Fourier transform and Grover's algorithm.

#### 6. **S Gate (Phase Gate)**
The S gate applies a 90° phase rotation.

**Matrix representation:**
$$
 \begin{pmatrix} 1 & 0 \\ 0 & i \end{pmatrix}
$$

**Action:**
$$
S|0\rangle = |0\rangle, \quad S|1\rangle = i|1\rangle
$$

**Relation to Z gate:**
$$
S^2 = Z
$$

**Why:** Used for precise phase control in quantum algorithms. The phase shift of $\pi/2$ (90°) is crucial for quantum Fourier transforms and phase estimation algorithms.

#### 7. **T Gate (π/8 Gate)**
The T gate applies a 45° phase rotation.

**Matrix representation:**
$$
\begin{pmatrix} 1 & 0 \\ 0 & e^{i\pi/4} \end{pmatrix} = \begin{pmatrix} 1 & 0 \\ 0 & \frac{1+i}{\sqrt{2}} \end{pmatrix}
$$

**Action:**
$$
T|0\rangle = |0\rangle, \quad T|1\rangle = e^{i\pi/4}|1\rangle
$$

**Relation to S gate:**
$$
T^2 = S, \quad T^4 = Z
$$

**Why:** Provides finer phase control than the S gate. Part of the universal gate set {H, T, CNOT} for quantum computation. The phase shift of $\pi/4$ (45°) is essential for implementing arbitrary single-qubit rotations.

### Two-Qubit Gates

#### 8. **CNOT Gate (Controlled-NOT)**
The CNOT gate flips the target qubit if and only if the control qubit is $|1\rangle$.

**Matrix representation:**
$$
\begin{pmatrix} 
1 & 0 & 0 & 0 \\
0 & 1 & 0 & 0 \\
0 & 0 & 0 & 1 \\
0 & 0 & 1 & 0
\end{pmatrix}
$$

**Action on basis states:**
$$
\text{CNOT}|00\rangle = |00\rangle, \quad \text{CNOT}|01\rangle = |01\rangle
$$
$$
\text{CNOT}|10\rangle = |11\rangle, \quad \text{CNOT}|11\rangle = |10\rangle
$$

**Why:** Creates entanglement between qubits. Used to generate Bell states and is essential for quantum error correction and quantum teleportation.

#### 9. **CZ Gate (Controlled-Z)**
The CZ gate applies a Z gate to the target qubit if the control qubit is $|1\rangle$.

**Matrix representation:**
$$
 \begin{pmatrix} 
1 & 0 & 0 & 0 \\
0 & 1 & 0 & 0 \\
0 & 0 & 1 & 0 \\
0 & 0 & 0 & -1
\end{pmatrix}
$$

**Action:**
$$
\text{CZ}|11\rangle = -|11\rangle
$$

**Why:** Symmetrical controlled operation useful for phase kickback and certain quantum algorithms. Equivalent to applying Hadamard before and after a CNOT.

#### 10. **SWAP Gate**
The SWAP gate exchanges the states of two qubits.

**Matrix representation:**
$$
\begin{pmatrix} 
1 & 0 & 0 & 0 \\
0 & 0 & 1 & 0 \\
0 & 1 & 0 & 0 \\
0 & 0 & 0 & 1
\end{pmatrix}
$$

**Action:**
$$
\text{SWAP}|01\rangle = |10\rangle, \quad \text{SWAP}|10\rangle = |01\rangle
$$

**Why:** Necessary for moving quantum information between non-adjacent qubits in architectures with limited connectivity.

### Three-Qubit Gates

#### 11. **CCNOT Gate (Toffoli Gate)**
The Toffoli gate is a controlled-controlled-NOT gate. It flips the target qubit only if both control qubits are $|1\rangle$.

**Matrix representation:**
$$
\begin{pmatrix} 
1 & 0 & 0 & 0 & 0 & 0 & 0 & 0 \\
0 & 1 & 0 & 0 & 0 & 0 & 0 & 0 \\
0 & 0 & 1 & 0 & 0 & 0 & 0 & 0 \\
0 & 0 & 0 & 1 & 0 & 0 & 0 & 0 \\
0 & 0 & 0 & 0 & 1 & 0 & 0 & 0 \\
0 & 0 & 0 & 0 & 0 & 1 & 0 & 0 \\
0 & 0 & 0 & 0 & 0 & 0 & 0 & 1 \\
0 & 0 & 0 & 0 & 0 & 0 & 1 & 0
\end{pmatrix}
$$

**Action:**
$$
\text{CCNOT}|11x\rangle = |11\bar{x}\rangle
$$

where $\bar{x}$ denotes the NOT of $x$.

**Why:** Reversible classical computation. Can implement any classical boolean function. Used in quantum arithmetic and Grover's algorithm.

## Mathematical Framework

### State Vector Representation

A quantum system with $n$ qubits is represented by a state vector $|\psi\rangle$ in a $2^n$-dimensional Hilbert space:

$$
|\psi\rangle = \sum_{i=0}^{2^n-1} \alpha_i |i\rangle
$$

where $\alpha_i \in \mathbb{C}$ are complex amplitudes satisfying the normalization condition:

$$
\sum_{i=0}^{2^n-1} |\alpha_i|^2 = 1
$$

### Complex Number Operations

The simulator implements custom complex number arithmetic:

**Addition:**
$$
(a + bi) + (c + di) = (a + c) + (b + d)i
$$

**Multiplication:**
$$
(a + bi) \cdot (c + di) = (ac - bd) + (ad + bc)i
$$

**Magnitude:**
$$
|a + bi| = \sqrt{a^2 + b^2}
$$


### Gate Application via Matrix Expansion

For a gate $G$ acting on qubits $q_1, q_2, \ldots, q_k$ in an $n$-qubit system, the full system operator is:

$$
U = I_{q_0} \otimes \cdots \otimes G_{q_1, \ldots, q_k} \otimes \cdots \otimes I_{q_{n-1}}
$$

where $I$ is the identity operator for qubits not affected by the gate, and $\otimes$ is the tensor product.

The implementation computes matrix elements as:

$$
U_{ij} = \begin{cases}
G_{i'j'} & \text{if non-target bits of } i \text{ and } j \text{ match} \\
0 & \text{otherwise}
\end{cases}
$$

where $i'$ and $j'$ are the indices extracted from bits corresponding to target qubits.

**Why:** This approach avoids explicitly computing tensor products, which would be memory-intensive for large qubit systems.

### Quantum Measurement

Measurement of qubit $q$ projects the state vector onto the $|0\rangle$ or $|1\rangle$ subspace.

**Probability of measuring |0⟩:**
$$
P(0) = \sum_{i: \text{bit } q \text{ of } i = 0} |\alpha_i|^2
$$

**State collapse:**
After measuring outcome $m \in \{0, 1\}$:

$$
|\psi'\rangle = \frac{1}{\sqrt{P(m)}} \sum_{i: \text{bit } q \text{ of } i = m} \alpha_i |i\rangle
$$

The normalization factor $\frac{1}{\sqrt{P(m)}}$ ensures the collapsed state remains normalized.

## Usage Guide

### Building a Circuit

1. **Select Number of Qubits**: Use the dropdown at the top
2. **Add Gates**: Click on gate buttons and then click on the circuit grid
3. **Set Initial State** (optional): Use "Set Initial State" button
4. **Simulate**: Click "Simulate Circuit"

### Example: Creating a Bell State

To create the Bell state $\frac{|00\rangle + |11\rangle}{\sqrt{2}}$:

1. Set 2 qubits
2. Apply Hadamard (H) gate to qubit 0
3. Apply CNOT gate with control=0, target=1
4. Simulate

The mathematical evolution:
$$
|00\rangle \xrightarrow{H \otimes I} \frac{|00\rangle + |10\rangle}{\sqrt{2}} \xrightarrow{\text{CNOT}} \frac{|00\rangle + |11\rangle}{\sqrt{2}}
$$

### Saving and Loading Circuits

- **Save**: File → Save Circuit (saves as JSON)
- **Load**: File → Load Circuit

## Implementation Details

### Algorithm Complexity

- **State vector size**: $O(2^n)$ for $n$ qubits
- **Gate application**: $O(4^n)$ for applying a gate to the full state vector
- **Memory usage**: $O(2^n)$ complex numbers

**Limitation**: This simulator is practical for up to ~15-20 qubits on typical hardware due to exponential scaling.

### Code Structure

- **Complex class**: Custom complex number implementation
- **QuantumGates class**: Static gate definitions
- **QuantumCircuit class**: Circuit simulation engine
- **QuantumSimulatorGUI class**: Tkinter-based user interface

## Known Limitations

- Limited to 8 qubits due to memory constraints
- No noise modeling (ideal quantum computer simulation)
- No visualization 
- No optimization for sparse circuits

## Future Enhancements

- Add more quantum gates (Fredkin, custom rotations)
- Implement quantum algorithms (Grover, Shor, QFT)
- Add noise models for realistic simulation
- Improve performance with sparse matrix representations

## License

GNU General Public License v3.0 - See LICENSE file for details

## Contributing

Contributions are welcome! Please feel free to submit pull requests or open issues for bugs and feature requests.
