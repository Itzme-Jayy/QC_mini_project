import os

from dotenv import find_dotenv, load_dotenv

load_dotenv(find_dotenv(), override=True)


class Config:
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg2://sudoku:sudoku@localhost:5433/quantum_sudoku",
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:5173")

    # Quantum simulator limits. A statevector of n qubits needs 16 * 2**n bytes,
    # so 24 qubits is roughly 270 MB. The default of 16 keeps solves fast.
    DEFAULT_QUBIT_BUDGET = int(os.getenv("QUBIT_BUDGET", "16"))
    MIN_QUBIT_BUDGET = 8
    HARD_QUBIT_CAP = 24
    DEFAULT_SHOTS = int(os.getenv("GROVER_SHOTS", "64"))
    MAX_GROVER_ATTEMPTS = int(os.getenv("MAX_GROVER_ATTEMPTS", "10"))
    MAX_WINDOWS = int(os.getenv("MAX_WINDOWS", "400"))
    MAX_SOLVE_SECONDS = float(os.getenv("MAX_SOLVE_SECONDS", "180"))


class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
