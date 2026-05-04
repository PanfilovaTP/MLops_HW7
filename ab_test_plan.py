from math import ceil, sqrt

import pandas as pd


alpha = 0.05
power = 0.80

baseline_accuracy = 0.90
mde = 0.05
new_accuracy = baseline_accuracy + mde

z_alpha_2 = 1.96
z_beta = 0.84

p_pool = (baseline_accuracy + new_accuracy) / 2

n_per_group = (
    (
        z_alpha_2 * sqrt(2 * p_pool * (1 - p_pool))
        + z_beta
        * sqrt(
            baseline_accuracy * (1 - baseline_accuracy)
            + new_accuracy * (1 - new_accuracy)
        )
    )
    ** 2
    / (new_accuracy - baseline_accuracy) ** 2
)

n_per_group = ceil(n_per_group)

ab_test_plan = pd.DataFrame(
    {
        "Параметр": [
            "Контрольная версия",
            "Тестовая версия",
            "Основная метрика",
            "alpha",
            "power",
            "baseline accuracy",
            "MDE",
            "Размер выборки на группу",
            "Общий размер выборки",
            "Начальное распределение трафика",
        ],
        "Значение": [
            "v1.0.0",
            "v1.1.0",
            "доля корректных предсказаний",
            alpha,
            power,
            baseline_accuracy,
            mde,
            n_per_group,
            2 * n_per_group,
            "90/10",
        ],
    }
)

print(ab_test_plan.to_string(index=False))