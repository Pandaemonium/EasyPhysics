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
python auto_generate_articles.py

Optional examples
-----------------
python auto_generate_articles.py --max-articles 3
python auto_generate_articles.py --topic "Quantum superposition analogized as acoustic chords on a guitar string"
python auto_generate_articles.py --force-finished
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
from urllib.parse import urlparse

try:
    import yaml
except ImportError as exc:
    raise SystemExit(
        "Missing dependency: PyYAML. Install with: pip install pyyaml"
    ) from exc

from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_community.utilities import DuckDuckGoSearchAPIWrapper


# =============================================================================
# 1. Configuration
# =============================================================================

BASE_DIR = Path(os.environ.get("EASYPHYSICS_BASE_DIR", Path(__file__).resolve().parent)).resolve()
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
    "top_p": 0.8,
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

search_wrapper = DuckDuckGoSearchAPIWrapper(max_results=5)

PASSING_SCORE = 9
MAX_CLAIMS_TO_SEARCH_PER_PASS = 3
MAX_CLAIM_REVIEW_ROUNDS_PER_PASS = 4
MAX_SEARCH_ATTEMPTS_PER_CLAIM = 3
SOURCE_SEARCH_MAX_RESULTS = 5
MAX_SEARCH_RESULT_CHARS_PER_CLAIM = 1800
MAX_CONTEXT_CHARS = 30000

PASSING_CLAIM_VERDICTS = {"supported", "mostly_supported"}
ACTIONABLE_CLAIM_VERDICTS = {"needs_qualification", "unsupported", "contradicted"}
EVIDENCE_RETRY_VERDICTS = {"not_enough_evidence"}
VALID_CLAIM_VERDICTS = PASSING_CLAIM_VERDICTS | ACTIONABLE_CLAIM_VERDICTS | EVIDENCE_RETRY_VERDICTS


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


def url_domain(url: str) -> str:
    try:
        return urlparse(url).netloc.lower().removeprefix("www.")
    except Exception:
        return ""


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


def write_role_failure_artifact(
    article_dir: Path,
    node_name: str,
    error: Exception,
    default: Any = None,
) -> None:
    failure_path = article_dir / "logs" / f"{node_name}_failure_{now_stamp()}.json"
    write_json(
        failure_path,
        {
            "node": node_name,
            "created_at": now_stamp(),
            "error": repr(error),
            "traceback": traceback.format_exc(),
            "default_returned": default,
        },
    )


def archive_file(path: Path, archive_dir: Path, label: str) -> None:
    if not path.exists():
        return
    archive_dir.mkdir(parents=True, exist_ok=True)
    archived = archive_dir / f"{label}_{now_stamp()}{path.suffix}"
    archived.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")


def invalidate_claim_review_artifacts(p: "ArticlePaths", reason: str) -> None:
    """Archive draft-dependent claim artifacts before regenerating them."""
    artifact_paths = [
        (p.claims, "claims_before_invalidation"),
        (p.sources, "sources_before_invalidation"),
        (p.claim_checks, "claim_checks_before_invalidation"),
    ]
    archived = []
    for path, label in artifact_paths:
        if not path.exists():
            continue
        archive_file(path, p.history_dir, label)
        archived.append(str(path.name))
        path.unlink()

    if archived:
        append_event_log(
            p.article_dir,
            "claim_review",
            {
                "event": "claim_artifacts_invalidated",
                "reason": reason,
                "archived": archived,
            },
        )


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
        write_role_failure_artifact(p.article_dir, name, exc, default=default)

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

def build_revision_brief(p: ArticlePaths, max_items: int = 6) -> str:
    items = []

    claim_checks = read_json(p.claim_checks, {})
    for fix in claim_checks.get("summary", {}).get("highest_priority_fixes", [])[:3]:
        if fix:
            items.append(f"- Claim/research fix: {fix}")

    if p.reviews_dir.exists():
        review_files = sorted(
            p.reviews_dir.glob("*.json"),
            key=lambda x: x.stat().st_mtime,
            reverse=True,
        )

        for path in review_files[:4]:
            review = read_json(path, {})
            review_type = review.get("review_type", path.stem)
            score = review.get("score", "?")

            for issue in review.get("issues", [])[:2]:
                if not isinstance(issue, dict):
                    continue
                problem = issue.get("problem", "")
                fix = issue.get("suggested_fix", "")
                if problem or fix:
                    items.append(
                        f"- {review_type} score {score}: {problem} Suggested fix: {fix}"
                    )

            best_next = review.get("best_next_revision", "")
            if best_next:
                items.append(f"- {review_type} next revision: {best_next}")

            if len(items) >= max_items:
                break

    if not items:
        return "No specific prior review notes. Improve clarity, rigor, and flow without changing the article's scope."

    return "\n".join(items[:max_items])

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


def persist_review_artifact(
    p: ArticlePaths,
    review_type: str,
    round_num: int,
    data: Dict[str, Any],
    raw: str = "",
) -> Dict[str, Any]:
    data = dict(data or {})
    data.setdefault("review_type", review_type)
    data.setdefault("round", round_num)
    data.setdefault("created_at", now_stamp())
    path = p.reviews_dir / f"{review_type}_round_{round_num:03d}.json"
    write_json(path, data)
    if raw:
        write_text(p.article_dir / f"{review_type}_judge_raw_round_{round_num:03d}.txt", raw)
    return data


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
        "claim_review_passed": False,
        "claim_total_count": 0,
        "claim_checked_count": 0,
        "claim_unchecked_count": 0,
        "claim_unresolved_count": 0,
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
    claim_summary = summarize_claim_review(p)
    merged["claim_review_passed"] = bool(claim_summary.get("claim_review_complete"))
    merged["claim_total_count"] = int(claim_summary.get("total_claims", 0) or 0)
    merged["claim_checked_count"] = int(claim_summary.get("checked_claim_count", 0) or 0)
    merged["claim_unchecked_count"] = int(claim_summary.get("unchecked_claim_count", 0) or 0)
    merged["claim_unresolved_count"] = int(
        claim_summary.get("unresolved_or_needs_qualification", 0) or 0
    )
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

    claim_summary = summarize_claim_review(p)
    unchecked = int(claim_summary.get("unchecked_claim_count", 0) or 0)
    unresolved = int(claim_summary.get("unresolved_or_needs_qualification", 0) or 0)
    actionable = int(claim_summary.get("actionable_issue_count", 0) or 0)
    evidence_retry = int(claim_summary.get("evidence_retry_count", 0) or 0)
    claim_review_passed = bool(claim_summary.get("claim_review_complete"))

    if unchecked:
        needs.append("claim_check")
    if evidence_retry:
        needs.append("source_retry")
    if actionable:
        needs.append("claim_revision")
    if unresolved and not actionable and not evidence_retry:
        needs.append("claim_review")

    state["claim_review_passed"] = claim_review_passed
    state["claim_total_count"] = int(claim_summary.get("total_claims", 0) or 0)
    state["claim_checked_count"] = int(claim_summary.get("checked_claim_count", 0) or 0)
    state["claim_unchecked_count"] = unchecked
    state["claim_unresolved_count"] = unresolved

    state["needs"] = needs
    state["finished"] = (
        accessibility_score >= PASSING_SCORE
        and rigor_score >= PASSING_SCORE
        and claim_review_passed
    )
    state["status"] = "finished" if state["finished"] else "needs_revision"

    write_yaml(p.state, state)
    return state


def claim_requires_external_check(claim: Dict[str, Any]) -> bool:
    return bool(claim.get("needs_external_check", True))


def claim_importance_rank(claim: Dict[str, Any]) -> int:
    return {"high": 0, "medium": 1, "low": 2}.get(claim.get("importance", "medium"), 1)


def latest_claim_checks_by_id(claim_checks_data: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    checks = claim_checks_data.get("claim_checks", [])
    latest: Dict[str, Dict[str, Any]] = {}
    if not isinstance(checks, list):
        return latest
    for check in checks:
        if not isinstance(check, dict):
            continue
        claim_id = str(check.get("id", "")).strip()
        if claim_id:
            latest[claim_id] = check
    return latest


def claim_check_passes(check: Optional[Dict[str, Any]]) -> bool:
    if not check:
        return False
    verdict = str(check.get("verdict", "")).strip()
    severity = str(check.get("severity", "none")).strip()
    return verdict in PASSING_CLAIM_VERDICTS and severity in {"none", "low", ""}


def claim_check_needs_revision(check: Optional[Dict[str, Any]]) -> bool:
    if not check:
        return False
    verdict = str(check.get("verdict", "")).strip()
    severity = str(check.get("severity", "none")).strip()
    if verdict in ACTIONABLE_CLAIM_VERDICTS:
        return True
    if (
        verdict in EVIDENCE_RETRY_VERDICTS
        and int(check.get("source_attempt_count", 0) or 0) >= MAX_SEARCH_ATTEMPTS_PER_CLAIM
    ):
        return True
    return severity in {"medium", "high"} and verdict not in EVIDENCE_RETRY_VERDICTS


def claim_check_needs_more_evidence(check: Optional[Dict[str, Any]]) -> bool:
    if not check:
        return False
    return (
        str(check.get("verdict", "")).strip() in EVIDENCE_RETRY_VERDICTS
        and int(check.get("source_attempt_count", 0) or 0) < MAX_SEARCH_ATTEMPTS_PER_CLAIM
    )


def summarize_claim_review_data(
    claims: List[Dict[str, Any]],
    checks: List[Dict[str, Any]],
) -> Dict[str, Any]:
    checkable_claims = [c for c in claims if claim_requires_external_check(c)]
    latest = latest_claim_checks_by_id({"claim_checks": checks})
    checked = [c for c in checkable_claims if c.get("id") in latest]
    passing = [c for c in checked if claim_check_passes(latest.get(c.get("id")))]
    unchecked = [c for c in checkable_claims if c.get("id") not in latest]
    revision_needed = [
        c for c in checked if claim_check_needs_revision(latest.get(c.get("id")))
    ]
    evidence_retry = [
        c for c in checked if claim_check_needs_more_evidence(latest.get(c.get("id")))
    ]
    unresolved = [
        c
        for c in checked
        if not claim_check_passes(latest.get(c.get("id")))
    ]

    total = len(checkable_claims)
    review_complete = total > 0 and not unchecked and not unresolved
    return {
        "total_claims": total,
        "checked_claim_count": len(checked),
        "passing_claim_count": len(passing),
        "unchecked_claim_count": len(unchecked),
        "unresolved_or_needs_qualification": len(unresolved) + len(unchecked),
        "actionable_issue_count": len(revision_needed),
        "evidence_retry_count": len(evidence_retry),
        "claim_review_complete": review_complete,
        "unchecked_claim_ids": [c.get("id") for c in unchecked if c.get("id")],
        "actionable_claim_ids": [c.get("id") for c in revision_needed if c.get("id")],
        "evidence_retry_claim_ids": [c.get("id") for c in evidence_retry if c.get("id")],
        "highest_priority_fixes": [
            latest.get(c.get("id"), {}).get("suggested_fix", "")
            for c in revision_needed
            if latest.get(c.get("id"), {}).get("suggested_fix")
        ][:5],
    }


def summarize_claim_review(p: ArticlePaths) -> Dict[str, Any]:
    claims_data = read_json(p.claims, {"claims": []})
    claim_checks_data = read_json(p.claim_checks, {"claim_checks": []})
    claims = claims_data.get("claims", [])
    checks = claim_checks_data.get("claim_checks", [])
    if not isinstance(claims, list):
        claims = []
    if not isinstance(checks, list):
        checks = []
    return summarize_claim_review_data(claims, checks)


def normalize_claim_check_payload(payload: Any, claim_id: str) -> Dict[str, Any]:
    if not isinstance(payload, dict):
        payload = {}

    verdict = str(payload.get("verdict", "not_enough_evidence")).strip()
    if verdict not in VALID_CLAIM_VERDICTS:
        verdict = "not_enough_evidence"

    severity = str(payload.get("severity", "medium")).strip()
    if severity not in {"none", "low", "medium", "high"}:
        severity = "medium"

    source_urls = payload.get("source_urls", [])
    if not isinstance(source_urls, list):
        source_urls = []

    return {
        "id": str(payload.get("id") or claim_id),
        "verdict": verdict,
        "severity": severity,
        "problem": str(payload.get("problem", "")),
        "suggested_fix": str(payload.get("suggested_fix", "")),
        "source_quality_note": str(payload.get("source_quality_note", "")),
        "source_urls": [str(url) for url in source_urls if url],
    }


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
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=45,
            check=False,
        )

        stdout = completed.stdout.decode("utf-8", errors="replace")
        stderr = completed.stderr.decode("utf-8", errors="replace")

        append_event_log(
            article_dir,
            "ollama_reset",
            {
                "event": "ollama_stop_model",
                "reason": reason,
                "returncode": completed.returncode,
                "stdout": stdout[-1000:],
                "stderr": stderr[-1000:],
            },
        )

        time.sleep(3)

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


def safe_search(query: str) -> Dict[str, Any]:
    try:
        raw_results = search_wrapper.results(
            query,
            max_results=SOURCE_SEARCH_MAX_RESULTS,
            source="text",
        )
        results = []
        for result in raw_results:
            url = str(result.get("link") or result.get("url") or "").strip()
            snippet = limit_chars(
                str(result.get("snippet") or result.get("body") or ""),
                MAX_SEARCH_RESULT_CHARS_PER_CLAIM,
            )
            results.append(
                {
                    "title": str(result.get("title") or "").strip(),
                    "url": url,
                    "domain": url_domain(url),
                    "snippet": snippet,
                }
            )

        result_snippet = "\n\n".join(
            f"[{i}] {r['title']}\nURL: {r['url']}\nSnippet: {r['snippet']}"
            for i, r in enumerate(results, start=1)
        )
        return {
            "status": "ok" if results else "no_results",
            "query": query,
            "results": results,
            "urls": [r["url"] for r in results if r.get("url")],
            "result_snippet": limit_chars(result_snippet, MAX_SEARCH_RESULT_CHARS_PER_CLAIM * 2),
            "searched_at": now_stamp(),
        }
    except Exception as exc:
        return {
            "status": "failed",
            "query": query,
            "results": [],
            "urls": [],
            "result_snippet": f"SEARCH_FAILED: {exc}",
            "searched_at": now_stamp(),
            "error": repr(exc),
        }


# =============================================================================
# 6. Workflow roles
# =============================================================================


def planner_role(p: ArticlePaths, state: Dict[str, Any]) -> None:
    if p.outline.exists() and read_text(p.outline).strip():
        print("  -> [planner] outline already exists; reusing it.")
        return

    prompt = f"""
Create a teaching outline for an EasyPhysics article.

Title: {state['title']}

Audience:
- Motivated high-schooler or college freshman.
- Curious, smart, but not assumed to know advanced math.

Return Markdown with these sections:

## Scope
What this article should explain.

## Out of scope
What this article should not try to cover yet.

## Core intuition
The one idea the reader should remember.

## Prerequisites
Concepts the reader should know first.

## Suggested terminology
Candidate intuitive names with standard terms in braces.

## Common misconceptions
Misleading pictures or explanations to avoid.

## Minimal math
Only the math that genuinely helps, with what each symbol means.

## Diagram ideas
Concrete diagrams that would help.

## Section outline
A clear beginner-friendly article structure.
""".strip()

    outline = invoke_llm(p.article_dir, "planner", prompt)
    write_text(p.outline, outline)


def writer_role(p: ArticlePaths, state: Dict[str, Any]) -> None:
    outline = read_text(p.outline)
    notes = read_text(p.notes)

    prompt = f"""
Write a first draft of an EasyPhysics article.

Title: {state['title']}

Article outline:
{limit_chars(outline, 9000)}

Human/editor notes:
{limit_chars(notes, 2000)}

Required structure:
# {state['title']}

## The core idea
## Why this matters
## The simple picture
## The more precise picture
## Common misconceptions
## How this connects to the rest of physics
## Recap

Writing rules:
- Begin with meaning, not jargon.
- Use intuitive teaching names with standard terms in braces.
- Keep the article concept-first, not history-first.
- Use concrete examples before abstractions.
- Include math only when it helps; explain every symbol in words.
- Avoid “spooky,” “magic,” or “physics is weird” framing.
- State analogy limits when an analogy could mislead.
- Keep the article roughly 1200-1800 words unless the topic genuinely needs more.
- Output only Markdown. No commentary before or after.
""".strip()

    previous_draft = read_text(p.draft)
    revision_brief = build_revision_brief(p)

    if previous_draft.strip():
        prompt = f"""
Revise this existing EasyPhysics article once.

Title: {state['title']}

Revision brief:
{limit_chars(revision_brief, 3500)}

Human/editor notes:
{limit_chars(notes, 2000)}

Current draft:
{limit_chars(previous_draft, 16000)}

Instructions:
- Return the complete revised article in Markdown.
- Do not start from scratch.
- Preserve good explanations.
- Fix only the most important clarity, structure, and rigor problems.
- If a section is already good, leave it mostly alone.
- Add qualifications where the current draft overclaims.
- Make the opening more intuitive if needed.
- Keep standard terms in braces after intuitive names.
- Do not include commentary before or after the article.
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

    if previous_draft.strip():
        archive_file(p.draft, p.history_dir, "draft_before_revision")

    write_text(p.draft, new_draft)
    if previous_draft.strip():
        invalidate_claim_review_artifacts(p, reason="writer_revision")


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

    merged: Dict[Tuple[str, str], Dict[str, Any]] = {}
    for term in existing.get("terms", []):
        if not isinstance(term, dict):
            continue
        key = (
            str(term.get("standard_term", "")).strip().lower(),
            str(term.get("candidate_name", "")).strip().lower(),
        )
        if key != ("", ""):
            merged[key] = term

    for term in data.get("terms", []):
        if not isinstance(term, dict):
            continue
        key = (
            str(term.get("standard_term", "")).strip().lower(),
            str(term.get("candidate_name", "")).strip().lower(),
        )
        if key == ("", ""):
            continue
        merged[key] = {**merged.get(key, {}), **term, "last_seen": now_stamp()}

    existing["terms"] = list(merged.values())
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
                "why_it_matters": "Automatically extracted fallback claim; keep it in the claim-check pipeline.",
                "suggested_search_query": build_fallback_search_query(topic, sentence),
            }
        )

    return claims


def claim_extractor_role(p: ArticlePaths, state: Dict[str, Any]) -> None:
    draft = read_text(p.draft)

    prompt = f"""
Extract 8 to 12 important scientific or explanatory claims from this article draft.

Return exactly one JSON object with this shape:
{{
  "claims": [
    {{
      "id": "C001",
      "claim": "A clear standalone claim.",
      "type": "definition",
      "importance": "high",
      "needs_external_check": true,
      "why_it_matters": "brief reason",
      "suggested_search_query": "stable physics source query"
    }}
  ]
}}

Rules:
- Return a JSON object, not a list.
- Do not return an empty list unless the draft is empty.
- Use true/false, not True/False.
- No Markdown fences.
- No prose outside the JSON.
- Prefer claims that matter for scientific correctness.
- Include claims where an analogy could mislead.
- Search queries should target stable sources: textbooks, lecture notes, CERN, Fermilab, NASA, DOE, NIST, or university pages.

Article title: {state['title']}

Draft:
{limit_chars(draft, 22000)}
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


def build_claim_search_query(topic: str, claim: Dict[str, Any], attempt_number: int) -> str:
    claim_text = claim.get("claim", "")
    suggested = claim.get("suggested_search_query") or build_fallback_search_query(
        topic,
        claim_text,
    )
    claim_words = " ".join(str(claim_text).split()[:18])
    variants = [
        suggested,
        f"{topic} {claim_words} university physics lecture notes textbook",
        f"{topic} {claim_words} site:edu physics",
        f"{topic} {claim_words} CERN Fermilab NASA DOE NIST physics explanation",
    ]
    index = min(max(attempt_number, 1) - 1, len(variants) - 1)
    return clean_search_query(variants[index])


def select_claims_for_source(
    claims: List[Dict[str, Any]],
    sources_by_claim: Dict[str, Any],
    latest_checks: Dict[str, Dict[str, Any]],
) -> List[Dict[str, Any]]:
    selected = []
    for claim in sorted(claims, key=claim_importance_rank):
        if not claim_requires_external_check(claim):
            continue
        claim_id = claim.get("id")
        if not claim_id:
            continue
        check = latest_checks.get(claim_id)
        if claim_check_passes(check) or claim_check_needs_revision(check):
            continue

        source_entry = sources_by_claim.get(claim_id, {})
        attempt_count = int(source_entry.get("attempt_count", 0) or 0)
        checked_source_attempt = int((check or {}).get("source_attempt_count", 0) or 0)

        needs_first_search = attempt_count == 0
        needs_better_search = (
            claim_check_needs_more_evidence(check)
            and attempt_count <= checked_source_attempt
            and attempt_count < MAX_SEARCH_ATTEMPTS_PER_CLAIM
        )
        previous_search_failed = (
            source_entry.get("search_status") in {"failed", "no_results"}
            and attempt_count < MAX_SEARCH_ATTEMPTS_PER_CLAIM
        )

        if needs_first_search or needs_better_search or previous_search_failed:
            selected.append(claim)
    return selected


def source_finder_role(p: ArticlePaths, state: Dict[str, Any]) -> int:
    claims_data = read_json(p.claims, {"claims": []})
    claims = claims_data.get("claims", [])
    existing_sources = read_json(p.sources, {"sources_by_claim": {}})
    sources_by_claim = existing_sources.setdefault("sources_by_claim", {})
    latest_checks = latest_claim_checks_by_id(read_json(p.claim_checks, {"claim_checks": []}))

    print(f"  -> [source_finder] loaded {len(claims)} claim(s).")

    candidates = select_claims_for_source(claims, sources_by_claim, latest_checks)
    candidates = candidates[:MAX_CLAIMS_TO_SEARCH_PER_PASS]

    if not candidates:
        print("  -> [source_finder] no claims selected for search.")
        existing_sources["summary"] = summarize_claim_review(p)
        existing_sources["last_updated"] = now_stamp()
        write_json(p.sources, existing_sources)
        return 0

    print(f"  -> [source_finder] searching for {len(candidates)} claim(s)...")
  
    for claim in candidates:
        claim_id = claim.get("id")
        if not claim_id:
            continue

        source_entry = sources_by_claim.setdefault(
            claim_id,
            {
                "claim": claim.get("claim", ""),
                "search_attempts": [],
            },
        )
        attempts = source_entry.setdefault("search_attempts", [])
        attempt_number = len(attempts) + 1
        query = build_claim_search_query(state["title"], claim, attempt_number)
        search_data = safe_search(query)
        search_data["attempt_number"] = attempt_number

        attempts.append(search_data)
        source_entry.update(
            {
                "claim": claim.get("claim", ""),
                "query": query,
                "search_status": search_data.get("status", ""),
                "result_snippet": search_data.get("result_snippet", ""),
                "results": search_data.get("results", []),
                "urls": search_data.get("urls", []),
                "attempt_count": len(attempts),
                "searched_at": search_data.get("searched_at", now_stamp()),
                "source_policy": "Prefer stable accepted physics sources; avoid novelty unless topic requires it.",
            }
        )
        sources_by_claim[claim_id] = source_entry
        time.sleep(0.5)  # Be polite to the search backend.
    print(f"  -> [source_finder] selected {len(candidates)} claim(s) for search.")

    existing_sources["summary"] = summarize_claim_review(p)
    existing_sources["last_updated"] = now_stamp()
    write_json(p.sources, existing_sources)
    return len(candidates)


def clean_search_query(query: str) -> str:
    query = re.sub(r"\s+", " ", query).strip()
    query = query.replace("latest", "")
    if len(query) > 240:
        query = query[:240]
    return query


def select_claims_for_check(
    claims: List[Dict[str, Any]],
    sources_by_claim: Dict[str, Any],
    latest_checks: Dict[str, Dict[str, Any]],
) -> List[Dict[str, Any]]:
    selected = []
    for claim in sorted(claims, key=claim_importance_rank):
        if not claim_requires_external_check(claim):
            continue
        claim_id = claim.get("id")
        if not claim_id:
            continue
        check = latest_checks.get(claim_id)
        if claim_check_passes(check) or claim_check_needs_revision(check):
            continue

        source_entry = sources_by_claim.get(claim_id, {})
        attempt_count = int(source_entry.get("attempt_count", 0) or 0)
        checked_source_attempt = int((check or {}).get("source_attempt_count", 0) or 0)
        has_search_results = bool(source_entry.get("results")) or bool(source_entry.get("result_snippet"))
        never_checked = check is None and has_search_results
        has_new_sources = claim_check_needs_more_evidence(check) and attempt_count > checked_source_attempt
        maxed_source_attempts = (
            claim_check_needs_more_evidence(check)
            and attempt_count >= MAX_SEARCH_ATTEMPTS_PER_CLAIM
        )

        if never_checked or has_new_sources or maxed_source_attempts:
            selected.append(claim)
    return selected


def claim_checker_role(p: ArticlePaths, state: Dict[str, Any]) -> int:
    claims_data = read_json(p.claims, {"claims": []})
    sources_data = read_json(p.sources, {"sources_by_claim": {}})
    existing_checks_data = read_json(p.claim_checks, {"claim_checks": [], "check_history": []})
    draft = read_text(p.draft)

    claims = claims_data.get("claims", [])
    sources_by_claim = sources_data.get("sources_by_claim", {})
    latest_checks = latest_claim_checks_by_id(existing_checks_data)
    selected_claims = select_claims_for_check(claims, sources_by_claim, latest_checks)
    selected_claims = selected_claims[:MAX_CLAIMS_TO_SEARCH_PER_PASS]

    if not selected_claims:
        print("  -> [claim_checker] no claims selected for checking.")
        summary = summarize_claim_review_data(claims, list(latest_checks.values()))
        existing_checks_data["summary"] = {
            **summary,
            "overall_claim_quality": "No claim-check work selected this round.",
        }
        existing_checks_data["last_updated"] = now_stamp()
        write_json(p.claim_checks, existing_checks_data)
        return 0

    new_checks = []
    timeout_count = 0

    for claim in selected_claims:
        claim_id = claim.get("id", "")
        source_context = sources_by_claim.get(claim_id, {})
        source_attempt_count = int(source_context.get("attempt_count", 0) or 0)
        source_urls = source_context.get("urls", [])

        prompt = f"""
Check this one article claim against the available structured search results.

Return JSON with this shape:
{{
  "id": "{claim_id}",
  "verdict": "supported | mostly_supported | needs_qualification | unsupported | contradicted | not_enough_evidence",
  "severity": "none | low | medium | high",
  "problem": "specific issue, or empty string",
  "suggested_fix": "specific correction to the article, or empty string",
  "source_quality_note": "brief note about whether the snippets look authoritative",
  "source_urls": ["URLs from the search results that support your verdict"]
}}

Rules:
- Be conservative.
- If the search results are weak, absent, or not clearly authoritative, say not_enough_evidence.
- Do not demand advanced nuance beyond the article's beginner scope.
- Do flag misleading simplifications.
- Focus on stable accepted physics.
- Do not import a new claim from a weak search result. Check the article's claim only.
- Use source_urls only for URLs present in the search results.

Article title: {state['title']}

Claim:
{json.dumps(claim, indent=2, ensure_ascii=False)}

Search results:
{limit_chars(json.dumps(source_context, indent=2, ensure_ascii=False), 7000)}

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
            raw_dir = p.article_dir / "claim_checker_raw"
            raw_dir.mkdir(parents=True, exist_ok=True)
            write_text(raw_dir / f"{claim_id}_{now_stamp()}.txt", raw)
            parsed = parse_json_loose(raw, None)
            data = normalize_claim_check_payload(parsed, claim_id)
            should_stop_after_this = False

        except Exception as exc:
            timeout_count += 1
            data = {
                "id": claim_id,
                "verdict": "not_enough_evidence",
                "severity": "medium",
                "problem": f"Claim checker failed: {repr(exc)}",
                "suggested_fix": "Automatically retry this claim with another source search or a smaller context.",
                "source_quality_note": "",
                "source_urls": [],
            }

            append_event_log(
                p.article_dir,
                "claim_checker",
                {
                    "event": "per_claim_check_failed",
                    "claim_id": claim_id,
                    "error": repr(exc),
                },
            )
            should_stop_after_this = "LLM_TIMEOUT" in repr(exc)

        data["claim"] = claim.get("claim", "")
        data["checked_at"] = now_stamp()
        data["source_attempt_count"] = source_attempt_count
        data["available_source_urls"] = source_urls
        if (
            data.get("verdict") in EVIDENCE_RETRY_VERDICTS
            and source_attempt_count >= MAX_SEARCH_ATTEMPTS_PER_CLAIM
            and not data.get("suggested_fix")
        ):
            data["suggested_fix"] = (
                "Make this claim more conservative or remove it because automated "
                "source search did not find enough support after multiple attempts."
            )
        if not data.get("source_urls") and data.get("verdict") in PASSING_CLAIM_VERDICTS:
            data["source_urls"] = source_urls[:3]

        latest_checks[claim_id] = data
        new_checks.append(data)

        if should_stop_after_this:
            break

    claim_ids = {c.get("id") for c in claims}
    ordered_checks = [
        latest_checks[c.get("id")]
        for c in claims
        if c.get("id") in latest_checks
    ]
    extras = [
        check for claim_id, check in latest_checks.items()
        if claim_id not in claim_ids
    ]
    check_history = existing_checks_data.get("check_history", [])
    if not isinstance(check_history, list):
        check_history = []
    check_history.extend(new_checks)
    summary = summarize_claim_review_data(claims, ordered_checks)

    result = {
        "claim_checks": ordered_checks + extras,
        "check_history": check_history[-200:],
        "summary": {
            **summary,
            "overall_claim_quality": (
                "Partial claim check completed."
                if timeout_count
                else "Claim check round completed."
            ),
        },
        "last_updated": now_stamp(),
    }

    write_json(p.claim_checks, result)
    return len(new_checks)


def claim_revision_role(p: ArticlePaths, state: Dict[str, Any]) -> bool:
    draft = read_text(p.draft)
    claim_checks = read_json(p.claim_checks, {})

    checks = claim_checks.get("claim_checks", [])
    serious_issues = [
        c for c in checks
        if claim_check_needs_revision(c)
    ]

    if not serious_issues:
        print("  -> [claim_revision] no actionable claim-check issues found; keeping draft.")
        return False

    archive_file(p.draft, p.history_dir, "draft_before_claim_revision")

    focused_feedback = {
        "claim_checks": serious_issues,
        "summary": {
            "highest_priority_fixes": [
                c.get("suggested_fix", "")
                for c in serious_issues
                if c.get("suggested_fix")
            ][:5],
        },
    }

    prompt = f"""
Revise the article once to address actionable claim-check feedback.

Do not rewrite for its own sake. Fix the scientific issues while preserving accessible language.

Only use the actionable feedback below. Missing evidence should normally be handled by source-search rounds first; if the feedback says the automated search attempts are exhausted, make the claim more conservative or remove it.

Actionable claim-check feedback:
{limit_chars(json.dumps(focused_feedback, indent=2, ensure_ascii=False), 14000)}

Current draft:
{limit_chars(draft, 30000)}

Instructions:
- Correct or qualify unsupported, contradicted, overstrong, or misleading claims.
- Preserve good accessible explanations.
- Do not add speculative research as settled fact.
- If an analogy was misleading, either repair it or state its limits.
- Keep standard terms in braces after descriptive names.
- Output only the revised article in Markdown.
""".strip()

    revised = invoke_llm(p.article_dir, "claim_revision", prompt)
    write_text(p.draft, revised)
    invalidate_claim_review_artifacts(p, reason="claim_revision")
    return True


def run_claim_review_rounds(p: ArticlePaths, state: Dict[str, Any]) -> Dict[str, Any]:
    """Search and check claims in small batches so the local model stays within context."""
    last_summary = summarize_claim_review(p)

    for round_index in range(1, MAX_CLAIM_REVIEW_ROUNDS_PER_PASS + 1):
        last_summary = summarize_claim_review(p)
        if last_summary.get("claim_review_complete"):
            print("  -> [claim_review] all extracted claims are passing.")
            break

        print(
            "  -> [claim_review] round "
            f"{round_index}/{MAX_CLAIM_REVIEW_ROUNDS_PER_PASS}: "
            f"checked={last_summary.get('checked_claim_count', 0)}/"
            f"{last_summary.get('total_claims', 0)}, "
            f"unresolved={last_summary.get('unresolved_or_needs_qualification', 0)}"
        )

        source_count = run_role(
            p,
            state,
            "source_finder",
            source_finder_role,
            required=False,
            default=0,
        ) or 0
        check_count = run_role(
            p,
            state,
            "claim_checker",
            claim_checker_role,
            required=False,
            default=0,
        ) or 0

        last_summary = summarize_claim_review(p)
        if last_summary.get("actionable_issue_count", 0):
            print("  -> [claim_review] actionable claim issue found; pausing checks for revision.")
            break

        if not source_count and not check_count:
            print("  -> [claim_review] no automated progress this round.")
            break

    return last_summary


def accessibility_judge_role(p: ArticlePaths, state: Dict[str, Any]) -> Dict[str, Any]:
    draft = read_text(p.draft)
    round_num = state.get("iteration_count", 0)

    prompt = f"""
Evaluate this EasyPhysics article for accessibility.

Return exactly one JSON object:
{{
  "score": 1,
  "pass": false,
  "strengths": ["specific strength"],
  "issues": [
    {{
      "severity": "low | medium | high",
      "location": "section name or short quote",
      "problem": "specific accessibility issue",
      "suggested_fix": "specific fix"
    }}
  ],
  "best_next_revision": "one concise paragraph"
}}

Rubric:
{ACCESSIBILITY_RUBRIC}

Rules:
- Return an object, not a list.
- Score must be an integer from 1 to 10.
- A 9 means publishable with light human editing.
- Do not give 9 or 10 if the opening is jargon-heavy.
- Do not give 9 or 10 if math appears without plain-language interpretation.
- Do not rewrite the article; only evaluate it.

Article title: {state['title']}

Draft:
{limit_chars(draft, 22000)}
""".strip()

    raw = invoke_llm(p.article_dir, "accessibility_judge", prompt, system_extra=ACCESSIBILITY_RUBRIC, expect_json=True)
    parsed = parse_json_loose(raw, {})
    data = normalize_review_payload(parsed, "accessibility")
    return persist_review_artifact(p, "accessibility", round_num, data, raw=raw)


def rigor_judge_role(p: ArticlePaths, state: Dict[str, Any]) -> Dict[str, Any]:
    draft = read_text(p.draft)
    claim_checks = read_json(p.claim_checks, {})
    round_num = state.get("iteration_count", 0)

    prompt = f"""
Evaluate this EasyPhysics article for scientific rigor.

Return exactly one JSON object:
{{
  "score": 1,
  "pass": false,
  "strengths": ["specific strength"],
  "issues": [
    {{
      "severity": "low | medium | high",
      "location": "section name or short quote",
      "problem": "specific rigor issue",
      "suggested_fix": "specific fix"
    }}
  ],
  "best_next_revision": "one concise paragraph"
}}

Rubric:
{RIGOR_RUBRIC}

Rules:
- Return an object, not a list.
- Score must be an integer from 1 to 10.
- A 9 means no major scientific errors and only light human editing needed.
- Penalize misleading analogies.
- Penalize overclaims.
- Penalize confusing settled physics with open questions.
- Do not demand graduate-level nuance for a beginner article.
- Do not rewrite the article; only evaluate it.

Claim-check context:
{limit_chars(json.dumps(claim_checks, indent=2, ensure_ascii=False), 6000)}

Article title: {state['title']}

Draft:
{limit_chars(draft, 22000)}
""".strip()

    raw = invoke_llm(p.article_dir, "rigor_judge", prompt, system_extra=RIGOR_RUBRIC, expect_json=True)
    parsed = parse_json_loose(raw, {})
    data = normalize_review_payload(parsed, "rigor")
    return persist_review_artifact(p, "rigor", round_num, data, raw=raw)


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
    merged: Dict[Tuple[str, str, str], Dict[str, Any]] = {}
    for term in bank.get("terms", []):
        if not isinstance(term, dict):
            continue
        key = (
            str(term.get("article_title", "")).strip().lower(),
            str(term.get("standard_term", "")).strip().lower(),
            str(term.get("candidate_name", "")).strip().lower(),
        )
        if key != ("", "", ""):
            merged[key] = term

    for term in terms:
        if not isinstance(term, dict):
            continue
        term = dict(term)
        term["article_title"] = article_title
        term["last_seen"] = now_stamp()
        key = (
            str(article_title).strip().lower(),
            str(term.get("standard_term", "")).strip().lower(),
            str(term.get("candidate_name", "")).strip().lower(),
        )
        if key == ("", "", ""):
            continue
        previous = merged.get(key, {})
        term.setdefault("captured_at", previous.get("captured_at", now_stamp()))
        merged[key] = {**previous, **term}

    bank["terms"] = list(merged.values())
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
    claim_review_passed = bool(state.get("claim_review_passed"))
    return bool(
        a is not None
        and r is not None
        and int(a) >= PASSING_SCORE
        and int(r) >= PASSING_SCORE
        and claim_review_passed
    )


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

        existing_draft_before_writer = read_text(p.draft).strip()
        writer_required = not bool(existing_draft_before_writer)

        run_role(
            p,
            state,
            "writer",
            writer_role,
            required=writer_required,
        )

        if not read_text(p.draft).strip():
            raise RuntimeError("No usable draft exists after writer step.")

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

        run_claim_review_rounds(p, state)

        if not p.claim_checks.exists():
            write_json(
                p.claim_checks,
                {
                    "claim_checks": [],
                    "summary": {
                        "overall_claim_quality": "Claim checking was skipped or failed.",
                        "unresolved_or_needs_qualification": 1,
                        "highest_priority_fixes": [
                            "Automatically rerun source finding and claim checking."
                        ],
                    },
                    "last_updated": now_stamp(),
                },
            )

        revised_after_claims = run_role(
            p,
            state,
            "claim_revision",
            claim_revision_role,
            required=False,
            default=False,
        )
        if revised_after_claims:
            run_role(p, state, "claim_extractor", claim_extractor_role, required=False)
            run_claim_review_rounds(p, state)

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
                        "suggested_fix": "Automatically rerun accessibility review.",
                    }
                ],
                "best_next_revision": "Automatically rerun accessibility review.",
            },
        )
        accessibility_review = persist_review_artifact(
            p,
            "accessibility",
            state.get("iteration_count", 0),
            accessibility_review,
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
                        "suggested_fix": "Automatically rerun rigor review.",
                    }
                ],
                "best_next_revision": "Automatically rerun rigor review.",
            },
        )
        rigor_review = persist_review_artifact(
            p,
            "rigor",
            state.get("iteration_count", 0),
            rigor_review,
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
