# HW7. Сборка конвейера CI/CD для ML-сервиса

## 1. Описание проекта

Проект демонстрирует CI/CD-конвейер для ML-сервиса и безопасное развертывание новой версии модели. В качестве сервиса используется FastAPI-приложение, которое обучает простую модель `RandomForestClassifier` на датасете Iris и предоставляет два endpoint:

- `GET /health` — проверка состояния сервиса и версии модели;
- `POST /predict` — получение предсказания модели.

В проекте используются две версии ML-сервиса:

- `v1.0.0` — стабильная версия;
- `v1.1.0` — новая версия, которая выкатывается через Canary Deployment.

## 2. Структура проекта

```text
.
├── app/
│   └── main.py
├── doc/architecture/decisions/
│   └── 0001-use-canary-deployment-for-ml-service.md
├── nginx/
│   ├── canary-90-10.conf
│   ├── canary-50-50.conf
│   ├── canary-100.conf
│   ├── rollback.conf
│   └── current.conf
├── scripts/
│   ├── check_endpoints.sh
│   └── switch_canary.sh
├── tests/
│   └── test_app.py
├── .github/workflows/
│   ├── ci.yml
│   └── deploy.yml
├── .gitlab-ci.yml
├── Dockerfile
├── docker-compose.canary.yml
├── docker-compose.blue.yml
├── docker-compose.green.yml
├── ml_pipeline.py
├── ab_test_plan.py
├── requirements.txt
└── README.md
```

## 3. GitLab CI/CD

В файле `.gitlab-ci.yml` настроены три стадии:

1. `reproducibility` — фиксируются зависимости, seed, параметры модели и метрики;
2. `test` — запускаются unit-тесты;
3. `package` — проверяется наличие файлов для деплоя.

Ключевой шаг воспроизводимости:

```yaml
make_pipeline_reproducible:
  stage: reproducibility
  script:
    - echo "Фиксируем зависимости, seed, параметры модели и метрики."
    - pip freeze | tee requirements.lock.txt
    - python ml_pipeline.py
    - cat artifacts/metrics.json
  artifacts:
    when: always
    paths:
      - requirements.lock.txt
      - artifacts/metrics.json
    expire_in: 1 week
```

Ссылка на выполненный GitLab pipeline:

```text
ВСТАВИТЬ_ССЫЛКУ_НА_GITLAB_PIPELINE
```

## 4. Обоснование стратегии деплоя

Выбрана стратегия **Canary Deployment**.

Причина выбора: в коде ML-сервиса нет полноценной обработки всех возможных ошибок, поэтому нельзя сразу отдавать 100% трафика новой версии. Canary снижает риск: сначала новая версия `v1.1.0` получает только 10% трафика, а стабильная `v1.0.0` продолжает обслуживать 90% запросов.

Сравнение альтернатив:

| Стратегия | Плюсы | Минусы | Риск |
|---|---|---|---|
| Blue-Green | Простая проверка двух окружений, быстрый откат | При переключении новая версия может сразу получить 100% трафика | Средний |
| Canary | Новая версия получает малую долю трафика, можно постепенно увеличивать нагрузку | Нужны балансировщик и контроль метрик | Низкий |
| Rolling | Экономит ресурсы, постепенно заменяет инстансы | Сложнее сравнивать две версии ML-модели | Средний |
| Shadow | Новая версия не влияет на пользователя | Требует зеркалирования запросов и сложнее в реализации | Низкий для пользователей, высокий по сложности |

ADR-файл находится здесь:

```text
doc/architecture/decisions/0001-use-canary-deployment-for-ml-service.md
```

## 5. Локальный запуск Canary Deployment

Запуск двух версий сервиса и Nginx-балансировщика:

```bash
docker compose -f docker-compose.canary.yml up --build
```

После запуска доступны endpoint:

```bash
curl http://localhost:8001/health
curl http://localhost:8002/health
curl http://localhost:8080/health
```

Ожидаемые ответы для прямой проверки версий:

```json
{"status":"ok","version":"v1.0.0"}
```

```json
{"status":"ok","version":"v1.1.0"}
```

Проверка предсказания через балансировщик:

```bash
curl -X POST http://localhost:8080/predict \
  -H "Content-Type: application/json" \
  -d '{"x": [1,2,3]}'
```

Пример ответа:

```json
{
  "status": "ok",
  "version": "v1.1.0",
  "prediction": 1,
  "class_name": "versicolor",
  "probabilities": [0.0, 0.8, 0.2],
  "features_used": [1.0, 2.0, 3.0, 0.0]
}
```

## 6. Переключение трафика и rollback

Изначально используется схема 90/10:

```text
v1.0.0 — 90%
v1.1.0 — 10%
```

Увеличить долю новой версии до 50%:

```bash
./scripts/switch_canary.sh 50-50
```

Переключить 100% трафика на новую версию:

```bash
./scripts/switch_canary.sh 100
```

Вернуть 100% трафика на старую версию при ошибках:

```bash
./scripts/switch_canary.sh rollback
```

Для быстрой проверки всех endpoint можно использовать:

```bash
./scripts/check_endpoints.sh
```

## 7. План A/B-тестирования ML-модели

Цель A/B-теста — проверить, улучшает ли новая версия модели `v1.1.0` качество по сравнению с `v1.0.0`.

Параметры эксперимента:

- контрольная группа: `v1.0.0`;
- тестовая группа: `v1.1.0`;
- основная метрика: доля корректных предсказаний после получения фактической разметки;
- guardrail-метрики: доля ошибок `/predict`, доля ошибок `/health`, задержка ответа;
- `alpha = 0.05`;
- мощность теста `power = 0.80`;
- базовое качество `baseline accuracy = 0.90`;
- минимальный детектируемый эффект `MDE = 0.03`.

Расчет размера выборки находится в файле:

```text
ab_test_plan.py
```

Запуск:

```bash
python ab_test_plan.py
```

Правило решения: выкатывать `v1.1.0` на 100%, если качество статистически значимо выше, а guardrail-метрики не ухудшились. Если качество не улучшилось или выросла доля ошибок, выполняется rollback на `v1.0.0`.

## 8. GitHub Actions

Файл деплоя находится здесь:

```text
.github/workflows/deploy.yml
```

Workflow выполняет следующие шаги:

1. забирает код из репозитория;
2. собирает Docker image;
3. запускает smoke-test `/health` и `/predict`;
4. логинится в GitHub Container Registry;
5. публикует Docker image в GHCR;
6. вызывает API деплоя, если задан `CLOUD_TOKEN`.

В GitHub Secrets нужно добавить:

```text
CLOUD_TOKEN
MODEL_VERSION
```

Ссылка на выполненный GitHub Actions pipeline:

```text
ВСТАВИТЬ_ССЫЛКУ_НА_GITHUB_ACTIONS
```

## 9. Скриншоты для сдачи

Для финальной сдачи нужно приложить скриншоты:

1. успешный GitLab Pipeline;
2. успешный GitHub Actions workflow;
3. результат команды `curl http://localhost:8001/health`;
4. результат команды `curl http://localhost:8002/health`;
5. результат команды `curl http://localhost:8080/health`;
6. результат команды `curl -X POST http://localhost:8080/predict -H "Content-Type: application/json" -d '{"x": [1,2,3]}'`;
7. переключение Canary на `50-50`, `100` или `rollback`.

Скриншоты можно положить в папку:

```text
screenshots/
```

## 10. Итоговые выводы

В этом домашнем задании был собран минимальный CI/CD-конвейер для ML-сервиса. Самой простой частью оказалась упаковка FastAPI-сервиса в Docker, потому что приложение небольшое и имеет понятные endpoint `/health` и `/predict`. Более сложной частью стала стратегия деплоя: для ML-модели важно проверять не только техническую доступность сервиса, но и качество ответов новой версии. Из-за отсутствия полноценной обработки ошибок была выбрана стратегия Canary Deployment, так как она снижает риск массового отказа. Новая версия сначала получает только небольшую долю трафика, после чего ее можно постепенно довести до 100%. Если новая версия работает нестабильно, Nginx быстро переключает весь трафик обратно на `v1.0.0`. GitLab CI используется для проверки воспроизводимости ML-пайплайна, а GitHub Actions — для сборки Docker-образа и деплоя. Такой подход применим в реальных проектах, потому что он соединяет тестирование, контроль версий модели, безопасный rollout и rollback.
