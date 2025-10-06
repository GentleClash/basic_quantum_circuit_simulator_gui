from qutip import Qobj, Bloch, ptrace
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from typing import List


class BlochSphereVisualizer:
    """
    Multi-Qubit Bloch Sphere Visualization Algorithm
    =================================================
    
    This class visualizes n-qubit quantum states using multiple Bloch spheres,
    with one sphere per qubit showing the reduced (marginal) state of each qubit.
    
    ALGORITHM OVERVIEW
    ------------------
    For a given n-qubit state vector |ψ⟩ of length 2^n:
    
    Step 1: Construct Full System Density Matrix
        Compute: ρ = |ψ⟩⟨ψ|
        Result: 2^n × 2^n density matrix representing the entire quantum system
    
    Step 2: Extract Reduced Density Matrix for Each Qubit
        For each qubit i (where i = 0, 1, ..., n-1):
            Apply partial trace to obtain reduced density matrix:
            ρᵢ = Trⱼ≠ᵢ(ρ)
            
            This operation traces out (sums over) all qubits except qubit i,
            resulting in a 2×2 matrix describing only qubit i's state.
            
            Partial trace formula:
            ρᵢ[a,b] = Σₖ ρ[index(a,k), index(b,k)]
            where k ranges over all basis states of the other n-1 qubits
    
    Step 3: Convert Density Matrix to Bloch Vector
        For each 2×2 reduced density matrix ρᵢ, compute Bloch coordinates:
        
        Using Pauli matrices:
            σₓ = [[0, 1],    σᵧ = [[0, -i],   σᵧ = [[1,  0],
                  [1, 0]]          [i,  0]]         [0, -1]]
        
        Compute components via trace:
            u = Tr(ρᵢ · σₓ) = 2·Re(ρᵢ[0,1])
            v = Tr(ρᵢ · σᵧ) = 2·Im(ρᵢ[0,1])
            w = Tr(ρᵢ · σᵧ) = ρᵢ[0,0] - ρᵢ[1,1]
        
        Result: Bloch vector (u, v, w) in 3D space
    
    Step 4: Determine State Purity
        Calculate magnitude: |r| = √(u² + v² + w²)
        
        Interpretation:
            |r| = 1.0  →  Pure state (qubit not entangled with others)
            |r| < 1.0  →  Mixed state (qubit entangled with others)
            |r| = 0.0  →  Maximally mixed (maximally entangled)
    
    Step 5: Render Multiple Bloch Spheres
        For each qubit i:
            - Create a 3D Bloch sphere visualization
            - Plot the Bloch vector (u, v, w) as an arrow from origin
            - Display magnitude |r| to indicate entanglement level
            - Arrange spheres in a grid layout for multi-qubit systems
    
    Step 6: Update on State Evolution
        When quantum gates are applied:
            - Update state vector |ψ'⟩
            - Recompute all reduced density matrices
            - Update all Bloch sphere visualizations

    Limitation: This representation ignores quantum correlations (entanglement) between qubits. Each sphere shows what you would measure if you only had access to that single qubit.

    INTERPRETATION GUIDE
    --------------------
    Bloch Vector Position:
        • On sphere surface (|r|=1): Pure quantum state, no entanglement
        • Inside sphere (0<|r|<1): Mixed state, partially entangled
        • At origin (|r|=0): Maximally mixed, maximally entangled

    Bloch Vector Direction:
        • +Z axis (0,0,+1): State |0⟩ (north pole)
        • -Z axis (0,0,-1): State |1⟩ (south pole)
        • +X axis (+1,0,0): State |+⟩ = (|0⟩+|1⟩)/√2
        • -X axis (-1,0,0): State |−⟩ = (|0⟩-|1⟩)/√2
        • +Y axis (0,+1,0): State |+i⟩ = (|0⟩+i|1⟩)/√2
        • -Y axis (0,-1,0): State |-i⟩ = (|0⟩-i|1⟩)/√2
    
    EXAMPLES
    --------
    1. Single qubit |+⟩ = (|0⟩ + |1⟩)/√2
       → Bloch vector: (+1, 0, 0), magnitude: 1.0
       → Points along +X axis, pure state
    
    2. Product state |+⟩⊗|0⟩ = (|00⟩ + |10⟩)/√2
       → Qubit 0: (+1, 0, 0), magnitude: 1.0
       → Qubit 1: (0, 0, +1), magnitude: 1.0
       → Both pure states, separable (not entangled)
    
    3. Bell state |Φ+⟩ = (|00⟩ + |11⟩)/√2
       → Qubit 0: (0, 0, 0), magnitude: 0.0
       → Qubit 1: (0, 0, 0), magnitude: 0.0
       → Both at origin, maximally entangled
    
    4. Partially entangled: 0.9|00⟩ + 0.436|11⟩
       → Both qubits: (0, 0, 0.62), magnitude: 0.62
       → Inside sphere, partially entangled
    
    USAGE
    -----
        # Create visualizer with state vector
        state = [1/np.sqrt(2), 0, 0, 1/np.sqrt(2)]  # Bell state
        viz = BlochSphereVisualizer(state)
        
        # Display interactive visualization
        viz.visualize()
        
        # Mouse controls:
        # - Left drag: Rotate spheres
        # - Right drag: Zoom
        # - Middle drag: Pan
    
    REFERENCES
    ----------
    - Quantum density matrices: Nielsen & Chuang, "Quantum Computation and Quantum Information", Chapter 2 - 2.4.3
    - Partial trace: https://en.wikipedia.org/wiki/Partial_trace
    - Bloch sphere: https://en.wikipedia.org/wiki/Bloch_sphere

    """

    def __init__(self, state_vector: List[complex]):
        """
        Initialize with a state vector representing n qubits.

        Parameters:
        -----------
        state_vector : List[complex]
            State vector of length 2^n for n qubits
        """
        self.state_vector = np.array(state_vector, dtype=complex)
        self.n_qubits = int(np.log2(len(self.state_vector))) if len(self.state_vector) > 0 else 0

        # Validate input
        if 2**self.n_qubits != len(self.state_vector):
            raise ValueError("State vector length must be a power of 2")

        # Create QuTiP quantum object
        # dims structure: [[2,2,...,2], [1,1,...,1]] for n qubits
        dims = [[2]*self.n_qubits, [1]*self.n_qubits]
        self.qobj = Qobj(self.state_vector, dims=dims)

        # Normalize if needed
        self.qobj = self.qobj.unit()

    def visualize(self) -> Figure:
        """
        Visualize all qubits using QuTiP Bloch spheres.
        """
        # Calculate grid layout
        ncols = min(self.n_qubits, 3)
        nrows = int(np.ceil(self.n_qubits / ncols))

        # Create figure
        figsize = (5 * ncols, 4 * nrows)
        fig = plt.figure(figsize=figsize)
        fig.suptitle(f'{self.n_qubits}-Qubit State Visualization', 
                     fontsize=14, fontweight='bold')

        bloch_vectors = []

        for qubit_idx in range(self.n_qubits):
            # Step 2: Compute reduced density matrix using ptrace
            rho_reduced = ptrace(self.qobj, qubit_idx)

            # Create subplot with 3D projection
            ax = fig.add_subplot(nrows, ncols, qubit_idx + 1, projection='3d')

            bloch = Bloch(fig=fig, axes=ax)

            # Add state to Bloch sphere
            bloch.add_states(rho_reduced)
            bloch.zlabel = ['$|0\\rangle$', '$|1\\rangle$']
            bloch.render()

            # Set box aspect for proper sphere shape
            #ax.set_box_aspect([1, 1, 1])

            # Get Bloch vector for display
            if len(bloch.vectors) > 0:
                vec = bloch.vectors[0]
                u, v, w = vec[0], vec[1], vec[2]
                mag = np.sqrt(u**2 + v**2 + w**2)
                bloch_vectors.append((u, v, w, mag))

            # Set title
            ax.set_title(f'Qubit {qubit_idx}', fontsize=10, pad=10)

        plt.tight_layout()
        plt.show()

        return fig
    
