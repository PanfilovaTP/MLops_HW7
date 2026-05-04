from math import ceil, sqrt

# План A/B-теста для сравнения текущей модели v1.0.0 и новой модели v1.1.0.
# Основная метрика: доля корректных предсказаний после получения разметки/факта.
# H0: качество v1.1.0 не выше качества v1.0.0.
# H1: качество v1.1.0 выше качества v1.0.0 минимум на MDE.

alpha = 0.05
power = 0.80
baseline_accuracy = 0.90
mde = 0.03
new_accuracy = baseline_accuracy + mde

# Нормальная аппроксимация для двух независимых долей.
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
print("План A/B-теста")
print(f"alpha = {alpha}")
print(f"power = {power}")
print(f"baseline accuracy = {baseline_accuracy:.2f}")
print(f"MDE = {mde:.2f}")
print(f"Размер выборки на группу: {n_per_group}")
print(f"Общий размер выборки: {2 * n_per_group}")
print("Правило решения: выкатывать v1.1.0 на 100%, если метрика статистически значимо выше и нет роста ошибок /predict и /health.")
