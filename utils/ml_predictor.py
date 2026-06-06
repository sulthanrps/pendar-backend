import os
import json
import numpy as np
import pandas as pd
import joblib

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_DIR = os.path.join(BASE_DIR, 'ml_models')

MODEL_PATH = os.path.join(MODEL_DIR, "tuned_xgboost_model.pkl")
MM_SCALER_PATH = os.path.join(MODEL_DIR, "mm_scaler.pkl")
STD_SCALER_PATH = os.path.join(MODEL_DIR, "std_scaler.pkl")
META_PATH = os.path.join(MODEL_DIR, "pipeline_meta.json")

BURNOUT_THRESHOLD_PCT = 70

class MindCheckPredictor:
    """
    Singleton-friendly wrapper. Instantiate sekali di level modul Flask,
    bukan per-request, agar model tidak di-reload berulang kali.
    """
 
    def __init__(
        self,
        model_path: str = MODEL_PATH,
        mm_scaler_path: str = MM_SCALER_PATH,
        std_scaler_path: str = STD_SCALER_PATH,
        meta_path: str = META_PATH,
    ):
        self.model = joblib.load(model_path)
        self.mm_scaler = joblib.load(mm_scaler_path)
        self.std_scaler = joblib.load(std_scaler_path)
 
        with open(meta_path, "r") as f:
            meta = json.load(f)
 
        self.minmax_cols: list[str] = meta["minmax_cols"]
        self.standard_cols: list[str] = meta["standard_cols"]
        self.sleep_thresh: float = meta["sleep_thresh"]
        self.feature_order: list[str] = meta["feature_order"]
        self.burnout_score_min: float = meta["burnout_score_min"]
        self.burnout_score_max: float = meta["burnout_score_max"]
 
    # ── Public API ─────────────────────────────────────────────────────────────
 
    def predict(self, raw_input: dict) -> dict:
        """
        Terima raw input dari Flutter, kembalikan output persentase.
 
        Parameters
        ----------
        raw_input : dict
            Kunci yang diharapkan:
                mental_health_index  (int, 0–2)
                depression_score     (int)
                anxiety_score        (int)
                stress_score         (int)
                sleep_hours          (int)
                study_hours          (int)
 
        Returns
        -------
        dict
            {
                "focus_level_pct":   int (0–100),
                "burnout_level_pct": int (0–100),
                "is_burnout":        bool
            }
 
        Raises
        ------
        ValueError
            Jika ada field wajib yang tidak ada di raw_input.
        """
        self._validate_input(raw_input)
 
        df = self._build_features(raw_input)
        df = self._apply_scaling(df)
        df = self._enforce_feature_order(df)
 
        burnout_score_raw = float(self.model.predict(df)[0])
 
        burnout_pct = self._to_percent(
            burnout_score_raw, self.burnout_score_min, self.burnout_score_max
        )
        focus_pct = self._burnout_to_focus(burnout_pct, raw_input)
 
        is_burnout = burnout_pct >= BURNOUT_THRESHOLD_PCT
 
        return {
            "focus_level_pct": focus_pct,
            "burnout_level_pct": burnout_pct,
            "is_burnout": is_burnout,
        }
 
    # ── Internal Steps ─────────────────────────────────────────────────────────
 
    def _validate_input(self, raw: dict) -> None:
        required = {
            "mental_health_index",
            "depression_score",
            "anxiety_score",
            "stress_score",
            "sleep_hours",
            "study_hours",
        }
        missing = required - raw.keys()
        if missing:
            raise ValueError(f"Field wajib tidak ada: {missing}")
 
    def _build_features(self, raw: dict) -> pd.DataFrame:
        """
        Mereplikasi seluruh feature engineering dari notebook:
          - Rename field Flutter → nama kolom training
          - Derived features (mental_burden, ratio, index, dll.)
          - is_sleep_deprived (menggunakan sleep_thresh dari training)
        """
        # Map nama field Flutter ke nama kolom di dataset training
        # Sesuaikan mapping ini jika nama kolom di notebook berbeda
        base = {
            "stress_level":        raw["stress_score"],
            "anxiety_score":       raw["anxiety_score"],
            "depression_score":    raw["depression_score"],
            "sleep_hours":         raw["sleep_hours"],
            "study_hours_per_day": raw["study_hours"],
            # mental_health_index tidak ada di dataset asli —
            # kita jadikan fitur tambahan jika ada di feature_order,
            # atau abaikan jika tidak.
        }
 
        df = pd.DataFrame([base])
 
        # ── Derived features (harus identik dengan notebook) ──────────────────
        df["mental_burden"] = df["anxiety_score"] + df["depression_score"]
        df["anxiety_x_depression"] = df["anxiety_score"] * df["depression_score"]
        df["study_sleep_ratio"] = df["study_hours_per_day"] / (df["sleep_hours"] + 1e-5)
        df["mental_pressure_index"] = df[
            ["stress_level", "anxiety_score", "depression_score"]
        ].mean(axis=1)
 
        # ── is_sleep_deprived (gunakan threshold dari training, BUKAN recompute) ─
        df["is_sleep_deprived"] = (df["sleep_hours"] < self.sleep_thresh).astype(int)

        df["academic_performance"] = 0.0
        df["family_expectation"]   = 0.0
 
        # ── Tambahkan mental_health_index hanya jika ada di feature_order ───────
        if "mental_health_index" in self.feature_order:
            df["mental_health_index"] = raw["mental_health_index"]
 
        return df
 
    def _apply_scaling(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Terapkan MinMaxScaler dan StandardScaler ke kolom yang tepat,
        sesuai pembagian yang direkam di pipeline_meta.json.
        """
        df = df.copy()
 
        # Filter hanya kolom yang ada di DataFrame (hindari KeyError)
        mm_apply = [c for c in self.minmax_cols if c in df.columns]
        std_apply = [c for c in self.standard_cols if c in df.columns]
 
        if mm_apply:
            df[mm_apply] = self.mm_scaler.transform(df[mm_apply])
 
        if std_apply:
            df[std_apply] = self.std_scaler.transform(df[std_apply])
 
        return df
 
    def _enforce_feature_order(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Pastikan urutan kolom identik dengan saat training.
        Kolom yang tidak ada di feature_order akan dibuang;
        kolom yang hilang akan diisi 0 dengan peringatan.
        """
        missing_cols = set(self.feature_order) - set(df.columns)
        if missing_cols:
            import warnings
            warnings.warn(
                f"Kolom berikut tidak ada saat inference, diisi 0: {missing_cols}",
                RuntimeWarning,
                stacklevel=3,
            )
            for col in missing_cols:
                df[col] = 0.0
 
        return df[self.feature_order]
 
    # ── Konversi ke Persentase ─────────────────────────────────────────────────
 
    @staticmethod
    def _to_percent(value: float, v_min: float, v_max: float) -> int:
        """
        Normalisasi nilai regresi ke rentang 0–100%.
        Clamp agar prediksi di luar range training tidak overflow.
        """
        if v_max == v_min:
            return 50  # fallback jika range nol (data edge case)
        pct = (value - v_min) / (v_max - v_min) * 100
        return int(np.clip(round(pct), 0, 100))
 
    @staticmethod
    def _burnout_to_focus(burnout_pct: int, raw: dict) -> int:
        """
        Hitung focus_level_pct dari burnout dan faktor pendukung lain.
 
        Logika:
          - Base focus adalah invers burnout (fokus turun saat burnout naik)
          - Bonus kecil untuk tidur cukup (>= 7 jam)
          - Penalti untuk mental_health_index tinggi (≥ 2 = kondisi buruk)
 
        Sesuaikan bobot ini dengan domain knowledge atau eksperimen lebih lanjut.
        """
        base_focus = 100 - burnout_pct
 
        sleep_bonus = 5 if raw.get("sleep_hours", 0) >= 7 else 0
        mhi_penalty = 10 if raw.get("mental_health_index", 0) >= 2 else 0
 
        focus = base_focus + sleep_bonus - mhi_penalty
        return int(np.clip(focus, 0, 100))