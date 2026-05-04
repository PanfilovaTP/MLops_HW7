# HW7. CI/CD-конвейер для ML-сервиса

Проект для домашнего задания №7 по теме CI/CD и безопасного развертывания ML-сервиса.

В проекте реализован небольшой ML-сервис на FastAPI с двумя эндпоинтами:

- GET /health — проверка статуса сервиса и версии модели;
- POST /predict — получение предсказания модели.

Для безопасного выкатывания новой версии используется Canary Deployment: старая версия сервиса v1.0.0 и новая версия v1.1.0 запускаются параллельно, а Nginx распределяет между ними трафик.

## Репозитории

Основной GitHub-репозиторий:

https://github.com/PanfilovaTP/MLops_HW7

GitVerse-репозиторий, использованный как аналог GitLab:

https://gitverse.ru/TatianaPanfilova/MLops_HW7

Успешный CI/CD-пайплайн GitVerse:

https://gitverse.ru/TatianaPanfilova/MLops_HW7/cicd/4

GitHub Actions:

https://github.com/PanfilovaTP/MLops_HW7/actions

GitLab-проект был создан, но запуск GitLab CI/CD на GitLab.com оказался недоступен из-за требования identity verification. Поэтому для выполнения условия «GitLab или аналог» был использован GitVerse.

## Структура проекта

```text
.
├── app/
│   └── main.py
├── artifacts/
│   └── metrics.json
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
│   ├── conftest.py
│   └── test_app.py
├── .github/workflows/
│   ├── ci.yml
│   └── deploy.yml
├── .gitverse/workflows/
│   └── ci.yml
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

## Основные файлы

- app/main.py — FastAPI-сервис с ручками /health и /predict;
- ml_pipeline.py — воспроизводимый ML-пайплайн на датасете Iris;
- Dockerfile — сборка Docker-образа сервиса;
- docker-compose.canary.yml — запуск двух версий сервиса и Nginx;
- nginx/ — конфигурации Nginx для режимов 90/10, 50/50, 100% и rollback;
- scripts/switch_canary.sh — переключение трафика между версиями;
- tests/ — unit-тесты для /health и /predict;
- ab_test_plan.py — расчет параметров A/B-теста;
- doc/architecture/decisions/ — ADR-файл с выбором стратегии деплоя;
- .gitverse/workflows/ci.yml — CI/CD workflow для GitVerse;
- .github/workflows/ci.yml — CI workflow для GitHub Actions;
- .github/workflows/deploy.yml — шаблон workflow для сборки Docker-образа и деплоя.

## Локальный запуск ML-пайплайна

```bash
python ml_pipeline.py
```

Ожидаемый результат:

```text
Точность accuracy: 0.90
Метрики сохранены в artifacts/metrics.json
```

## Локальный запуск сервиса

Запуск Canary Deployment:

```bash
docker compose -f docker-compose.canary.yml up --build
```

После запуска доступны:

```bash
curl http://127.0.0.1:8001/health
curl http://127.0.0.1:8002/health
curl http://127.0.0.1:18080/health
```

Порты:

- 8001 — версия v1.0.0;
- 8002 — версия v1.1.0;
- 18080 — Nginx-балансировщик.

Проверка /predict через балансировщик:

```bash
Invoke-RestMethod -Uri "http://127.0.0.1:18080/predict" `
  -Method Post `
  -ContentType "application/json" `
  -Body '{"x":[1,2,3]}' | ConvertTo-Json -Depth 5
```

Для PowerShell на Windows:

```powershell
curl.exe --% -X POST http://127.0.0.1:18080/predict -H "Content-Type: application/json" -d "{"x":[1,2,3]}"
```

## Canary Deployment

В проекте подготовлены конфигурации Nginx:

- nginx/canary-90-10.conf — 90% трафика на v1.0.0 и 10% на v1.1.0;
- nginx/canary-50-50.conf — равное распределение трафика;
- nginx/canary-100.conf — 100% трафика на v1.1.0;
- nginx/rollback.conf — возврат 100% трафика на v1.0.0.

Переключение режима:

```bash
./scripts/switch_canary.sh 90-10
./scripts/switch_canary.sh 50-50
./scripts/switch_canary.sh 100
./scripts/switch_canary.sh rollback
```

На Windows режим можно переключить вручную: заменить nginx/current.conf нужной конфигурацией из папки nginx и перезапустить контейнер Nginx.

## Выбранная стратегия деплоя

Для проекта выбрана стратегия Canary Deployment.

Причина выбора: новая версия ML-сервиса не должна сразу получать весь трафик, так как в условии задания указано отсутствие полноценной обработки ошибок. Canary Deployment позволяет сначала направить на новую версию небольшую долю запросов, проверить /health и /predict, а затем постепенно увеличивать долю трафика.

Если новая версия работает нестабильно, можно выполнить rollback на v1.0.0.

ADR-файл:

```text
doc/architecture/decisions/0001-use-canary-deployment-for-ml-service.md
```

## A/B-тестирование

План A/B-тестирования находится в файле:

```text
ab_test_plan.py
```

В тесте сравниваются:

- контрольная версия — v1.0.0;
- тестовая версия — v1.1.0.

Основная метрика — доля корректных предсказаний после получения фактической разметки.

Дополнительные метрики:

- ошибки /predict;
- статус /health;
- задержка ответа.

Запуск расчета:

```bash
python ab_test_plan.py
```

## CI/CD

### GitVerse

GitVerse использован как аналог GitLab для первого CI/CD-пайплайна.

Workflow:

```text
.gitverse/workflows/ci.yml
```

Он выполняет:

- установку зависимостей;
- запуск ml_pipeline.py;
- проверку artifacts/metrics.json;
- запуск unit-тестов;
- проверку файлов, необходимых для деплоя.

Успешный pipeline:

https://gitverse.ru/TatianaPanfilova/MLops_HW7/cicd/4

### GitHub Actions

Основной workflow GitHub Actions:

```text
.github/workflows/ci.yml
```

Он запускается при push в main и выполняет:

- установку Python 3.11;
- установку зависимостей из requirements.txt;
- запуск ml_pipeline.py;
- проверку artifacts/metrics.json;
- запуск pytest.

Также подготовлен файл:

```text
.github/workflows/deploy.yml
```

Это шаблон deploy workflow для сборки Docker-образа, публикации образа в GHCR и вызова API деплоя.

## Тесты

Локальный запуск тестов:

```bash
pytest -q
```

Ожидаемый результат:

```text
2 passed
```

## Итог

В проекте реализованы:

- CI/CD-пайплайн в GitVerse;
- CI workflow в GitHub Actions;
- Canary Deployment через Docker Compose и Nginx;
- rollback на стабильную версию;
- ADR-файл с выбором стратегии деплоя;
- план A/B-тестирования;
- ноутбук с пояснениями и скриншотами.
