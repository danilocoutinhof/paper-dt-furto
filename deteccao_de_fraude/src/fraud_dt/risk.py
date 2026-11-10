from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.inspection import permutation_importance
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score, roc_auc_score, roc_curve
from sklearn.neural_network import MLPClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


FEATURE_COLUMNS = [
    "relative_divergence",
    "rolling_divergence_mean",
    "rolling_divergence_max",
    "slot_recurrence",
    "alarm_score",
    "operational_penalty",
    "hour",
    "day_of_week",
]


def score_rule_based_risk(df: pd.DataFrame) -> pd.DataFrame:
    score = np.zeros(len(df), dtype=float)
    score += (df["relative_divergence"] > 0.08).astype(float) * 0.35
    score += (df["rolling_divergence_mean"] > 0.06).astype(float) * 0.20
    score += (df["rolling_divergence_max"] > 0.12).astype(float) * 0.10
    score += (df["slot_recurrence"] > 0.25).astype(float) * 0.15
    score += (df["alarm_out_of_bounds_power"] > 0).astype(float) * 0.10
    score += (df["alarm_overcurrent"] > 0).astype(float) * 0.05
    score += (df["operational_penalty"] > 0).astype(float) * 0.05

    df = df.copy()
    df["risk_probability"] = np.clip(score, 0.0, 0.99)
    df["risk_class"] = pd.cut(
        df["risk_probability"],
        bins=[-0.01, 0.30, 0.60, 1.0],
        labels=["low", "moderate", "high"],
    ).astype(str)
    return df


def train_supervised_baseline(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    if "theft_active" not in df.columns:
        raise ValueError("Expected theft_active column for supervised baseline.")

    model_df = df.copy()
    split_index = max(int(len(model_df) * 0.7), 1)
    train_df = model_df.iloc[:split_index].copy()
    test_df = model_df.iloc[split_index:].copy()
    if test_df.empty:
        test_df = train_df.copy()

    if train_df["theft_active"].nunique() < 2:
        positive_class = int(train_df["theft_active"].iloc[0])
        constant_probability = float(positive_class)
        model_df["supervised_probability"] = constant_probability
        model_df["supervised_prediction"] = positive_class
        metrics = pd.DataFrame(
            [
                {
                    "model": "constant_baseline_single_class",
                    "accuracy": accuracy_score(test_df["theft_active"], np.full(len(test_df), positive_class)),
                    "precision": precision_score(test_df["theft_active"], np.full(len(test_df), positive_class), zero_division=0),
                    "recall": recall_score(test_df["theft_active"], np.full(len(test_df), positive_class), zero_division=0),
                    "f1": f1_score(test_df["theft_active"], np.full(len(test_df), positive_class), zero_division=0),
                    "roc_auc": np.nan,
                    "train_samples": len(train_df),
                    "test_samples": len(test_df),
                }
            ]
        )
        return model_df, metrics

    preprocessor = ColumnTransformer(
        transformers=[("num", StandardScaler(), FEATURE_COLUMNS)],
        remainder="drop",
    )
    model = Pipeline(
        steps=[
            ("preprocessor", preprocessor),
            ("classifier", LogisticRegression(max_iter=1000, class_weight="balanced")),
        ]
    )

    model.fit(train_df[FEATURE_COLUMNS], train_df["theft_active"])
    model_df["supervised_probability"] = model.predict_proba(model_df[FEATURE_COLUMNS])[:, 1]
    model_df["supervised_prediction"] = (model_df["supervised_probability"] >= 0.50).astype(int)

    test_predictions = model.predict(test_df[FEATURE_COLUMNS])
    test_probabilities = model.predict_proba(test_df[FEATURE_COLUMNS])[:, 1]
    metrics = pd.DataFrame(
        [
            {
                "model": "logistic_regression",
                "accuracy": accuracy_score(test_df["theft_active"], test_predictions),
                "precision": precision_score(test_df["theft_active"], test_predictions, zero_division=0),
                "recall": recall_score(test_df["theft_active"], test_predictions, zero_division=0),
                "f1": f1_score(test_df["theft_active"], test_predictions, zero_division=0),
                "roc_auc": roc_auc_score(test_df["theft_active"], test_probabilities),
                "train_samples": len(train_df),
                "test_samples": len(test_df),
            }
        ]
    )
    return model_df, metrics


def compute_model_comparison_and_importance(
    df: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Reporting-only analysis requested during peer review (feature
    importance, a deeper model as an alternative to logistic regression, and
    explicit ROC curves/AUROC). This function is intentionally separate from
    `train_supervised_baseline`: it does not feed the twin's decision loop
    (which keeps using the logistic-regression `supervised_probability` for
    reproducibility of the closed-loop behavior already validated by the
    existing test suite) and is used purely to produce comparison artifacts
    for the manuscript.

    Returns (model_comparison_df, feature_importance_df, roc_curve_df). All
    three are empty when the scenario has a single class in the training
    split (e.g. `persistent_theft`, `normal`), since neither a second model
    nor an ROC curve is meaningful in that degenerate case.
    """
    if "theft_active" not in df.columns:
        raise ValueError("Expected theft_active column.")

    split_index = max(int(len(df) * 0.7), 1)
    train_df = df.iloc[:split_index].copy()
    test_df = df.iloc[split_index:].copy()
    if test_df.empty:
        test_df = train_df.copy()

    if train_df["theft_active"].nunique() < 2:
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

    scaler = StandardScaler()
    x_train = scaler.fit_transform(train_df[FEATURE_COLUMNS])
    x_test = scaler.transform(test_df[FEATURE_COLUMNS])
    y_train = train_df["theft_active"].to_numpy()
    y_test = test_df["theft_active"].to_numpy()

    logistic_model = LogisticRegression(max_iter=1000, class_weight="balanced")
    logistic_model.fit(x_train, y_train)
    logistic_test_probabilities = logistic_model.predict_proba(x_test)[:, 1]
    logistic_test_predictions = (logistic_test_probabilities >= 0.50).astype(int)

    # A small multi-layer perceptron (two hidden layers) is used as a higher-
    # capacity alternative requested by reviewers, to check whether added
    # model capacity meaningfully changes detection performance once the
    # circular divergence-vs-label construction has been removed from the
    # data-generation process.
    mlp_model = MLPClassifier(
        hidden_layer_sizes=(16, 8),
        activation="relu",
        max_iter=2000,
        random_state=42,
    )
    mlp_model.fit(x_train, y_train)
    mlp_test_probabilities = mlp_model.predict_proba(x_test)[:, 1]
    mlp_test_predictions = (mlp_test_probabilities >= 0.50).astype(int)

    def _metrics_row(model_name: str, predictions: np.ndarray, probabilities: np.ndarray) -> dict:
        return {
            "model": model_name,
            "accuracy": accuracy_score(y_test, predictions),
            "precision": precision_score(y_test, predictions, zero_division=0),
            "recall": recall_score(y_test, predictions, zero_division=0),
            "f1": f1_score(y_test, predictions, zero_division=0),
            "roc_auc": roc_auc_score(y_test, probabilities),
            "train_samples": len(train_df),
            "test_samples": len(test_df),
        }

    model_comparison = pd.DataFrame(
        [
            _metrics_row("logistic_regression", logistic_test_predictions, logistic_test_probabilities),
            _metrics_row("mlp_2_hidden_layers", mlp_test_predictions, mlp_test_probabilities),
        ]
    )

    standardized_coefficients = logistic_model.coef_[0]
    permutation_result = permutation_importance(
        logistic_model, x_test, y_test, n_repeats=20, random_state=42, scoring="f1"
    )
    feature_importance = pd.DataFrame(
        {
            "feature": FEATURE_COLUMNS,
            "logistic_standardized_coefficient": standardized_coefficients,
            "permutation_importance_mean": permutation_result.importances_mean,
            "permutation_importance_std": permutation_result.importances_std,
        }
    ).sort_values("permutation_importance_mean", ascending=False)

    fpr, tpr, thresholds = roc_curve(y_test, logistic_test_probabilities)
    roc_curve_df = pd.DataFrame(
        {
            "model": "logistic_regression",
            "false_positive_rate": fpr,
            "true_positive_rate": tpr,
            "threshold": thresholds,
        }
    )
    mlp_fpr, mlp_tpr, mlp_thresholds = roc_curve(y_test, mlp_test_probabilities)
    roc_curve_df = pd.concat(
        [
            roc_curve_df,
            pd.DataFrame(
                {
                    "model": "mlp_2_hidden_layers",
                    "false_positive_rate": mlp_fpr,
                    "true_positive_rate": mlp_tpr,
                    "threshold": mlp_thresholds,
                }
            ),
        ],
        ignore_index=True,
    )

    return model_comparison, feature_importance, roc_curve_df


# --- Revalidation protocol (E1+): one model across scenarios, frozen ----------


def score_rule_based_record(record: dict) -> float:
    """Single-sample version of `score_rule_based_risk` (same rules and
    weights), used when features are recomputed online inside the closed
    loop (revalidation stage E4)."""
    score = 0.0
    score += 0.35 if record["relative_divergence"] > 0.08 else 0.0
    score += 0.20 if record["rolling_divergence_mean"] > 0.06 else 0.0
    score += 0.10 if record["rolling_divergence_max"] > 0.12 else 0.0
    score += 0.15 if record["slot_recurrence"] > 0.25 else 0.0
    score += 0.10 if record["alarm_out_of_bounds_power"] > 0 else 0.0
    score += 0.05 if record["alarm_overcurrent"] > 0 else 0.0
    score += 0.05 if record["operational_penalty"] > 0 else 0.0
    return float(min(max(score, 0.0), 0.99))


class FrozenSupervisedModel:
    """Logistic regression trained once on pooled training realizations of
    all scenarios and then frozen (revalidation stage E1 onward).

    This replaces the per-scenario chronological split of v1, in which the
    model was refitted inside every scenario (and degenerated into a
    constant predictor whenever the scenario's training split had a single
    class). The frozen model is applied to unseen test realizations only.
    """

    def __init__(self) -> None:
        self.pipeline: Pipeline | None = None
        self._mean: np.ndarray | None = None
        self._scale: np.ndarray | None = None
        self._coef: np.ndarray | None = None
        self._intercept: float = 0.0
        self.train_samples: int = 0
        self.train_positive_rate: float = 0.0

    def fit(self, train_df: pd.DataFrame) -> "FrozenSupervisedModel":
        if train_df["theft_active"].nunique() < 2:
            raise ValueError("Pooled training data must contain both classes.")
        preprocessor = ColumnTransformer(
            transformers=[("num", StandardScaler(), FEATURE_COLUMNS)],
            remainder="drop",
        )
        self.pipeline = Pipeline(
            steps=[
                ("preprocessor", preprocessor),
                ("classifier", LogisticRegression(max_iter=1000, class_weight="balanced")),
            ]
        )
        self.pipeline.fit(train_df[FEATURE_COLUMNS], train_df["theft_active"])
        scaler = self.pipeline.named_steps["preprocessor"].named_transformers_["num"]
        classifier = self.pipeline.named_steps["classifier"]
        self._mean = scaler.mean_.astype(float)
        self._scale = scaler.scale_.astype(float)
        self._coef = classifier.coef_[0].astype(float)
        self._intercept = float(classifier.intercept_[0])
        self.train_samples = int(len(train_df))
        self.train_positive_rate = float(train_df["theft_active"].mean())
        return self

    def predict_proba(self, df: pd.DataFrame) -> np.ndarray:
        x = df[FEATURE_COLUMNS].to_numpy(dtype=float)
        z = ((x - self._mean) / self._scale) @ self._coef + self._intercept
        return 1.0 / (1.0 + np.exp(-z))

    def predict_record(self, record: dict) -> float:
        x = np.array([float(record[c]) for c in FEATURE_COLUMNS])
        z = float(((x - self._mean) / self._scale) @ self._coef + self._intercept)
        return float(1.0 / (1.0 + np.exp(-z)))

    def apply(self, df: pd.DataFrame) -> pd.DataFrame:
        out = df.copy()
        out["supervised_probability"] = self.predict_proba(out)
        out["supervised_prediction"] = (out["supervised_probability"] >= 0.50).astype(int)
        return out
