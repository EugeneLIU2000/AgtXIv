#!/usr/bin/env python3
"""Deterministic finite-instance checks for the Stabilizerness pilot.

These checks are regression evidence, not a proof of the universal theorem and
not a reproduction of Figure 2.  The active-dependency physical example closes
an exact projected-RoM value with explicit primal and dual certificates.
"""

from __future__ import annotations

import argparse
import itertools
import json
import math
import platform
from pathlib import Path
from typing import Iterable, Sequence

import numpy as np


TOL = 1e-9
PAULI_1 = {
    "I": np.array([[1, 0], [0, 1]], dtype=complex),
    "X": np.array([[0, 1], [1, 0]], dtype=complex),
    "Y": np.array([[0, -1j], [1j, 0]], dtype=complex),
    "Z": np.array([[1, 0], [0, -1]], dtype=complex),
}


def pauli(label: str) -> np.ndarray:
    result = np.array([[1]], dtype=complex)
    for char in label:
        result = np.kron(result, PAULI_1[char])
    return result


def is_close(a: np.ndarray | float, b: np.ndarray | float, tol: float = TOL) -> bool:
    return bool(np.allclose(a, b, atol=tol, rtol=0.0))


def commutes(a: np.ndarray, b: np.ndarray) -> bool:
    return is_close(a @ b, b @ a)


def anticommutes(a: np.ndarray, b: np.ndarray) -> bool:
    return is_close(a @ b, -(b @ a))


def proportional_to_identity(a: np.ndarray) -> tuple[bool, complex]:
    dim = a.shape[0]
    phase = np.trace(a) / dim
    return is_close(a, phase * np.eye(dim, dtype=complex)), complex(phase)


def frustration_graph(matrices: Sequence[np.ndarray]) -> list[list[bool]]:
    size = len(matrices)
    adjacency = [[False] * size for _ in range(size)]
    for i, j in itertools.combinations(range(size), 2):
        adjacency[i][j] = adjacency[j][i] = anticommutes(matrices[i], matrices[j])
    return adjacency


def subsets(nodes: Sequence[int], include_empty: bool = False) -> Iterable[tuple[int, ...]]:
    start = 0 if include_empty else 1
    for length in range(start, len(nodes) + 1):
        yield from itertools.combinations(nodes, length)


def is_clique(adjacency: Sequence[Sequence[bool]], nodes: Sequence[int]) -> bool:
    return all(adjacency[i][j] for i, j in itertools.combinations(nodes, 2))


def clique_number(adjacency: Sequence[Sequence[bool]], nodes: Sequence[int]) -> int:
    return max((len(s) for s in subsets(tuple(nodes)) if is_clique(adjacency, s)), default=0)


def chromatic_number(adjacency: Sequence[Sequence[bool]], nodes: Sequence[int]) -> int:
    nodes = tuple(nodes)
    if not nodes:
        return 0
    ordered = sorted(nodes, key=lambda node: sum(adjacency[node][other] for other in nodes), reverse=True)

    def colorable(k: int) -> bool:
        colors: dict[int, int] = {}

        def visit(index: int) -> bool:
            if index == len(ordered):
                return True
            node = ordered[index]
            forbidden = {colors[other] for other in colors if adjacency[node][other]}
            for color in range(k):
                if color not in forbidden:
                    colors[node] = color
                    if visit(index + 1):
                        return True
                    del colors[node]
            return False

        return visit(0)

    for k in range(1, len(nodes) + 1):
        if colorable(k):
            return k
    raise AssertionError("finite graph was not colorable")


def perfect_graph_certificate(adjacency: Sequence[Sequence[bool]]) -> dict:
    nodes = tuple(range(len(adjacency)))
    checked = 0
    for induced in subsets(nodes, include_empty=True):
        checked += 1
        omega = clique_number(adjacency, induced)
        chi = chromatic_number(adjacency, induced)
        if chi != omega:
            return {"perfect": False, "checked_induced_subgraphs": checked, "counterexample": list(induced), "chi": chi, "omega": omega}
    return {"perfect": True, "checked_induced_subgraphs": checked}


def active_dependencies(labels: Sequence[str]) -> list[dict]:
    matrices = [pauli(label) for label in labels]
    relations: list[tuple[tuple[int, ...], complex]] = []
    for support in subsets(tuple(range(len(labels)))):
        product = np.eye(matrices[0].shape[0], dtype=complex)
        for index in support:
            product = product @ matrices[index]
        related, phase = proportional_to_identity(product)
        if related and not any(set(old).issubset(support) for old, _ in relations):
            relations.append((support, phase))
    result = []
    for support, phase in relations:
        if all(commutes(matrices[i], matrices[j]) for i, j in itertools.combinations(support, 2)):
            result.append({"support": [labels[i] for i in support], "phase": [round(phase.real), round(phase.imag)]})
    return result


def all_cliques(adjacency: Sequence[Sequence[bool]]) -> list[tuple[int, ...]]:
    return [s for s in subsets(tuple(range(len(adjacency)))) if is_clique(adjacency, s)]


def graph_only_formula(adjacency: Sequence[Sequence[bool]], expectation: Sequence[float]) -> float:
    return max(1.0, *(sum(abs(expectation[i]) for i in clique) for clique in all_cliques(adjacency)))


def signed_affine_l1(vertices: Sequence[Sequence[float]], target: Sequence[float]) -> tuple[float, list[float]]:
    """Solve a tiny l1 affine-decomposition LP by enumerating basic solutions."""
    vertex_array = np.asarray(vertices, dtype=float)
    target_array = np.asarray(target, dtype=float)
    count, dimension = vertex_array.shape
    a = np.vstack([vertex_array.T, np.ones(count)])
    rhs = np.concatenate([target_array, [1.0]])
    columns = np.concatenate([a, -a], axis=1)
    rank = dimension + 1
    best = math.inf
    best_x: np.ndarray | None = None
    for chosen in itertools.combinations(range(2 * count), rank):
        basis = columns[:, chosen]
        if np.linalg.matrix_rank(basis, tol=TOL) < rank:
            continue
        weights = np.linalg.solve(basis, rhs)
        if np.min(weights) < -TOL or not is_close(basis @ weights, rhs):
            continue
        objective = float(np.sum(np.maximum(weights, 0.0)))
        if objective + TOL < best:
            signed = np.zeros(count)
            for column, weight in zip(chosen, weights):
                index = column % count
                signed[index] += weight if column < count else -weight
            best = objective
            best_x = signed
    if best_x is None:
        raise RuntimeError("no feasible signed affine decomposition found")
    return best, best_x.tolist()


def expectation(rho: np.ndarray, labels: Sequence[str]) -> list[float]:
    values = [float(np.trace(pauli(label) @ rho).real) for label in labels]
    assert all(abs(np.trace(pauli(label) @ rho).imag) <= TOL for label in labels)
    return values


def all_two_qubit_projected_stabilizer_points(measurement_labels: Sequence[str]) -> list[tuple[float, ...]]:
    labels = ["".join(chars) for chars in itertools.product("IXYZ", repeat=2) if chars != ("I", "I")]
    matrices = [pauli(label) for label in labels]
    identity = np.eye(4, dtype=complex)
    projected: set[tuple[float, ...]] = set()
    states: set[tuple[float, ...]] = set()
    for i, j in itertools.combinations(range(len(labels)), 2):
        if not commutes(matrices[i], matrices[j]):
            continue
        related, _ = proportional_to_identity(matrices[i] @ matrices[j])
        if related:
            continue
        for sign_i, sign_j in itertools.product((-1, 1), repeat=2):
            rho = ((identity + sign_i * matrices[i]) @ (identity + sign_j * matrices[j])) / 4.0
            if not is_close(np.trace(rho), 1.0) or not is_close(rho @ rho, rho):
                continue
            state_key = tuple(np.round(np.concatenate([rho.real.ravel(), rho.imag.ravel()]), 12))
            states.add(state_key)
            values = tuple(round(value, 12) for value in expectation(rho, measurement_labels))
            projected.add(values)
    if len(states) != 60:
        raise AssertionError(f"expected 60 two-qubit pure stabilizer states, found {len(states)}")
    return sorted(projected)


def one_qubit_k3_case() -> dict:
    labels = ["X", "Y", "Z"]
    matrices = [pauli(label) for label in labels]
    adjacency = frustration_graph(matrices)
    a = sum(matrices) / math.sqrt(3.0)
    rho = (np.eye(2, dtype=complex) + a) / 2.0
    b = expectation(rho, labels)
    vertices = []
    for axis in range(3):
        for sign in (-1.0, 1.0):
            vertex = [0.0, 0.0, 0.0]
            vertex[axis] = sign
            vertices.append(vertex)
    direct, _ = signed_affine_l1(vertices, b)
    formula = graph_only_formula(adjacency, b)
    expected = math.sqrt(3.0)
    return {
        "labels": labels,
        "active_dependencies": active_dependencies(labels),
        "perfect_graph": perfect_graph_certificate(adjacency),
        "expectation": b,
        "direct_projected_rom": direct,
        "graph_formula": formula,
        "expected_capacity": expected,
        "passed": not active_dependencies(labels) and is_close(direct, formula) and is_close(formula, expected),
    }


def two_qubit_ising_path_case() -> dict:
    labels = ["XI", "IX", "ZZ"]
    matrices = [pauli(label) for label in labels]
    adjacency = frustration_graph(matrices)
    a = (matrices[0] + matrices[2]) / math.sqrt(2.0)
    rho = (np.eye(4, dtype=complex) + a) / 4.0
    b = expectation(rho, labels)
    vertices = [[sx, sy, 0.0] for sx, sy in itertools.product((-1.0, 1.0), repeat=2)]
    vertices += [[0.0, 0.0, -1.0], [0.0, 0.0, 1.0]]
    direct, _ = signed_affine_l1(vertices, b)
    formula = graph_only_formula(adjacency, b)
    expected = math.sqrt(2.0)
    return {
        "labels": labels,
        "active_dependencies": active_dependencies(labels),
        "perfect_graph": perfect_graph_certificate(adjacency),
        "expectation": b,
        "direct_projected_rom": direct,
        "graph_formula": formula,
        "expected_capacity": expected,
        "passed": not active_dependencies(labels) and is_close(direct, formula) and is_close(formula, expected),
    }


def commuting_parity_geometry_case() -> dict:
    labels = ["XX", "ZZ", "YY"]
    exact_vertices = [list(signs) for signs in itertools.product((-1.0, 1.0), repeat=3) if math.prod(signs) == -1]
    relaxed_vertices = [list(signs) for signs in itertools.product((-1.0, 1.0), repeat=3)]
    pseudo_b = [1.0, 1.0, 1.0]
    exact, _ = signed_affine_l1(exact_vertices, pseudo_b)
    relaxed, _ = signed_affine_l1(relaxed_vertices, pseudo_b)
    return {
        "labels": labels,
        "active_dependencies": active_dependencies(labels),
        "exact_vertex_count": len(exact_vertices),
        "relaxed_vertex_count": len(relaxed_vertices),
        "pseudo_expectation": pseudo_b,
        "pseudo_expectation_is_quantum_realizable": False,
        "exact_signed_affine_l1": exact,
        "relaxed_signed_affine_l1": relaxed,
        "passed": bool(active_dependencies(labels)) and is_close(exact, 2.0) and is_close(relaxed, 1.0),
    }


def active_dependency_physical_counterexample() -> dict:
    labels = ["XX", "ZZ", "YY", "IX", "XI"]
    matrices = [pauli(label) for label in labels]
    adjacency = frustration_graph(matrices)
    psi = np.array([1.0, 1.0, 1.0 + 1.0j, 0.0], dtype=complex) / 2.0
    rho = np.outer(psi, np.conjugate(psi))
    b = expectation(rho, labels)
    stabilizer_points = all_two_qubit_projected_stabilizer_points(labels)

    dual_y = np.array([-0.5, -0.5, 0.5, 0.5, 0.5])
    dual_mu = 0.5
    dual_values = [abs(float(np.dot(point, dual_y) + dual_mu)) for point in stabilizer_points]
    dual_objective = float(np.dot(b, dual_y) + dual_mu)

    primal_coefficients = np.array([1 / 8, 1 / 8, 1 / 2, -1 / 8, 3 / 8], dtype=float)
    primal_vertices = np.array(
        [
            [-1, -1, -1, 0, 0],
            [-1, 1, 1, 0, 0],
            [1, -1, 1, 0, 0],
            [1, 0, 0, -1, -1],
            [1, 0, 0, 1, 1],
        ],
        dtype=float,
    )
    stabilizer_set = set(stabilizer_points)
    listed_vertices_valid = all(tuple(row) in stabilizer_set for row in primal_vertices)
    primal_reconstruction = primal_coefficients @ primal_vertices
    primal_value = float(np.sum(np.abs(primal_coefficients)))
    graph_value = graph_only_formula(adjacency, b)
    expected = 1.25

    return {
        "labels": labels,
        "active_dependencies": active_dependencies(labels),
        "perfect_graph": perfect_graph_certificate(adjacency),
        "expectation": b,
        "projected_stabilizer_point_count": len(stabilizer_points),
        "graph_only_formula": graph_value,
        "dual_certificate": {
            "y": dual_y.tolist(),
            "mu": dual_mu,
            "objective": dual_objective,
            "maximum_vertex_constraint": max(dual_values),
        },
        "primal_certificate": {
            "coefficients": primal_coefficients.tolist(),
            "vertices": primal_vertices.tolist(),
            "coefficient_sum": float(np.sum(primal_coefficients)),
            "l1_value": primal_value,
            "reconstruction": primal_reconstruction.tolist(),
            "all_vertices_are_projected_stabilizer_points": listed_vertices_valid,
        },
        "exact_projected_rom": expected,
        "passed": (
            bool(active_dependencies(labels))
            and perfect_graph_certificate(adjacency)["perfect"]
            and is_close(b, [0.5, -0.5, 0.5, 0.5, 0.5])
            and is_close(graph_value, 1.0)
            and listed_vertices_valid
            and is_close(np.sum(primal_coefficients), 1.0)
            and is_close(primal_reconstruction, b)
            and is_close(primal_value, expected)
            and max(dual_values) <= 1.0 + TOL
            and is_close(dual_objective, expected)
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    cases = {
        "one_qubit_k3_positive": one_qubit_k3_case(),
        "two_qubit_ising_path_positive": two_qubit_ising_path_case(),
        "commuting_parity_geometry_negative_control": commuting_parity_geometry_case(),
        "active_dependency_physical_counterexample": active_dependency_physical_counterexample(),
    }
    result = {
        "schema_version": "0.1.0-prototype",
        "claim_scope": "finite deterministic regression evidence only",
        "environment": {
            "python": platform.python_version(),
            "numpy": np.__version__,
            "float": "float64",
            "tolerance": TOL,
            "random_seed": None,
        },
        "cases": cases,
        "all_passed": all(case["passed"] for case in cases.values()),
        "warning": "Passing these examples does not verify the universal closed-form theorem or reproduce Figure 2.",
    }
    rendered = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0 if result["all_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
