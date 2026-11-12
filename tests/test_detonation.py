import pandas as pd
import pytest
import os
from pathlib import Path

# Находим путь к корню проекта (на одну папку выше папки tests)
BASE_DIR = Path(__file__).resolve().parent.parent
CSV_PATH = BASE_DIR / "data" / "explosives.csv"

@pytest.mark.parametrize("row", pd.read_csv(CSV_PATH).to_dict("records"))
def test_d_against_experiment(row):
    from core.detonation import kamlet_jacobs
    D, _ = kamlet_jacobs(row["rho_max"], row["Q_cal_g"], row["N"], row["M"])
    rel = abs(D - row["D_exp_km_s"]) / row["D_exp_km_s"]
    print(f'{row["name"]}: D_расч={D:.2f}, D_эксп={row["D_exp_km_s"]}, откл={rel*100:.1f}%')
    assert rel < 0.10