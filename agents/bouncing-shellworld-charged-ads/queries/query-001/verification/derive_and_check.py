#!/usr/bin/env python3
"""Deterministically check the paper's exact zero-Lambda_4 solution.

The charged-shellworld Friedmann equation is a conditional input. This script
checks its conformal-time first integral, the displayed solution, turning
points, strict-bounce conditions, and both endpoints. It does not derive the
reduced equation from the five-dimensional junction condition and uses no
network access.
"""

from __future__ import annotations

import json
import platform
from pathlib import Path

import sympy as sp

OUTPUT = Path(__file__).with_name("check-result.json")
COMMAND = "python3 agents/bouncing-shellworld-charged-ads/queries/query-001/verification/derive_and_check.py"


def exact_text(expr: sp.Expr) -> str:
    return sp.sstr(sp.factor(sp.trigsimp(sp.simplify(expr))))


def checked_status(passed: bool) -> str:
    return "VERIFIED" if passed else "CHECK_FAILED"


def main() -> int:
    eta = sp.symbols("eta", real=True)
    D, E, omega = sp.symbols("D E omega_4", positive=True, finite=True)
    beta = sp.symbols("beta", real=True, finite=True)

    rho = 3 * E / (4 * D**2)
    e_from_beta = 4 * D**2 * (1 - beta**2) / 3
    x = omega * D * (1 - beta * sp.cos(2 * eta)) / 2
    x_min = omega * D * (1 - beta) / 2
    x_max = omega * D * (1 + beta) / 2

    residual_raw = sp.diff(x, eta) ** 2 - 4 * (-x**2 + omega * D * x - 3 * omega**2 * E / 16)
    residual = sp.simplify(residual_raw.subs(E, e_from_beta))
    turning = lambda value: sp.expand(value**2 - omega * D * value + 3 * omega**2 * E / 16)
    min_root_residual = sp.simplify(turning(x_min).subs(E, e_from_beta))
    max_root_residual = sp.simplify(turning(x_max).subs(E, e_from_beta))
    period_residual = sp.simplify(x.subs(eta, eta + sp.pi) - x)

    xp_min = sp.simplify(sp.diff(x, eta).subs(eta, 0))
    xpp_min = sp.simplify(sp.diff(x, eta, 2).subs(eta, 0))
    xp_max = sp.simplify(sp.diff(x, eta).subs(eta, sp.pi / 2))
    xpp_max = sp.simplify(sp.diff(x, eta, 2).subs(eta, sp.pi / 2))

    identity_passed = residual == 0
    roots_passed = min_root_residual == 0 and max_root_residual == 0
    period_passed = period_residual == 0
    stationary_passed = xp_min == 0 and xp_max == 0
    min_second_positive = sp.ask(sp.Q.positive(xpp_min), sp.Q.positive(beta)) is True
    max_second_negative = sp.ask(sp.Q.negative(xpp_max), sp.Q.positive(beta)) is True
    second_derivative_signs_passed = min_second_positive and max_second_negative

    xmin_counterexample_set = sp.reduce_inequalities([beta > 0, beta < 1, x_min <= 0], beta)
    xmin_positive_passed = xmin_counterexample_set is sp.false or xmin_counterexample_set == False  # noqa: E712

    nonconstant_difference = sp.simplify(x.subs(eta, sp.pi / 2) - x.subs(eta, 0))
    nonconstant_passed = sp.ask(sp.Q.positive(nonconstant_difference), sp.Q.positive(beta)) is True

    rho0_x = sp.simplify(x.subs(beta, 1))
    rho0_xmin = sp.simplify(x_min.subs(beta, 1))
    rho0_at_min = sp.simplify(rho0_x.subs(eta, 0))
    rho0_singular_passed = rho0_xmin == 0 and rho0_at_min == 0

    rho1_x = sp.simplify(x.subs(beta, 0))
    rho1_constancy = sp.simplify(rho1_x - rho1_x.subs(eta, 0))
    rho1_derivative = sp.simplify(sp.diff(rho1_x, eta))
    rho1_static_passed = rho1_constancy == 0 and rho1_derivative == 0

    discriminant = sp.factor((omega * D) ** 2 - 4 * 3 * omega**2 * E / 16)
    discriminant_beta = sp.simplify(discriminant.subs(E, e_from_beta))
    discriminant_passed = sp.simplify(discriminant_beta - omega**2 * D**2 * beta**2) == 0

    symbolic_checks = {
        "equivalent_first_integral": {"passed": identity_passed, "residual_before_beta_relation": exact_text(residual_raw), "residual_after_beta_relation": exact_text(residual)},
        "turning_polynomial_roots": {"passed": roots_passed, "minimum_residual": exact_text(min_root_residual), "maximum_residual": exact_text(max_root_residual), "x_min": exact_text(x_min), "x_max": exact_text(x_max)},
        "period_pi": {"passed": period_passed, "residual": exact_text(period_residual)},
        "stationary_extrema": {"passed": stationary_passed, "x_prime_at_zero": exact_text(xp_min), "x_prime_at_pi_over_2": exact_text(xp_max)},
        "second_derivative_signs_for_beta_positive": {"passed": second_derivative_signs_passed, "x_second_at_zero": exact_text(xpp_min), "minimum_positive_proved": min_second_positive, "x_second_at_pi_over_2": exact_text(xpp_max), "maximum_negative_proved": max_second_negative},
        "strict_positive_minimum_for_zero_lt_beta_lt_one": {"passed": xmin_positive_passed, "x_min": exact_text(x_min), "counterexample_inequalities_reduce_to": str(xmin_counterexample_set)},
        "nonconstancy_for_beta_positive": {"passed": nonconstant_passed, "x_pi_over_2_minus_x_zero": exact_text(nonconstant_difference)},
        "rho_zero_singular_endpoint": {"passed": rho0_singular_passed, "beta": "1", "x_at_nominal_minimum": exact_text(rho0_at_min), "x_min": exact_text(rho0_xmin)},
        "rho_one_static_endpoint": {"passed": rho1_static_passed, "beta": "0", "x": exact_text(rho1_x), "constancy_residual": exact_text(rho1_constancy), "derivative": exact_text(rho1_derivative)},
        "turning_polynomial_discriminant": {"passed": discriminant_passed, "in_D_E": exact_text(discriminant), "after_beta_relation": exact_text(discriminant_beta)},
    }

    sample = {D: sp.Integer(2), E: sp.Integer(4), omega: sp.Integer(2)}
    sample_rho = sp.simplify(rho.subs(sample))
    sample_beta = sp.sqrt(1 - sample_rho)
    sample_x = sp.simplify(x.subs(sample).subs(beta, sample_beta))
    sample_residual = sp.simplify(residual_raw.subs(sample).subs(beta, sample_beta))
    sample_passed = sample_residual == 0 and sample_x.subs(eta, 0) == 1 and sample_x.subs(eta, sp.pi / 2) == 3
    numerical_spot_check = {
        "passed": sample_passed,
        "parameters": {"D": "2", "E": "4", "omega_4": "2", "rho": exact_text(sample_rho), "beta": exact_text(sample_beta)},
        "solution_squared": exact_text(sample_x), "a_min_squared": exact_text(sample_x.subs(eta, 0)), "a_max_squared": exact_text(sample_x.subs(eta, sp.pi / 2)), "first_integral_residual": exact_text(sample_residual),
    }

    aggregate_checks = {**{name: row["passed"] for name, row in symbolic_checks.items()}, "exact_spot_check": sample_passed}
    aggregate_passed = all(aggregate_checks.values())
    endpoint_rows = []
    for case, passed, finding in (
        ("rho=0", rho0_singular_passed, "beta=1 and x_min=0, so the nominal bounce endpoint is singular."),
        ("rho=1", rho1_static_passed, "beta=0 and x is constant, so this endpoint is static rather than a nonconstant bounce."),
        ("0<rho<1", xmin_positive_passed and nonconstant_passed and second_derivative_signs_passed, "0<beta<1 gives x_min>0, nonconstancy, and a strict local minimum at eta=n*pi."),
    ):
        endpoint_rows.append({"case": case, "passed": passed, "status": checked_status(passed), "finding": finding})

    result = {
        "schema": "agtxiv.symbolic-check-result/1.0.0",
        "id": "check-result:2608.22855v1:zero-lambda-bounce",
        "command": COMMAND,
        "runtime": {"python_version": platform.python_version(), "python_implementation": platform.python_implementation(), "sympy_version": sp.__version__, "platform": platform.platform(), "network_required": False},
        "conditional_input": {"equation": "H^2=-a^-2+omega_4 D a^-4-(3 omega_4^2 E/16)a^-6 at Lambda_4=0", "status": "SOURCE_ATTESTED_NOT_DERIVED_IN_THIS_RUN", "unresolved_reduction": "The junction-to-Friedmann derivation and its approximation status are not checked."},
        "definitions": {"D": "(M_+ L_+ - M_- L_-)/(L_+ - L_-)", "E": "(Q_+^2 L_+ - Q_-^2 L_-)/(L_+ - L_-)", "rho": "3E/(4D^2)", "beta": "sqrt(1-rho)", "x": "a^2=(omega_4 D/2)(1-beta cos(2 eta))"},
        "symbolic_checks": symbolic_checks,
        "endpoint_checks": endpoint_rows,
        "numerical_spot_check": numerical_spot_check,
        "aggregate_checks": aggregate_checks,
        "aggregate_passed": aggregate_passed,
        "conditional_mathematical_outcome": "VERIFIED_WITH_ENDPOINT_QUALIFICATION" if aggregate_passed else "CHECK_FAILED",
        "literal_scientific_claim_outcome": "NOT_CHECKED",
        "scientific_acceptance": "NOT_REVIEWED",
        "qualification": "Conditional on the stated reduced equation and D>0, E>0, the nonconstant positive bounce regime is 0<rho<1. The literal source rho<=1 proposition includes the static rho=1 endpoint and does not by itself close physical applicability.",
        "scope_note": "No Lean checking, junction reduction, horizon ordering, phase scan, perturbative stability, or full scientific acceptance is claimed.",
    }
    OUTPUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0 if aggregate_passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
