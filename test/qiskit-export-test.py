from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister, transpile
from qiskit_aer import AerSimulator
from numpy import pi

# Create quantum circuit
qc = QuantumCircuit(3)

# Initialize custom state
initial_state = [1.0+0.0j, 0.0+0.0j, 0.0+0.0j, 0.0+0.0j, 0.0+0.0j, 0.0+0.0j, 0.0+0.0j, 0.0+0.0j]
qc.initialize(initial_state, range(3))

# Apply gates (in order of execution time)
qc.h(0)  # Time: 0
qc.h(1)  # Time: 0
qc.h(2)  # Time: 0
qc.x(1)  # Time: 1
qc.h(2)  # Time: 2
qc.ccx(0, 1, 2)  # controls: [0, 1], target: 2  # Time: 3
qc.h(2)  # Time: 4
qc.x(1)  # Time: 5
qc.h(0)  # Time: 6
qc.h(1)  # Time: 6
qc.h(2)  # Time: 6
qc.x(0)  # Time: 7
qc.x(1)  # Time: 7
qc.x(2)  # Time: 7
qc.h(2)  # Time: 8
qc.ccx(0, 1, 2)  # controls: [0, 1], target: 2  # Time: 9
qc.h(2)  # Time: 10
qc.x(0)  # Time: 11
qc.x(1)  # Time: 11
qc.x(2)  # Time: 11
qc.h(0)  # Time: 12
qc.h(1)  # Time: 12
qc.h(2)  # Time: 12
qc.x(1)  # Time: 13
qc.h(2)  # Time: 14
qc.ccx(0, 1, 2)  # controls: [0, 1], target: 2  # Time: 15
qc.h(2)  # Time: 16
qc.x(1)  # Time: 17
qc.h(0)  # Time: 18
qc.h(1)  # Time: 18
qc.h(2)  # Time: 18
qc.x(0)  # Time: 19
qc.x(1)  # Time: 19
qc.x(2)  # Time: 19
qc.h(2)  # Time: 20
qc.ccx(0, 1, 2)  # controls: [0, 1], target: 2  # Time: 21
qc.h(2)  # Time: 22
qc.x(0)  # Time: 23
qc.x(1)  # Time: 23
qc.x(2)  # Time: 23
qc.h(0)  # Time: 24
qc.h(1)  # Time: 24
qc.h(2)  # Time: 24

qc.save_statevector()
# Visualize circuit
print(qc.draw())

# Execute circuit
simulator = AerSimulator()
qc_t = transpile(qc, simulator)
result = simulator.run(qc_t).result()
statevector = result.get_statevector(qc_t)
probabilities = statevector.probabilities_dict()
print('Final statevector:')
print(statevector)
print('Probabilities:')
print(probabilities)