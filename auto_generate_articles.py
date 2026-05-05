"""
EasyPhysics Article Workflow
============================

A semi-autonomous local-LLM editorial workflow for drafting accessible,
scientifically careful fundamental-physics wiki articles.

Design goals
------------
- One folder per article.
- Durable artifacts: outline, draft, claims, sources, reviews, term candidates.
- One full treatment per article per pass; no endless revision loop on a single article.
- Skip articles that already score >= 9/10 on both rigor and accessibility.
- Encourage creative intuitive nomenclature while marking standard terms as {standard term}.
- Prefer stable, accepted physics explanations over "latest" or speculative sources.

Suggested install
-----------------
pip install langchain-ollama langchain-community duckduckgo-search pyyaml

Before running
--------------
1. Make sure Ollama is running.
2. Make sure qwen3:8b is pulled:
   ollama pull qwen3:8b
3. Adjust BASE_DIR / ARTICLE_ROOT if needed.

Run
---
python article_workflow.py

Optional examples
-----------------
python article_workflow.py --max-articles 3
python article_workflow.py --topic "Quantum superposition analogized as acoustic chords on a guitar string"
python article_workflow.py --force-finished
"""

from __future__ import annotations

import argparse
import json
import multiprocessing as mp
import os
import queue
import re
import textwrap
import time
import traceback
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import subprocess

try:
    import yaml
except ImportError as exc:
    raise SystemExit(
        "Missing dependency: PyYAML. Install with: pip install pyyaml"
    ) from exc

from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_community.tools import DuckDuckGoSearchRun


# =============================================================================
# 1. Configuration
# =============================================================================

BASE_DIR = Path(r"C:\Projects\EasyPhysics")
ARTICLE_ROOT = BASE_DIR / "AgentTasks" / "generated_articles"
GLOBAL_ARTIFACT_DIR = BASE_DIR / "AgentTasks" / "article_workflow_globals"
GLOBAL_LOG_DIR = BASE_DIR / "AgentTasks" / "logs" / "article_workflow"

ARTICLE_ROOT.mkdir(parents=True, exist_ok=True)
GLOBAL_ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
GLOBAL_LOG_DIR.mkdir(parents=True, exist_ok=True)

MODEL_NAME = "qwen3:8b"

# Arc A750 stability note:
# If Ollama/Level Zero/SYCL/driver execution "flatlines" instead of raising a Python
# exception, the Python call can hang forever. We run each LLM call in a child process
# and kill that process if it exceeds LLM_TIMEOUT_SECONDS.
LLM_OPTIONS = {
    "temperature": 0.25,
    "top_p": 0.85,
    "num_ctx": 8192,
    "num_predict": 2048,
    "num_batch": 32,
}
LLM_TIMEOUT_SECONDS = 8 * 60
LLM_MAX_RETRIES = 0

RESET_OLLAMA_MODEL_ON_TIMEOUT = True

NODE_OPTION_OVERRIDES = {
    "term_collector": {"num_predict": 768},
    "claim_extractor": {"num_predict": 1024},
    "claim_checker": {"num_predict": 768},
    "accessibility_judge": {"num_predict": 1024},
    "rigor_judge": {"num_predict": 1024},
}

search_tool = DuckDuckGoSearchRun()

PASSING_SCORE = 9
MAX_CLAIMS_TO_SEARCH_PER_PASS = 2
MAX_SEARCH_RESULT_CHARS_PER_CLAIM = 1800
MAX_CONTEXT_CHARS = 36000


TOPICS_TO_GENERATE = [
  "Noether's second theorem",
    "Lagrangian",
    "Hamiltonian",
    "Least action principle",
    "Variational principle",
    "Eigenvalue",
    "Eigenvector",
    "Eigenstate",
    "Scattering",
    "Dispersion",
    "Polarization",
    "Coherence",
    "Decoherence",
    "Hilbert space",
    "Bra-ket notation",
    "Projection",
    "Quantum measurement",
    "Observable operator",
    "Hermitian operator",
    "Unitary evolution",
    "Schrodinger equation",
    "Time-dependent Schrodinger equation",
    "Time-independent Schrodinger equation",
    "Hamiltonian operator",
    "Energy eigenstate",

]

TOPICS_TO_GENERATE_BACKLOG = [
    "Physics",
    "Physical state",
    "System",
    "Observable",
    "Measurement",
    "Prediction",
    "Model",
    "Theory",
    "Law of nature",
    "Principle",
    "Approximation",
    "Idealization",
    "Scale",
    "Order of magnitude",
    "Dimensional analysis",
    "Units",
    "Constants of nature",
    "Degrees of freedom",
    "Constraint",
    "Initial condition",
    "Boundary condition",
    "Reference frame",
    "Coordinate system",
    "Transformation",
    "Invariance",
    "Symmetry",
    "Conservation law",
    "Energy",
    "Momentum",
    "Angular momentum",
    "Mass",
    "Charge",
    "Action",
    "Equation of motion",
    "State space",
    "Phase space",
    "Configuration space",
    "Vector space",
    "Basis",
    "Linear combination",
    "Inner product",
    "Norm",
    "Metric",
    "Tensor",
    "Scalar",
    "Vector",
    "Matrix",
    "Operator",
    "Complex number",
    "Complex phase",
    "Amplitude",
    "Probability",
    "Probability distribution",
    "Expectation value",
    "Correlation",
    "Causality",
    "Determinism",
    "Randomness",
    "Emergence",
    "Reductionism",
    "Effective theory",
    "Fundamental theory",
    "Classical physics",
    "Quantum physics",
    "Relativity",
    "Field theory",
    "Particle physics",
    "Cosmology",
    "Statistical physics",
    "Thermodynamics",
    "Mechanics",
    "Kinematics",
    "Dynamics",
    "Position",
    "Displacement",
    "Distance",
    "Velocity",
    "Speed",
    "Acceleration",
    "Force",
    "Inertia",
    "Newton's laws",
    "Newton's first law",
    "Newton's second law",
    "Newton's third law",
    "Impulse",
    "Work",
    "Power",
    "Kinetic energy",
    "Potential energy",
    "Mechanical energy",
    "Friction",
    "Drag",
    "Normal force",
    "Tension",
    "Torque",
    "Center of mass",
    "Moment of inertia",
    "Rigid body",
    "Rotation",
    "Orbital motion",
    "Circular motion",
    "Centripetal acceleration",
    "Harmonic oscillator",
    "Simple harmonic motion",
    "Damped oscillator",
    "Driven oscillator",
    "Resonance",
    "Pendulum",
    "Kepler's laws",
    "Two-body problem",
    "Many-body problem",
    "Stability",
    "Chaos",
    "Deterministic chaos",
    "Nonlinear dynamics",
    "Phase portrait",
    "Attractor",
    "Fluid",
    "Pressure",
    "Density",
    "Buoyancy",
    "Viscosity",
    "Turbulence",
    "Continuity equation",
    "Bernoulli principle",
    "Sound",
    "Wave",
    "Wavelength",
    "Frequency",
    "Period",
    "Wave speed",
    "Phase velocity",
    "Group velocity",
    "Standing wave",
    "Traveling wave",
    "Interference",
    "Constructive interference",
    "Destructive interference",
    "Diffraction",
    "Refraction",
    "Reflection",
    "Fourier analysis",
    "Fourier transform",
    "Normal mode",
    "Electromagnetism",
    "Electric charge",
    "Electric field",
    "Magnetic field",
    "Electromagnetic field",
    "Electric potential",
    "Voltage",
    "Current",
    "Resistance",
    "Capacitance",
    "Inductance",
    "Coulomb's law",
    "Gauss's law",
    "Ampere's law",
    "Faraday's law",
    "Lenz's law",
    "Maxwell's equations",
    "Electromagnetic wave",
    "Light",
    "Photon",
    "Radiation",
    "Spectrum",
    "Electromagnetic spectrum",
    "Radio wave",
    "Microwave",
    "Infrared light",
    "Visible light",
    "Ultraviolet light",
    "X-ray",
    "Gamma ray",
    "Optics",
    "Geometric optics",
    "Wave optics",
    "Lens",
    "Mirror",
    "Index of refraction",
    "Total internal reflection",
    "Blackbody radiation",
    "Photoelectric effect",
    "Thermodynamic system",
    "Temperature",
    "Heat",
    "Entropy",
    "Enthalpy",
    "Free energy",
    "Internal energy",
    "Thermal equilibrium",
    "Zeroth law of thermodynamics",
    "First law of thermodynamics",
    "Second law of thermodynamics",
    "Third law of thermodynamics",
    "Heat engine",
    "Carnot cycle",
    "Refrigerator",
    "Equation of state",
    "Ideal gas",
    "Pressure-volume work",
    "Microstate",
    "Macrostate",
    "Boltzmann distribution",
    "Partition function",
    "Statistical ensemble",
    "Canonical ensemble",
    "Microcanonical ensemble",
    "Grand canonical ensemble",
    "Maxwell-Boltzmann statistics",
    "Fermi-Dirac statistics",
    "Bose-Einstein statistics",
    "Phase transition",
    "Critical point",
    "Order parameter",
    "Spontaneous symmetry breaking",
    "Renormalization group",
    "Universality",
    "Quantum state",
    "Wavefunction",
    "Superposition",
    "Quantum amplitude",
    "Quantum phase",
    "Born rule",
    "Ket",
    "Bra",
    "Ground state",
    "Excited state",
    "Quantum probability",
    "Quantum interference",
    "Double-slit experiment",
    "Wave-particle duality",
    "Quantum tunneling",
    "Potential barrier",
    "Quantum well",
    "Bound state",
    "Free particle",
    "Plane wave",
    "Wave packet",
    "Uncertainty principle",
    "Position-momentum uncertainty",
    "Energy-time uncertainty",
    "Commutation",
    "Commutator",
    "Canonical commutation relation",
    "Spin",
    "Spinor",
    "Pauli matrices",
    "Angular momentum quantization",
    "Orbital angular momentum",
    "Spin angular momentum",
    "Magnetic moment",
    "Stern-Gerlach experiment",
    "Quantum harmonic oscillator",
    "Creation operator",
    "Annihilation operator",
    "Ladder operator",
    "Number operator",
    "Fock space",
    "Occupation number",
    "Identical particles",
    "Exchange symmetry",
    "Fermion",
    "Boson",
    "Pauli exclusion principle",
    "Bose-Einstein condensate",
    "Entanglement",
    "Separable state",
    "Bell state",
    "Bell's theorem",
    "Bell inequality",
    "EPR paradox",
    "Locality",
    "Nonlocal correlation",
    "Hidden variable",
    "Decoherence",
    "Density matrix",
    "Pure state",
    "Mixed state",
    "Quantum Zeno effect",
    "Path integral",
    "Feynman path integral",
    "Action phase",
    "Classical limit",
    "Correspondence principle",
    "Quantum information",
    "Qubit",
    "Quantum gate",
    "Quantum circuit",
    "Quantum algorithm",
    "Quantum error correction",
    "No-cloning theorem",
    "Quantum teleportation",
    "Quantum field",
    "Field",
    "Classical field",
    "Scalar field",
    "Vector field",
    "Spinor field",
    "Gauge field",
    "Field excitation",
    "Particle as field excitation",
    "Vacuum",
    "Quantum vacuum",
    "Vacuum fluctuation",
    "Zero-point energy",
    "Propagator",
    "Virtual particle",
    "Feynman diagram",
    "Vertex",
    "Coupling",
    "Coupling constant",
    "Interaction term",
    "Perturbation theory",
    "Nonperturbative physics",
    "Scattering amplitude",
    "Cross section",
    "Decay rate",
    "Renormalization",
    "Regularization",
    "Ultraviolet divergence",
    "Infrared divergence",
    "Running coupling",
    "Effective field theory",
    "Lagrangian density",
    "Canonical quantization",
    "Path-integral quantization",
    "Gauge symmetry",
    "Local symmetry",
    "Global symmetry",
    "Gauge freedom",
    "Gauge fixing",
    "Gauge transformation",
    "Connection",
    "Curvature",
    "Field strength tensor",
    "Covariant derivative",
    "Fiber bundle",
    "Lie group",
    "Lie algebra",
    "Generator",
    "Representation",
    "Fundamental representation",
    "Adjoint representation",
    "U(1) symmetry",
    "SU(2) symmetry",
    "SU(3) symmetry",
    "Lorentz symmetry",
    "Poincare symmetry",
    "CPT symmetry",
    "Parity",
    "Charge conjugation",
    "Time reversal symmetry",
    "Chirality",
    "Helicity",
    "Anomaly",
    "Gauge anomaly",
    "Anomaly cancellation",
    "Spontaneous symmetry breaking in field theory",
    "Goldstone boson",
    "Goldstone theorem",
    "Higgs mechanism",
    "Higgs field",
    "Higgs boson",
    "Vacuum expectation value",
    "Mass generation",
    "Yukawa coupling",
    "Standard Model",
    "Standard Model particle chart",
    "Matter particle",
    "Force carrier",
    "Fermion generation",
    "Lepton",
    "Quark",
    "Gauge boson",
    "Electron",
    "Muon",
    "Tau",
    "Electron neutrino",
    "Muon neutrino",
    "Tau neutrino",
    "Neutrino",
    "Up quark",
    "Down quark",
    "Charm quark",
    "Strange quark",
    "Top quark",
    "Bottom quark",
    "Photon",
    "Gluon",
    "W boson",
    "Z boson",
    "Higgs boson",
    "Antiparticle",
    "Antimatter",
    "Positron",
    "Baryon",
    "Meson",
    "Hadron",
    "Proton",
    "Neutron",
    "Pion",
    "Kaon",
    "Color charge",
    "Color confinement",
    "Quark confinement",
    "Asymptotic freedom",
    "Quantum chromodynamics",
    "Strong interaction",
    "Gluon field",
    "Hadronization",
    "Parton",
    "Sea quark",
    "Valence quark",
    "Nuclear force",
    "Residual strong force",
    "Electroweak interaction",
    "Weak interaction",
    "Weak isospin",
    "Hypercharge",
    "Electroweak symmetry breaking",
    "Charged current",
    "Neutral current",
    "Beta decay",
    "Neutrino oscillation",
    "Neutrino mass",
    "CKM matrix",
    "PMNS matrix",
    "Flavor",
    "Flavor mixing",
    "Particle generation",
    "Matter-antimatter asymmetry",
    "CP violation",
    "Baryon number",
    "Lepton number",
    "Baryogenesis",
    "Atomic physics",
    "Atom",
    "Nucleus",
    "Electron shell",
    "Orbital",
    "Quantum orbital",
    "Energy level",
    "Spectral line",
    "Ionization",
    "Emission",
    "Absorption",
    "Selection rule",
    "Fine structure",
    "Hyperfine structure",
    "Zeeman effect",
    "Stark effect",
    "Molecule",
    "Chemical bond",
    "Covalent bond",
    "Ionic bond",
    "Metallic bond",
    "Band structure",
    "Conductor",
    "Insulator",
    "Semiconductor",
    "Superconductor",
    "Cooper pair",
    "BCS theory",
    "Nuclear physics",
    "Atomic nucleus",
    "Nucleon",
    "Isotope",
    "Binding energy",
    "Mass defect",
    "Radioactivity",
    "Alpha decay",
    "Beta decay",
    "Gamma decay",
    "Half-life",
    "Nuclear fission",
    "Nuclear fusion",
    "Chain reaction",
    "Stellar fusion",
    "Deuterium",
    "Tritium",
    "Helium nucleus",
    "Nuclear shell model",
    "Liquid drop model",
    "Special relativity",
    "Speed of light",
    "Invariant speed",
    "Spacetime",
    "Event",
    "Worldline",
    "Light cone",
    "Proper time",
    "Proper length",
    "Time dilation",
    "Length contraction",
    "Relativity of simultaneity",
    "Lorentz transformation",
    "Minkowski diagram",
    "Minkowski spacetime",
    "Spacetime interval",
    "Four-vector",
    "Four-velocity",
    "Four-momentum",
    "Energy-momentum relation",
    "Mass-energy equivalence",
    "Relativistic momentum",
    "Relativistic energy",
    "Rapidity",
    "Twin paradox",
    "Causality in relativity",
    "General relativity",
    "Equivalence principle",
    "Gravity",
    "Gravitational field",
    "Spacetime curvature",
    "Geodesic",
    "Metric tensor",
    "Stress-energy tensor",
    "Einstein field equations",
    "Curved spacetime",
    "Christoffel symbol",
    "Riemann curvature tensor",
    "Ricci tensor",
    "Ricci scalar",
    "Cosmological constant",
    "Gravitational time dilation",
    "Gravitational redshift",
    "Gravitational lensing",
    "Tidal force",
    "Schwarzschild solution",
    "Black hole",
    "Event horizon",
    "Singularity",
    "Photon sphere",
    "Accretion disk",
    "Kerr black hole",
    "Rotating black hole",
    "Frame dragging",
    "Gravitational wave",
    "Binary inspiral",
    "LIGO",
    "Hawking radiation",
    "Black hole entropy",
    "Bekenstein-Hawking entropy",
    "Information paradox",
    "Holographic principle",
    "Cosmology",
    "Universe",
    "Observable universe",
    "Cosmic horizon",
    "Big Bang",
    "Cosmic expansion",
    "Scale factor",
    "Hubble parameter",
    "Hubble law",
    "Redshift",
    "Cosmic microwave background",
    "Inflation",
    "Cosmic inflation",
    "Primordial fluctuation",
    "Structure formation",
    "Galaxy formation",
    "Dark matter",
    "Dark energy",
    "Lambda-CDM model",
    "Matter density",
    "Radiation density",
    "Critical density",
    "Flat universe",
    "Open universe",
    "Closed universe",
    "Friedmann equation",
    "FLRW metric",
    "Cosmic time",
    "Recombination",
    "Nucleosynthesis",
    "Big Bang nucleosynthesis",
    "Baryon acoustic oscillation",
    "Cosmic variance",
    "Multiverse",
    "Anthropic principle",
    "Planck scale",
    "Planck length",
    "Planck time",
    "Planck mass",
    "Quantum gravity",
    "Black hole thermodynamics",
    "Loop quantum gravity",
    "String theory",
    "Brane",
    "Extra dimension",
    "Supersymmetry",
    "Superpartner",
    "Grand unified theory",
    "Unification",
    "Theory of everything",
    "Hierarchy problem",
    "Naturalness",
    "Fine-tuning",
    "Vacuum energy problem",
    "Cosmological constant problem",
    "Strong CP problem",
    "Axion",
    "Magnetic monopole",
    "Proton decay",
    "Sterile neutrino",
    "Majorana particle",
    "Dirac particle",
    "Dirac equation",
    "Klein-Gordon equation",
    "Maxwell field",
    "Yang-Mills theory",
    "Yang-Mills field",
    "Non-Abelian gauge theory",
    "Abelian gauge theory",
    "Topological defect",
    "Soliton",
    "Instanton",
    "Skyrmion",
    "Berry phase",
    "Aharonov-Bohm effect",
    "Topology in physics",
    "Topological phase",
    "Topological order",
    "Chern number",
    "Quantum Hall effect",
    "Fractional quantum Hall effect",
    "Plasma",
    "Ion",
    "Electron gas",
    "Debye shielding",
    "Magnetohydrodynamics",
    "Astrophysics",
    "Star",
    "Stellar structure",
    "Stellar evolution",
    "White dwarf",
    "Neutron star",
    "Pulsar",
    "Supernova",
    "Black hole formation",
    "Main sequence",
    "Hydrostatic equilibrium",
    "Degeneracy pressure",
    "Electron degeneracy pressure",
    "Neutron degeneracy pressure",
    "Chandrasekhar limit",
    "Tolman-Oppenheimer-Volkoff limit",
    "Escape velocity",
    "Orbital energy",
    "Virial theorem",
    "Gravitational collapse",
    "Accretion",
    "Galaxy",
    "Dark matter halo",
    "Cluster of galaxies",
    "Cosmic web",
    "Mathematical group",
    "Group theory",
    "Rotation group",
    "SO(3)",
    "SU(2)",
    "Spin group",
    "Lorentz group",
    "Poincare group",
    "Representation theory",
    "Symmetry breaking",
    "Discrete symmetry",
    "Continuous symmetry",
    "Translation symmetry",
    "Rotational symmetry",
    "Boost symmetry",
    "Scale symmetry",
    "Conformal symmetry",
    "Supersymmetry algebra",
    "Grassmann number",
    "Clifford algebra",
    "Gamma matrix",
    "Pauli spinor",
    "Dirac spinor",
    "Weyl spinor",
    "Majorana spinor",
    "Chiral spinor",
    "Lattice",
    "Lattice field theory",
    "Lattice QCD",
    "Fermion doubling",
    "Wilson fermion",
    "Staggered fermion",
    "Ginsparg-Wilson fermion",
    "Path integral on a lattice",
    "Continuum limit",
    "Cutoff",
    "Regularization scale",
    "Effective potential",
    "Scattering",
    "Elastic scattering",
    "Inelastic scattering",
    "Decay",
    "Conservation of charge",
    "Conservation of energy",
    "Conservation of momentum",
    "Conservation of angular momentum",
    "Conservation of baryon number",
    "Conservation of lepton number",
    "Approximate conservation law",
    "Selection rule",
    "Symmetry-allowed process",
    "Forbidden process",
    "Dimensional reduction",
    "Duality",
    "Wave equation",
    "Heat equation",
    "Laplace equation",
    "Poisson equation",
    "Continuity equation in physics",
    "Euler-Lagrange equation",
    "Hamilton's equations",
    "Poisson bracket",
    "Canonical transformation",
    "Symplectic geometry",
    "Classical limit of quantum mechanics",
    "Semiclassical approximation",
    "WKB approximation",
    "Gauge principle",
    "Minimal coupling",
    "Charge as response to symmetry",
    "Forces as gauge interactions",
    "Particles as representations of symmetry",
    "Mass as rest energy",
    "Mass as coupling to the Higgs field",
    "Why matter takes up space",
    "Why light comes in chunks",
    "Why atoms have shells",
    "Why solids are solid",
    "Why stars shine",
    "Why nuclei hold together",
    "Why the universe expands",
    "Why time depends on motion",
    "Why gravity affects clocks",
    "Why quantum amplitudes can cancel",
    "Why probabilities are squared amplitudes",
    "Why fields are more fundamental than particles",
    "Why conservation laws come from symmetry",
    "Why gauge fields are needed",
    "Why the Standard Model has charges",
    "Why there are antiparticles",
    "Why there are three particle generations",
    "Why neutrinos oscillate",
    "Why the weak interaction changes particle identity",
    "Why the strong interaction confines quarks",
    "Why photons are massless",
    "Why W and Z bosons are massive",
    "Why gluons carry color charge",
    "Why the Higgs field has a nonzero vacuum value",
    "Why quantum mechanics uses complex numbers",
    "Why spin is not ordinary spinning",
    "Why measurement changes a quantum state",
    "Why decoherence makes the world look classical",
    "Why black holes have horizons",
    "Why black holes have entropy",
    "Why dark matter is inferred",
    "Why dark energy is inferred",
    "Open questions in fundamental physics",
    "Limits of the Standard Model",
    "Limits of general relativity",
    "The search for quantum gravity",
    "The measurement problem",
    "The hierarchy problem",
    "The flavor puzzle",
    "The matter-antimatter puzzle",
    "The dark matter problem",
    "The dark energy problem",
    "The unification problem",
]

# =============================================================================
# 2. Project philosophy, rubrics, and prompt blocks
# =============================================================================

PROJECT_BRIEF = """
You are helping build EasyPhysics: a comprehensive, concept-first wiki and lesson
sequence that makes fundamental physics accessible to motivated high-schoolers,
college freshmen, and curious adults.

Core philosophy:
- Teach the clean modern conceptual structure first, not the historical path of discovery.
- Use standard physics accurately, but introduce jargon gently.
- Prefer descriptive, intuitive names first, with standard terms in braces.
  Example: space-occupier {fermion}; definite-answer state {eigenstate}.
- Braces are editorial markers. They help the human editor later search for and standardize nomenclature.
- Do not pretend physics is magic, spooky, or unknowable. When a topic is counterintuitive,
  explain the lawful structure that makes it understandable.
- Use analogies, diagrams, simple examples, and minimal math when helpful.
- If using math, explain what the math is doing in plain language.
- Avoid misleading simplifications. An analogy is useful only if its limits are clear.
- Focus on stable, accepted explanations. Do not center speculative research unless the article is explicitly about open questions.

Important style preference:
- The article should eventually work as MD/MDX, but do not obsess over exact MDX component formatting.
- The heart of the task is: clarity, rigor, structure, and usefulness.
""".strip()


NOMENCLATURE_GUIDE = """
Nomenclature policy:
- You may propose creative descriptive names for standard concepts.
- Put the standard historical/technical term in braces immediately after the descriptive name.
  Examples:
  - space-occupier {fermion}
  - stackable ripple {boson}
  - possibility-weight {amplitude}
  - phase-arrow {complex phase}
  - definite-answer state {eigenstate}
- Use the same standard term consistently inside braces once chosen in a draft.
- Do not use braces for ordinary emphasis. Braces are only for standard physics terms.
- If a descriptive name might mislead, flag it in the term candidate notes.
""".strip()


ACCESSIBILITY_RUBRIC = """
Accessibility score, 1-10:

10 = Exceptional. A motivated high-schooler can follow the article's main arc without prior exposure.
     Jargon is introduced only after intuition. Examples are vivid. Math is explained as meaning,
     not just symbols. The article feels empowering and clear.

9 = Publishable with light human editing. The main idea is easy to follow; jargon is mostly controlled;
    analogies are helpful; sections flow logically; any math has a plain-language interpretation.

8 = Strong draft. Mostly clear, but has a few dense sections, unexplained terms, abrupt transitions,
    or analogies that need more setup.

7 = Useful but uneven. A motivated reader could learn from it, but several passages need simplification,
    clearer examples, or better sequencing.

6 = Borderline. The article contains useful explanations, but assumes too much background or uses too much jargon.

5 = Mixed. Some good paragraphs, but the structure or language would lose many target readers.

4 = Hard to follow. Mostly written for someone who already knows the subject.

3 = Very inaccessible. Dense, abstract, jargon-heavy, or poorly sequenced.

2 = Barely useful to the target audience.

1 = Fails the accessibility goal.

Accessibility judge priorities:
- Does the opening give the reader an intuitive foothold?
- Are standard terms introduced after meaning, not before?
- Are descriptive names useful rather than cutesy or misleading?
- Are analogies concrete and then carefully limited?
- Is any math explained in words?
- Does the article avoid "spooky/magic/weird" framing while still acknowledging counterintuitive ideas?
- Does each section make the next section easier?
""".strip()


RIGOR_RUBRIC = """
Rigor score, 1-10:

10 = Exceptional. Scientifically accurate, well-qualified, and careful about analogy limits.
     No obvious misleading simplifications. Claims align with stable accepted physics.

9 = Publishable with light human editing. No major errors. A few details may need polishing,
    but the article is safe as an educational explanation.

8 = Strong draft. Mostly accurate but has minor imprecision, missing qualifications, or analogy risks.

7 = Useful but needs scientific review. Contains no catastrophic errors, but some claims are too loose,
    incomplete, or potentially misleading.

6 = Borderline. Several important corrections or qualifications are needed.

5 = Mixed. The article has valuable explanations but also significant inaccuracies or misleading framings.

4 = Scientifically weak. Multiple substantial errors or serious conceptual muddling.

3 = Very unreliable. The reader would likely learn incorrect physics.

2 = Mostly wrong or confused.

1 = Fails the rigor goal.

Rigor judge priorities:
- Are definitions compatible with standard physics?
- Are analogies technically safe, with their limits stated when necessary?
- Are quantum concepts distinguished correctly: amplitude vs probability, superposition vs ignorance,
  measurement vs ordinary looking, phase vs probability?
- Are field/particle/wave descriptions accurate enough for a beginner article?
- Are conservation, symmetry, force, energy, mass, and spin statements properly qualified?
- Does the article avoid replacing historical jargon with new misleading jargon?
- Are open questions distinguished from settled explanations?
""".strip()


SOURCE_POLICY = """
Source policy:
- Prefer stable, accepted educational or reference sources.
- Good source types: university lecture notes, textbooks, national labs, CERN/Fermilab/NASA/DOE pages,
  Stanford Encyclopedia-style references, reputable physics education sites, review articles.
- Avoid treating SEO summaries, unsourced blogs, forum answers, and speculative papers as authoritative.
- Do not search for "latest explanations" unless the article is about a current/open research issue.
- For beginner articles, source the standard explanation, not novelty.
""".strip()


ARTICLE_TEMPLATE_GUIDE = """
Preferred article structure:

# Title

## The core idea
A short, intuitive explanation that gives the reader the main point first.

## Why this matters
Explain what the concept helps us understand.

## The simple picture
Use an analogy, diagram idea, or concrete example.

## The more precise picture
Introduce standard terms, careful distinctions, and optional minimal math.

## Common misconceptions
Name and correct the traps.

## How this connects to the rest of physics
Link the concept to fields, particles, symmetry, conservation, relativity, or the Standard Model as appropriate.

## Recap
A few concise takeaways.
""".strip()


JSON_DISCIPLINE = """
Output valid JSON only.
Do not wrap the JSON in Markdown fences.
Do not include comments.
Do not include explanatory prose before or after the JSON.
""".strip()


# =============================================================================
# 3. Helpers
# =============================================================================


def slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-") or "untitled"


def now_stamp() -> str:
    return datetime.now().strftime("%Y-%m-%d_%H-%M-%S")


def today_iso() -> str:
    return datetime.now().strftime("%Y-%m-%d")


def limit_chars(text: Any, max_chars: int = MAX_CONTEXT_CHARS) -> str:
    s = str(text)
    if len(s) <= max_chars:
        return s
    half = max_chars // 2
    return s[:half] + "\n\n...[TRUNCATED]...\n\n" + s[-half:]


def strip_qwen_thinking(text: str) -> str:
    """Remove accidental Qwen <think> blocks if the model emits them."""
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL | re.IGNORECASE)
    return text.strip()


def read_text(path: Path, default: str = "") -> str:
    if not path.exists():
        return default
    return path.read_text(encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def read_yaml(path: Path, default: Dict[str, Any]) -> Dict[str, Any]:
    if not path.exists():
        return default
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            return data
        return default
    except Exception:
        return default


def write_yaml(path: Path, data: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(data, sort_keys=False, allow_unicode=True), encoding="utf-8")


def parse_json_loose(text: str, fallback: Any) -> Any:
    """Try hard to recover JSON from an LLM response."""
    clean = strip_qwen_thinking(text).strip()

    # Remove common markdown fences.
    clean = re.sub(r"^```(?:json)?\s*", "", clean, flags=re.IGNORECASE)
    clean = re.sub(r"\s*```$", "", clean)

    try:
        return json.loads(clean)
    except Exception:
        pass

    # Try to find the first JSON object or array.
    candidates = []
    obj_match = re.search(r"\{.*\}", clean, flags=re.DOTALL)
    arr_match = re.search(r"\[.*\]", clean, flags=re.DOTALL)
    if obj_match:
        candidates.append(obj_match.group(0))
    if arr_match:
        candidates.append(arr_match.group(0))

    for candidate in candidates:
        try:
            return json.loads(candidate)
        except Exception:
            continue

    return fallback


def approx_tokens(text: str) -> int:
    # Cheap approximation good enough for trend logging. English prose is often
    # around 3.5-4 chars/token; code/JSON can vary.
    return max(1, int(len(text) / 4))


def append_log(article_dir: Path, node_name: str, prompt: str, response: str) -> None:
    log_dir = article_dir / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / f"{today_iso()}.log"

    with log_path.open("a", encoding="utf-8") as f:
        f.write("\n" + "=" * 80 + "\n")
        f.write(f"TIME: {datetime.now().isoformat(timespec='seconds')}\n")
        f.write(f"NODE: {node_name}\n")
        f.write(f"PROMPT_CHARS: {len(prompt)}\n")
        f.write(f"PROMPT_TOKENS_APPROX: {approx_tokens(prompt)}\n")
        f.write(f"RESPONSE_CHARS: {len(response)}\n")
        f.write(f"LLM_MODEL: {MODEL_NAME}\n")
        f.write(f"LLM_OPTIONS: {json.dumps(LLM_OPTIONS, sort_keys=True)}\n")
        f.write("=" * 80 + "\n")
        f.write("PROMPT:\n")
        f.write(prompt)
        f.write("\n\nRESPONSE:\n")
        f.write(response)
        f.write("\n")


def append_event_log(article_dir: Path, node_name: str, event: Dict[str, Any]) -> None:
    log_dir = article_dir / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / f"events_{today_iso()}.jsonl"
    event = dict(event)
    event.setdefault("time", datetime.now().isoformat(timespec="seconds"))
    event.setdefault("node", node_name)
    with log_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")


def archive_file(path: Path, archive_dir: Path, label: str) -> None:
    if not path.exists():
        return
    archive_dir.mkdir(parents=True, exist_ok=True)
    archived = archive_dir / f"{label}_{now_stamp()}{path.suffix}"
    archived.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")

def run_role(
    p: ArticlePaths,
    state: Dict[str, Any],
    name: str,
    func,
    required: bool = False,
    default: Any = None,
) -> Any:
    try:
        return func(p, state)
    except Exception as exc:
        append_event_log(
            p.article_dir,
            name,
            {
                "event": "role_failed",
                "required": required,
                "error": repr(exc),
                "traceback": traceback.format_exc(),
            },
        )
        print(f"  -> [{name}] failed: {repr(exc)}")

        if required:
            raise

        return default

def normalize_review_payload(payload: Any, review_type: str) -> Dict[str, Any]:
    if isinstance(payload, list):
        payload = payload[0] if payload and isinstance(payload[0], dict) else {}

    if not isinstance(payload, dict):
        payload = {}

    nested = payload.get("review")
    if isinstance(nested, dict):
        payload = {**nested, **payload}

    score = (
        payload.get("score")
        or payload.get(f"{review_type}_score")
        or payload.get("rating")
        or 0
    )

    try:
        score = int(score)
    except Exception:
        score = 0

    return {
        "score": max(0, min(10, score)),
        "pass": bool(payload.get("pass", score >= PASSING_SCORE)),
        "strengths": payload.get("strengths", []),
        "issues": payload.get("issues", []),
        "best_next_revision": payload.get("best_next_revision", ""),
    }

# =============================================================================
# 4. Article state and paths
# =============================================================================


@dataclass(frozen=True)
class ArticlePaths:
    article_dir: Path
    state: Path
    outline: Path
    draft: Path
    claims: Path
    sources: Path
    claim_checks: Path
    term_candidates: Path
    final_mdx: Path
    notes: Path
    reviews_dir: Path
    history_dir: Path


def paths_for_topic(topic: str) -> ArticlePaths:
    slug = slugify(topic)
    article_dir = ARTICLE_ROOT / slug
    return ArticlePaths(
        article_dir=article_dir,
        state=article_dir / "article.yml",
        outline=article_dir / "outline.md",
        draft=article_dir / "draft.md",
        claims=article_dir / "claims.json",
        sources=article_dir / "sources.json",
        claim_checks=article_dir / "claim_checks.json",
        term_candidates=article_dir / "term_candidates.json",
        final_mdx=article_dir / "final.mdx",
        notes=article_dir / "notes.md",
        reviews_dir=article_dir / "reviews",
        history_dir=article_dir / "history",
    )


def default_state(topic: str) -> Dict[str, Any]:
    return {
        "title": topic,
        "slug": slugify(topic),
        "status": "new",
        "finished": False,
        "iteration_count": 0,
        "accessibility_score": None,
        "rigor_score": None,
        "last_worked_on": None,
        "last_completed_pass": None,
        "needs": ["outline", "draft", "claim_check", "review"],
        "current_draft": "draft.md",
    }


def load_article_state(topic: str) -> Tuple[ArticlePaths, Dict[str, Any]]:
    p = paths_for_topic(topic)
    p.article_dir.mkdir(parents=True, exist_ok=True)
    p.reviews_dir.mkdir(parents=True, exist_ok=True)
    p.history_dir.mkdir(parents=True, exist_ok=True)

    state = read_yaml(p.state, default_state(topic))
    # Keep title/slug stable if state exists, but fill missing fields.
    merged = default_state(topic)
    merged.update(state)
    write_yaml(p.state, merged)
    if not p.notes.exists():
        write_text(
            p.notes,
            "# Human/editor notes\n\nAdd any preferences, corrections, or article-specific constraints here.\n",
        )
    return p, merged


def mark_scores_and_status(
    p: ArticlePaths,
    state: Dict[str, Any],
    accessibility_review: Dict[str, Any],
    rigor_review: Dict[str, Any],
) -> Dict[str, Any]:
    accessibility_score = int(accessibility_review.get("score", 0) or 0)
    rigor_score = int(rigor_review.get("score", 0) or 0)

    state["accessibility_score"] = accessibility_score
    state["rigor_score"] = rigor_score
    state["last_worked_on"] = today_iso()
    state["last_completed_pass"] = now_stamp()

    needs: List[str] = []
    if accessibility_score < PASSING_SCORE:
        needs.append("accessibility_revision")
    if rigor_score < PASSING_SCORE:
        needs.append("rigor_revision")

    claim_checks = read_json(p.claim_checks, {})
    unresolved = claim_checks.get("summary", {}).get("unresolved_or_needs_qualification", None)
    if unresolved:
        needs.append("claim_review")

    state["needs"] = needs
    state["finished"] = accessibility_score >= PASSING_SCORE and rigor_score >= PASSING_SCORE
    state["status"] = "finished" if state["finished"] else "needs_revision"

    write_yaml(p.state, state)
    return state


# =============================================================================
# 5. LLM and search wrappers
# =============================================================================


class LLMCallError(RuntimeError):
    pass


def _llm_worker(
    result_queue: "mp.Queue",
    model_name: str,
    llm_options: Dict[str, Any],
    system: str,
    prompt: str,
) -> None:
    """Runs in a child process so a stuck backend call can be terminated."""
    try:
        local_llm = ChatOllama(model=model_name, **llm_options)
        messages = [SystemMessage(content=system), HumanMessage(content=prompt)]
        response = local_llm.invoke(messages).content
        result_queue.put({"ok": True, "response": response})
    except Exception as exc:
        result_queue.put(
            {
                "ok": False,
                "error": repr(exc),
                "traceback": traceback.format_exc(),
            }
        )

def effective_llm_options(node_name: str) -> Dict[str, Any]:
    options = dict(LLM_OPTIONS)
    options.update(NODE_OPTION_OVERRIDES.get(node_name, {}))
    return options


def stop_ollama_model(article_dir: Path, reason: str) -> None:
    """Try to unload a stuck Ollama model/runner after timeout."""
    if not RESET_OLLAMA_MODEL_ON_TIMEOUT:
        return

    try:
        completed = subprocess.run(
            ["ollama", "stop", MODEL_NAME],
            capture_output=True,
            text=True,
            timeout=45,
        )
        append_event_log(
            article_dir,
            "ollama_reset",
            {
                "event": "ollama_stop_model",
                "reason": reason,
                "returncode": completed.returncode,
                "stdout": completed.stdout[-1000:],
                "stderr": completed.stderr[-1000:],
            },
        )
    except Exception as exc:
        append_event_log(
            article_dir,
            "ollama_reset",
            {
                "event": "ollama_stop_model_failed",
                "reason": reason,
                "error": repr(exc),
            },
        )


def invoke_llm_once_with_timeout(
    system: str,
    prompt: str,
    timeout_seconds: int,
    llm_options: Dict[str, Any],
) -> str:
    ctx = mp.get_context("spawn")
    result_queue: "mp.Queue" = ctx.Queue(maxsize=1)
    proc = ctx.Process(
        target=_llm_worker,
        args=(result_queue, MODEL_NAME, llm_options, system, prompt),
        daemon=True,
    )
    proc.start()
    proc.join(timeout_seconds)

    if proc.is_alive():
        proc.terminate()
        proc.join(10)
        if proc.is_alive():
            proc.kill()
            proc.join(10)
        raise LLMCallError(f"LLM_TIMEOUT_AFTER_{timeout_seconds}_SECONDS")

    try:
        payload = result_queue.get_nowait()
    except queue.Empty as exc:
        raise LLMCallError(f"LLM_PROCESS_EXITED_WITHOUT_RESPONSE_exitcode={proc.exitcode}") from exc

    if not payload.get("ok"):
        raise LLMCallError(payload.get("error", "UNKNOWN_LLM_ERROR"))

    return strip_qwen_thinking(payload.get("response", ""))


def invoke_llm(
    article_dir: Path,
    node_name: str,
    prompt: str,
    system_extra: str = "",
    expect_json: bool = False,
) -> str:
    system = PROJECT_BRIEF + "\n\n" + NOMENCLATURE_GUIDE
    if system_extra:
        system += "\n\n" + system_extra.strip()
    if expect_json:
        system += "\n\n" + JSON_DISCIPLINE

    full_prompt_chars = len(system) + len(prompt)
    full_prompt_tokens = approx_tokens(system + prompt)

    options = effective_llm_options(node_name)

    print(
        f"  -> [{node_name}] calling {MODEL_NAME} "
        f"(~{full_prompt_tokens} tok, {full_prompt_chars} chars, "
        f"ctx={options.get('num_ctx')}, batch={options.get('num_batch')}, "
        f"predict={options.get('num_predict')})..."
    )

    append_event_log(
        article_dir,
        node_name,
        {
            "event": "llm_start",
            "prompt_chars": full_prompt_chars,
            "prompt_tokens_approx": full_prompt_tokens,
            "llm_options": options,
            "timeout_seconds": LLM_TIMEOUT_SECONDS,
        },
    )

    last_error: Optional[str] = None
    for attempt in range(LLM_MAX_RETRIES + 1):
        started = time.monotonic()
        try:
            response = invoke_llm_once_with_timeout(system, prompt, LLM_TIMEOUT_SECONDS, options)
            elapsed = round(time.monotonic() - started, 2)
            append_event_log(
                article_dir,
                node_name,
                {
                    "event": "llm_success",
                    "attempt": attempt + 1,
                    "elapsed_seconds": elapsed,
                    "response_chars": len(response),
                },
            )
            append_log(article_dir, node_name, prompt, response)
            return response
        except Exception as exc:
            elapsed = round(time.monotonic() - started, 2)
            last_error = repr(exc)
            append_event_log(
                article_dir,
                node_name,
                {
                    "event": "llm_failure",
                    "attempt": attempt + 1,
                    "elapsed_seconds": elapsed,
                    "error": last_error,
                },
            )
            if "LLM_TIMEOUT" in last_error:
                stop_ollama_model(article_dir, reason=f"timeout in {node_name}")
            print(f"  -> [{node_name}] LLM call failed on attempt {attempt + 1}: {last_error}")
            if attempt < LLM_MAX_RETRIES:
                time.sleep(5)

    raise LLMCallError(f"{node_name} failed after {LLM_MAX_RETRIES + 1} attempt(s): {last_error}")


def safe_search(query: str) -> str:
    try:
        result = search_tool.invoke(query)
        return limit_chars(result, MAX_SEARCH_RESULT_CHARS_PER_CLAIM)
    except Exception as exc:
        return f"SEARCH_FAILED: {exc}"


# =============================================================================
# 6. Workflow roles
# =============================================================================


def planner_role(p: ArticlePaths, state: Dict[str, Any]) -> None:
    if p.outline.exists() and read_text(p.outline).strip():
        print("  -> [planner] outline already exists; reusing it.")
        return

    prompt = f"""
Create a strong teaching outline for this EasyPhysics article:

Title: {state['title']}

The outline should include:
1. Scope: what this article explains.
2. Out of scope: what it should not try to explain yet.
3. Prerequisite concepts.
4. Core intuition.
5. Suggested descriptive names with standard terms in braces.
6. Common misconceptions to avoid.
7. Section-by-section outline.
8. Optional diagram ideas.
9. Optional minimal math, with what the math means.

Use Markdown.
""".strip()

    outline = invoke_llm(p.article_dir, "planner", prompt)
    write_text(p.outline, outline)


def writer_role(p: ArticlePaths, state: Dict[str, Any]) -> None:
    outline = read_text(p.outline)
    notes = read_text(p.notes)

    previous_draft = read_text(p.draft)
    previous_reviews = gather_recent_reviews(p, max_reviews=4)
    previous_claim_checks = read_json(p.claim_checks, {})

    if previous_draft.strip():
        archive_file(p.draft, p.history_dir, "draft_before_revision")
        prompt = f"""
Revise the current article draft once. Do not create multiple alternatives.

Title: {state['title']}

Article outline:
{limit_chars(outline, 9000)}

Human/editor notes:
{limit_chars(notes, 3000)}

Recent review feedback:
{limit_chars(previous_reviews, 9000)}

Recent claim-check feedback:
{limit_chars(json.dumps(previous_claim_checks, indent=2, ensure_ascii=False), 10000)}

Current draft:
{limit_chars(previous_draft, 22000)}

Revision instructions:
- Preserve what is already good.
- Improve clarity and rigor.
- Use descriptive names with standard terms in braces, e.g. space-occupier {{fermion}}.
- Avoid overclaiming.
- If math is included, explain what it means.
- Output only the revised article in Markdown, with no commentary before or after.
""".strip()
    else:
        prompt = f"""
Write a high-quality first draft for this EasyPhysics article.

Title: {state['title']}

Article outline:
{limit_chars(outline, 12000)}

Human/editor notes:
{limit_chars(notes, 3000)}

Template guidance:
{ARTICLE_TEMPLATE_GUIDE}

Drafting instructions:
- Make it accessible to a motivated high-schooler or college freshman.
- Teach the modern concept directly rather than narrating historical discovery.
- Use descriptive names with standard terms in braces, e.g. space-occupier {{fermion}}.
- Include common misconceptions and correct them.
- Include minimal math only when it helps, and explain what the math means.
- Suggest diagram ideas inline where helpful using this format: [Diagram idea: ...]
- Output only the article in Markdown, with no commentary before or after.
""".strip()

    new_draft = invoke_llm(p.article_dir, "writer", prompt)

    if not new_draft.strip():
        append_event_log(
            p.article_dir,
            "writer",
            {
                "event": "empty_writer_response",
                "message": "Writer returned an empty draft; preserving existing draft.md.",
            },
        )
        raise RuntimeError("Writer returned an empty draft.")

    write_text(p.draft, new_draft)


def term_collector_role(p: ArticlePaths, state: Dict[str, Any]) -> None:
    draft = read_text(p.draft)
    existing = read_json(p.term_candidates, {"terms": []})

    prompt = f"""
Extract the descriptive-name candidates from this draft.

Return JSON with this shape:
{{
  "terms": [
    {{
      "standard_term": "fermion",
      "candidate_name": "space-occupier",
      "context_quote": "short quote from the draft",
      "usefulness": "why this name helps",
      "risk": "how it could mislead, or empty string if low risk"
    }}
  ]
}}

Only include actual teaching-name candidates, especially phrases followed by standard terms in braces.

Draft:
{limit_chars(draft, 30000)}
""".strip()

    raw = invoke_llm(p.article_dir, "term_collector", prompt, expect_json=True)
    data = parse_json_loose(raw, {"terms": []})

    # Merge without trying to be too clever.
    merged_terms = existing.get("terms", []) + data.get("terms", [])
    existing["terms"] = merged_terms
    existing["last_updated"] = now_stamp()
    write_json(p.term_candidates, existing)

    update_global_term_bank(state["title"], data.get("terms", []))

def normalize_claims_payload(payload: Any) -> List[Dict[str, Any]]:
    """Accept several plausible LLM JSON shapes and return a clean claim list."""
    if isinstance(payload, list):
        claims = payload
    elif isinstance(payload, dict):
        claims = (
            payload.get("claims")
            or payload.get("scientific_claims")
            or payload.get("items")
            or payload.get("results")
            or []
        )
    else:
        claims = []

    if not isinstance(claims, list):
        return []

    normalized = []
    for item in claims:
        if isinstance(item, str):
            item = {"claim": item}
        if not isinstance(item, dict):
            continue

        claim_text = (
            item.get("claim")
            or item.get("text")
            or item.get("statement")
            or item.get("sentence")
            or ""
        ).strip()

        if not claim_text:
            continue

        normalized.append(
            {
                "id": item.get("id", ""),
                "claim": claim_text,
                "type": item.get("type", "other"),
                "importance": item.get("importance", "medium"),
                "needs_external_check": item.get("needs_external_check", True),
                "why_it_matters": item.get("why_it_matters", ""),
                "suggested_search_query": item.get("suggested_search_query", ""),
            }
        )

    return normalized


def fallback_claims_from_draft(topic: str, draft: str, max_claims: int = 8) -> List[Dict[str, Any]]:
    """Crude deterministic fallback so claims.json is not empty after parser failure."""
    cleaned = re.sub(r"\s+", " ", draft)
    sentences = re.split(r"(?<=[.!?])\s+", cleaned)

    useful = []
    skip_starts = (
        "in this article",
        "recap",
        "diagram idea",
        "for example",
    )

    for sentence in sentences:
        s = sentence.strip()
        if len(s) < 50 or len(s) > 300:
            continue
        if s.lower().startswith(skip_starts):
            continue
        if any(
            word in s.lower()
            for word in [
                "is ",
                "are ",
                "means",
                "explains",
                "depends",
                "conserved",
                "symmetry",
                "field",
                "energy",
                "state",
                "particle",
                "wave",
                "force",
                "equation",
            ]
        ):
            useful.append(s)

        if len(useful) >= max_claims:
            break

    claims = []
    for i, sentence in enumerate(useful, start=1):
        claims.append(
            {
                "id": f"C{i:03d}",
                "claim": sentence,
                "type": "fallback-extracted",
                "importance": "medium",
                "needs_external_check": True,
                "why_it_matters": "Automatically extracted fallback claim; review manually.",
                "suggested_search_query": build_fallback_search_query(topic, sentence),
            }
        )

    return claims


def claim_extractor_role(p: ArticlePaths, state: Dict[str, Any]) -> None:
    draft = read_text(p.draft)

    prompt = f"""
Extract 8 to 12 important scientific and explanatory claims from this article draft.

Return JSON with exactly this shape:
{{
  "claims": [
    {{
      "id": "C001",
      "claim": "A clear, standalone claim from the article.",
      "type": "definition",
      "importance": "high",
      "needs_external_check": true,
      "why_it_matters": "brief reason",
      "suggested_search_query": "stable source search query, not latest-news oriented"
    }}
  ]
}}

Rules:
- Do not return an empty claims list unless the draft is empty.
- Use only valid JSON.
- Use true/false, not True/False.
- Do not include Markdown fences.
- Do not include prose before or after the JSON.
- Extract claims that matter for scientific correctness.
- Include claims embedded in analogies if the analogy could mislead.
- Do not include purely stylistic statements.
- Search queries should prefer stable sources: textbooks, lecture notes, CERN, Fermilab, university pages.

Article title: {state['title']}

Draft:
{limit_chars(draft, 26000)}
""".strip()

    raw = invoke_llm(
        p.article_dir,
        "claim_extractor",
        prompt,
        system_extra=SOURCE_POLICY,
        expect_json=True,
    )

    # Always save the raw output so you can inspect what Qwen actually returned.
    raw_path = p.article_dir / "claim_extractor_raw.txt"
    write_text(raw_path, raw)

    parsed = parse_json_loose(raw, None)
    claims = normalize_claims_payload(parsed)

    parse_note = ""

    if not claims:
        parse_note = (
            "No usable claims parsed from LLM output. "
            "Using deterministic fallback extraction from draft sentences."
        )
        append_event_log(
            p.article_dir,
            "claim_extractor",
            {
                "event": "claim_parse_failed_or_empty",
                "raw_response_chars": len(raw),
                "raw_response_preview": raw[:1000],
            },
        )
        claims = fallback_claims_from_draft(state["title"], draft)

    for i, claim in enumerate(claims, start=1):
        claim["id"] = claim.get("id") or f"C{i:03d}"

        if claim.get("importance") not in {"high", "medium", "low"}:
            claim["importance"] = "medium"

        if not isinstance(claim.get("needs_external_check"), bool):
            claim["needs_external_check"] = True

        if not claim.get("suggested_search_query"):
            claim["suggested_search_query"] = build_fallback_search_query(
                state["title"],
                claim.get("claim", ""),
            )

    write_json(
        p.claims,
        {
            "claims": claims,
            "last_updated": now_stamp(),
            "count": len(claims),
            "parse_note": parse_note,
        },
    )

    print(f"  -> [claim_extractor] wrote {len(claims)} claim(s).")


def build_fallback_search_query(topic: str, claim: str) -> str:
    claim_words = " ".join(str(claim).split()[:16])
    return f"{topic} {claim_words} physics lecture notes textbook explanation"


def source_finder_role(p: ArticlePaths, state: Dict[str, Any]) -> None:
    claims_data = read_json(p.claims, {"claims": []})
    claims = claims_data.get("claims", [])
    existing_sources = read_json(p.sources, {"sources_by_claim": {}})
    sources_by_claim = existing_sources.setdefault("sources_by_claim", {})

    print(f"  -> [source_finder] loaded {len(claims)} claim(s).")

    candidates = [
        c for c in claims
        if c.get("needs_external_check", True)
        and c.get("importance", "medium") in {"high", "medium"}
    ]
    candidates = candidates[:MAX_CLAIMS_TO_SEARCH_PER_PASS]

    if not candidates:
        print("  -> [source_finder] no claims selected for search.")
        write_json(p.sources, existing_sources)
        return

    print(f"  -> [source_finder] searching for {len(candidates)} claim(s)...")
  
    for claim in candidates:
        claim_id = claim.get("id")
        if not claim_id:
            continue

        # Re-search each pass for now; this keeps it simple and can catch better snippets.
        query = claim.get("suggested_search_query") or build_fallback_search_query(
            state["title"], claim.get("claim", "")
        )
        query = clean_search_query(query)
        result = safe_search(query)

        sources_by_claim[claim_id] = {
            "claim": claim.get("claim", ""),
            "query": query,
            "result_snippet": result,
            "searched_at": now_stamp(),
            "source_policy": "Prefer stable accepted physics sources; avoid novelty unless topic requires it.",
        }
        time.sleep(0.5)  # Be polite to the search backend.
    print(f"  -> [source_finder] selected {len(candidates)} claim(s) for search.")

    existing_sources["last_updated"] = now_stamp()
    write_json(p.sources, existing_sources)


def clean_search_query(query: str) -> str:
    query = re.sub(r"\s+", " ", query).strip()
    query = query.replace("latest", "")
    if len(query) > 240:
        query = query[:240]
    return query


def claim_checker_role(p: ArticlePaths, state: Dict[str, Any]) -> None:
    claims_data = read_json(p.claims, {"claims": []})
    sources_data = read_json(p.sources, {"sources_by_claim": {}})
    draft = read_text(p.draft)

    claims = claims_data.get("claims", [])
    sources_by_claim = sources_data.get("sources_by_claim", {})

    selected_claims = [
        c for c in claims
        if c.get("importance", "medium") in {"high", "medium"}
    ][:MAX_CLAIMS_TO_SEARCH_PER_PASS]

    claim_checks = []
    timeout_count = 0

    for claim in selected_claims:
        claim_id = claim.get("id", "")
        source_context = sources_by_claim.get(claim_id, {})

        prompt = f"""
Check this one article claim against the available search snippet.

Return JSON with this shape:
{{
  "id": "{claim_id}",
  "verdict": "supported | mostly_supported | needs_qualification | unsupported | contradicted | not_enough_evidence",
  "severity": "none | low | medium | high",
  "problem": "specific issue, or empty string",
  "suggested_fix": "specific correction to the article, or empty string",
  "source_quality_note": "brief note about whether the snippets look authoritative"
}}

Rules:
- Be conservative.
- If the snippet is weak or absent, say not_enough_evidence.
- Do not demand advanced nuance beyond the article's beginner scope.
- Do flag misleading simplifications.
- Focus on stable accepted physics.

Article title: {state['title']}

Claim:
{json.dumps(claim, indent=2, ensure_ascii=False)}

Search snippet:
{limit_chars(json.dumps(source_context, indent=2, ensure_ascii=False), 5000)}

Relevant draft context:
{limit_chars(draft, 7000)}
""".strip()

        try:
            raw = invoke_llm(
                p.article_dir,
                "claim_checker",
                prompt,
                system_extra=SOURCE_POLICY,
                expect_json=True,
            )
            data = parse_json_loose(
                raw,
                {
                    "id": claim_id,
                    "verdict": "not_enough_evidence",
                    "severity": "medium",
                    "problem": "Could not parse claim-checker output.",
                    "suggested_fix": "Review this claim manually.",
                    "source_quality_note": "",
                },
            )
            claim_checks.append(data)

        except Exception as exc:
            timeout_count += 1
            claim_checks.append(
                {
                    "id": claim_id,
                    "verdict": "not_enough_evidence",
                    "severity": "medium",
                    "problem": f"Claim checker failed: {repr(exc)}",
                    "suggested_fix": "Review this claim manually or rerun with smaller context.",
                    "source_quality_note": "",
                }
            )

            append_event_log(
                p.article_dir,
                "claim_checker",
                {
                    "event": "per_claim_check_failed",
                    "claim_id": claim_id,
                    "error": repr(exc),
                },
            )

            # If one claim-check call flatlines, do not spend 8 minutes each on the rest.
            if timeout_count >= 1:
                break

    unresolved = sum(
        1 for c in claim_checks
        if c.get("verdict") in {
            "needs_qualification",
            "unsupported",
            "contradicted",
            "not_enough_evidence",
        }
        or c.get("severity") in {"medium", "high"}
    )

    result = {
        "claim_checks": claim_checks,
        "summary": {
            "overall_claim_quality": (
                "Partial claim check completed."
                if timeout_count
                else "Claim check completed."
            ),
            "unresolved_or_needs_qualification": unresolved,
            "highest_priority_fixes": [
                c.get("suggested_fix", "")
                for c in claim_checks
                if c.get("suggested_fix")
            ][:5],
        },
        "last_updated": now_stamp(),
    }

    write_json(p.claim_checks, result)


def claim_revision_role(p: ArticlePaths, state: Dict[str, Any]) -> None:
    draft = read_text(p.draft)
    claim_checks = read_json(p.claim_checks, {})

    checks = claim_checks.get("claim_checks", [])
    serious_issues = [
        c for c in checks
        if c.get("severity") in {"medium", "high"}
        or c.get("verdict") in {"needs_qualification", "unsupported", "contradicted"}
    ]

    if not serious_issues:
        print("  -> [claim_revision] no serious claim-check issues found; keeping draft.")
        return

    archive_file(p.draft, p.history_dir, "draft_before_claim_revision")

    prompt = f"""
Revise the article once to address claim-check feedback.

Do not rewrite for its own sake. Fix the scientific issues while preserving accessible language.

Claim-check feedback:
{limit_chars(json.dumps(claim_checks, indent=2, ensure_ascii=False), 14000)}

Current draft:
{limit_chars(draft, 30000)}

Instructions:
- Correct or qualify unsupported, contradicted, or overstrong claims.
- Preserve good accessible explanations.
- Do not add speculative research as settled fact.
- If an analogy was misleading, either repair it or state its limits.
- Keep standard terms in braces after descriptive names.
- Output only the revised article in Markdown.
""".strip()

    revised = invoke_llm(p.article_dir, "claim_revision", prompt)
    write_text(p.draft, revised)


def accessibility_judge_role(p: ArticlePaths, state: Dict[str, Any]) -> Dict[str, Any]:
    draft = read_text(p.draft)
    round_num = state.get("iteration_count", 0)

    prompt = f"""
Score this EasyPhysics article for accessibility using the rubric below.

{ACCESSIBILITY_RUBRIC}

Return JSON with this shape:
{{
  "score": 1,
  "pass": false,
  "strengths": ["specific strength"],
  "issues": [
    {{
      "severity": "low | medium | high",
      "location": "section or paragraph description",
      "problem": "specific accessibility issue",
      "suggested_fix": "specific fix"
    }}
  ],
  "best_next_revision": "one concise paragraph describing what to improve next"
}}

Article title: {state['title']}

Draft:
{limit_chars(draft, 34000)}
""".strip()

    raw = invoke_llm(p.article_dir, "accessibility_judge", prompt, system_extra=ACCESSIBILITY_RUBRIC, expect_json=True)
    parsed = parse_json_loose(raw, {})
    data = normalize_review_payload(parsed, "accessibility")
    data["review_type"] = "accessibility"
    data["round"] = round_num
    data["created_at"] = now_stamp()

    path = p.reviews_dir / f"accessibility_round_{round_num:03d}.json"
    write_json(path, data)
    write_text(p.article_dir / f"accessibility_judge_raw_round_{round_num:03d}.txt", raw)
    return data


def rigor_judge_role(p: ArticlePaths, state: Dict[str, Any]) -> Dict[str, Any]:
    draft = read_text(p.draft)
    claim_checks = read_json(p.claim_checks, {})
    round_num = state.get("iteration_count", 0)

    prompt = f"""
Score this EasyPhysics article for scientific rigor using the rubric below.

{RIGOR_RUBRIC}

Use the claim-check results as context, but judge the final draft itself.

Return JSON with this shape:
{{
  "score": 1,
  "pass": false,
  "strengths": ["specific strength"],
  "issues": [
    {{
      "severity": "low | medium | high",
      "location": "section or paragraph description",
      "problem": "specific rigor issue",
      "suggested_fix": "specific fix"
    }}
  ],
  "best_next_revision": "one concise paragraph describing what to improve next"
}}

Article title: {state['title']}

Claim-check context:
{limit_chars(json.dumps(claim_checks, indent=2, ensure_ascii=False), 12000)}

Draft:
{limit_chars(draft, 34000)}
""".strip()

    raw = invoke_llm(p.article_dir, "rigor_judge", prompt, system_extra=RIGOR_RUBRIC, expect_json=True)
    parsed = parse_json_loose(raw, {})
    data = normalize_review_payload(parsed, "rigor")
    data["review_type"] = "rigor"
    data["round"] = round_num
    data["created_at"] = now_stamp()

    path = p.reviews_dir / f"rigor_round_{round_num:03d}.json"
    write_json(path, data)
    write_text(p.article_dir / f"rigor_judge_raw_round_{round_num:03d}.txt", raw)
    return data


def final_mdx_role(p: ArticlePaths, state: Dict[str, Any]) -> None:
    """Write a lightweight final.mdx wrapper. The human editor can still polish it."""
    draft = read_text(p.draft)
    title = state["title"].replace('"', "'")
    frontmatter = f"---\ntitle: \"{title}\"\nslug: \"{state['slug']}\"\n---\n\n"
    write_text(p.final_mdx, frontmatter + draft)


# =============================================================================
# 7. Global term bank and review gathering
# =============================================================================


def update_global_term_bank(article_title: str, terms: List[Dict[str, Any]]) -> None:
    if not terms:
        return

    bank_path = GLOBAL_ARTIFACT_DIR / "term_bank_candidates.json"
    bank = read_json(bank_path, {"terms": []})
    for term in terms:
        term = dict(term)
        term["article_title"] = article_title
        term["captured_at"] = now_stamp()
        bank["terms"].append(term)
    bank["last_updated"] = now_stamp()
    write_json(bank_path, bank)


def gather_recent_reviews(p: ArticlePaths, max_reviews: int = 4) -> str:
    if not p.reviews_dir.exists():
        return ""
    review_files = sorted(p.reviews_dir.glob("*.json"), key=lambda x: x.stat().st_mtime, reverse=True)
    chunks = []
    for path in review_files[:max_reviews]:
        chunks.append(f"# {path.name}\n{path.read_text(encoding='utf-8')}")
    return "\n\n".join(chunks)


# =============================================================================
# 8. One-cycle article workflow
# =============================================================================


def article_is_passing(state: Dict[str, Any]) -> bool:
    a = state.get("accessibility_score")
    r = state.get("rigor_score")
    return bool(a is not None and r is not None and int(a) >= PASSING_SCORE and int(r) >= PASSING_SCORE)


def run_one_article_cycle(topic: str, force_finished: bool = False) -> Dict[str, Any]:
    p, state = load_article_state(topic)

    if article_is_passing(state) and not force_finished:
        print(
            f"\n--- Skipping already-passing article: {topic} "
            f"(A={state.get('accessibility_score')}, R={state.get('rigor_score')}) ---"
        )
        return state

    print(f"\n--- Working article: {topic} ---")
    state["iteration_count"] = int(state.get("iteration_count", 0) or 0) + 1
    state["status"] = "in_progress"
    state["last_worked_on"] = today_iso()
    write_yaml(p.state, state)

    try:
        run_role(p, state, "planner", planner_role, required=False)

        run_role(p, state, "writer", writer_role, required=True)

        if not read_text(p.draft).strip():
            raise RuntimeError("Writer completed but draft.md is empty.")

        run_role(p, state, "term_collector", term_collector_role, required=False)
        run_role(p, state, "claim_extractor", claim_extractor_role, required=False)

        if not p.claims.exists():
            write_json(
                p.claims,
                {
                    "claims": [],
                    "last_updated": now_stamp(),
                    "note": "Claim extraction failed or produced no claims.",
                },
            )

        run_role(p, state, "source_finder", source_finder_role, required=False)
        run_role(p, state, "claim_checker", claim_checker_role, required=False)

        if not p.claim_checks.exists():
            write_json(
                p.claim_checks,
                {
                    "claim_checks": [],
                    "summary": {
                        "overall_claim_quality": "Claim checking was skipped or failed.",
                        "unresolved_or_needs_qualification": 1,
                        "highest_priority_fixes": ["Manually review claims or rerun claim checker."],
                    },
                    "last_updated": now_stamp(),
                },
            )

        run_role(p, state, "claim_revision", claim_revision_role, required=False)
        run_role(p, state, "term_collector", term_collector_role, required=False)

        accessibility_review = run_role(
            p,
            state,
            "accessibility_judge",
            accessibility_judge_role,
            required=False,
            default={
                "score": 0,
                "pass": False,
                "strengths": [],
                "issues": [
                    {
                        "severity": "high",
                        "location": "whole article",
                        "problem": "Accessibility judge failed.",
                        "suggested_fix": "Rerun review manually.",
                    }
                ],
                "best_next_revision": "Rerun accessibility review.",
            },
        )

        rigor_review = run_role(
            p,
            state,
            "rigor_judge",
            rigor_judge_role,
            required=False,
            default={
                "score": 0,
                "pass": False,
                "strengths": [],
                "issues": [
                    {
                        "severity": "high",
                        "location": "whole article",
                        "problem": "Rigor judge failed.",
                        "suggested_fix": "Rerun review manually.",
                    }
                ],
                "best_next_revision": "Rerun rigor review.",
            },
        )

        final_mdx_role(p, state)

        state = mark_scores_and_status(p, state, accessibility_review, rigor_review)

        print(
            f"  -> [done] A={state.get('accessibility_score')}/10, "
            f"R={state.get('rigor_score')}/10, status={state.get('status')}"
        )
        print(f"  -> [saved] {p.article_dir}")
        return state

    except Exception as exc:
        state["status"] = "error"
        state["last_error"] = repr(exc)
        state["last_worked_on"] = today_iso()
        write_yaml(p.state, state)

        error_log = p.article_dir / "logs" / f"ERROR_{now_stamp()}.txt"
        write_text(error_log, traceback.format_exc())

        print(f"  -> [error] {exc}")
        stop_ollama_model(p.article_dir, reason=f"article-level error in {topic}")
        return state


# =============================================================================
# 9. Batch runner
# =============================================================================


def select_topics(
    all_topics: List[str],
    explicit_topic: Optional[str],
    max_articles: Optional[int],
    force_finished: bool,
) -> List[str]:
    if explicit_topic:
        return [explicit_topic]

    selected = []
    for topic in all_topics:
        _, state = load_article_state(topic)
        if force_finished or not article_is_passing(state):
            selected.append(topic)
        if max_articles is not None and len(selected) >= max_articles:
            break
    return selected


def print_summary(topics: List[str]) -> None:
    print("\n=== Batch summary ===")
    for topic in topics:
        p, state = load_article_state(topic)
        print(
            f"- {topic}\n"
            f"  status={state.get('status')}, "
            f"A={state.get('accessibility_score')}, "
            f"R={state.get('rigor_score')}, "
            f"folder={p.article_dir}"
        )


def main() -> None:
    parser = argparse.ArgumentParser(description="Run EasyPhysics article workflow.")
    parser.add_argument("--topic", type=str, default=None, help="Run one explicit topic only.")
    parser.add_argument("--max-articles", type=int, default=None, help="Maximum number of articles to process this run.")
    parser.add_argument(
        "--force-finished",
        action="store_true",
        help="Process articles even if they already scored >= 9 on rigor and accessibility.",
    )
    args = parser.parse_args()

    topics = select_topics(
        TOPICS_TO_GENERATE,
        explicit_topic=args.topic,
        max_articles=args.max_articles,
        force_finished=args.force_finished,
    )

    if not topics:
        print("No articles need work. All selected articles are already passing.")
        return

    print(f"Starting workflow for {len(topics)} article(s).")
    print(f"Article root: {ARTICLE_ROOT}")

    for topic in topics:
        run_one_article_cycle(topic, force_finished=args.force_finished)

    print_summary(topics)


if __name__ == "__main__":
    main()
