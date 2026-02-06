"""
reporting.py — Generación uniforme de outputs para cada caso.

Produce metrics.json y report.md con formato estandarizado.
"""

import json
import os
import subprocess
from datetime import datetime


def get_git_info():
    """Obtiene info del repositorio git."""
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    try:
        top = subprocess.check_output(
            ["git", "-C", repo_root, "rev-parse", "--show-toplevel"],
            text=True, stderr=subprocess.DEVNULL
        ).strip()
        commit = subprocess.check_output(
            ["git", "-C", repo_root, "rev-parse", "HEAD"],
            text=True, stderr=subprocess.DEVNULL
        ).strip()
        status = subprocess.check_output(
            ["git", "-C", repo_root, "status", "--porcelain"],
            text=True, stderr=subprocess.DEVNULL
        ).strip()
        return {"root": top, "commit": commit, "dirty": bool(status)}
    except Exception:
        return {"root": None, "commit": None, "dirty": None}


def build_results_envelope(phases, case_name=""):
    """Construye el envelope estándar de resultados."""
    return {
        "case": case_name,
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "git": get_git_info(),
        "phases": phases,
    }


def write_outputs(results, output_dir):
    """Escribe metrics.json y report.md."""
    os.makedirs(output_dir, exist_ok=True)

    metrics_path = os.path.join(output_dir, "metrics.json")
    with open(metrics_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, default=_json_default)

    report_path = os.path.join(output_dir, "report.md")
    with open(report_path, "w", encoding="utf-8") as f:
        case_name = results.get("case", "Desconocido")
        f.write(f"# Reporte de Validación — {case_name}\n\n")
        f.write("## Metadata\n")
        f.write(f"- generated_at: {results['generated_at']}\n")
        git = results.get("git", {})
        f.write(f"- git_commit: {git.get('commit', 'N/A')}\n")
        f.write(f"- git_dirty: {git.get('dirty', 'N/A')}\n\n")

        for label, phase in results.get("phases", {}).items():
            _write_phase_report(f, label, phase)

    return metrics_path, report_path


def _json_default(obj):
    """Serializa tipos no estándar."""
    if hasattr(obj, "item"):
        return obj.item()
    if hasattr(obj, "tolist"):
        return obj.tolist()
    return str(obj)


def _write_phase_report(f, label, results):
    """Escribe sección de una fase en el reporte."""
    f.write(f"## Fase {label}\n")
    overall = results.get("overall_pass", "N/A")
    f.write(f"- **overall_pass**: {overall}\n\n")

    if "data" in results:
        d = results["data"]
        f.write("### Datos\n")
        for key in ["start", "end", "split", "steps", "val_steps", "coverage"]:
            if key in d:
                val = d[key]
                if isinstance(val, float):
                    f.write(f"- {key}: {val:.3f}\n")
                else:
                    f.write(f"- {key}: {val}\n")
        f.write("\n")

    if "calibration" in results:
        f.write("### Calibración\n")
        for key, val in results["calibration"].items():
            if isinstance(val, float):
                f.write(f"- {key}: {val:.4f}\n")
            else:
                f.write(f"- {key}: {val}\n")
        f.write("\n")

    f.write("### Criterios C1-C5\n")
    for ci in ["c1_convergence", "c2_robustness", "c3_replication", "c4_validity", "c5_uncertainty"]:
        if ci in results:
            val = results[ci]
            if isinstance(val, dict):
                f.write(f"- {ci}: {val.get('pass', 'N/A')}\n")
            else:
                f.write(f"- {ci}: {val}\n")
    f.write("\n")

    if "errors" in results:
        f.write("### Errores\n")
        for key, val in results["errors"].items():
            if isinstance(val, float):
                f.write(f"- {key}: {val:.4f}\n")
            else:
                f.write(f"- {key}: {val}\n")
        f.write("\n")

    if "edi" in results:
        f.write("### EDI (Effective Dependence Index)\n")
        edi = results["edi"]
        if isinstance(edi, dict):
            f.write(f"- edi: {edi.get('value', 'N/A')}\n")
            if "ci_lo" in edi:
                f.write(f"- ci_95: [{edi['ci_lo']:.3f}, {edi['ci_hi']:.3f}]\n")
        else:
            f.write(f"- edi: {edi}\n")
        f.write("\n")

    if "symploke" in results:
        f.write("### Symploké\n")
        s = results["symploke"]
        f.write(f"- internal: {s.get('internal', 'N/A')}\n")
        f.write(f"- external: {s.get('external', 'N/A')}\n")
        f.write(f"- CR: {s.get('cr', 'N/A')}\n")
        f.write(f"- pass: {s.get('pass', 'N/A')}\n\n")

    if "emergence" in results:
        f.write("### Emergencia\n")
        e = results["emergence"]
        for key, val in e.items():
            if isinstance(val, float):
                f.write(f"- {key}: {val:.4f}\n")
            else:
                f.write(f"- {key}: {val}\n")
        f.write("\n")
