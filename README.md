# 💶 Finance Flow

Веб-сервис для контроля, учёта и управления личными финансами пользователя.

---

# Требования

Перед запуском убедитесь, что установлены:

- Docker Desktop (Windows/macOS) или Docker Engine (Linux)
- Docker Compose

Проверить установку:

```shell
docker --version
docker compose version
```

---

# Клонирование проекта

```shell
git clone https://github.com/TolstenkovAnton/FinanceFlow.git
cd FinanceFlow
```

---

# Создание файла окружения

Создайте файл .env на основе шаблона .env.example

---

# Генерация JWT-ключей

Для подписи JWT используются RSA-ключи.
Создайте директорию app/certificates. Перейдите в директорию.

Создайте приватный RSA (RS256) ключ.
```shell
openssl genrsa -out jwt-private.pem 2048
```
Создайте публичный ключ в пару к приватному для сертификата.
```shell
openssl rsa -in jwt-private.pem -outform PEM -pubout -out jwt-public.pem
```

Скопируйте ключи в переменные окружения.

---

# Запуск приложения

Из корневой директории выполните:

```shell
docker compose up --build
```
После успешного запуска приложение будет доступно по адресу http://localhost:8000.

Запуск уже собранного образа.
```shell
docker compose up
```

---

# Остановка приложения

```shell
docker compose down
```