# FoolGame mini-app

_Full-stack реализация карточной игры "Дурак" с real-time мультиплеером на FastAPI и React._

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![Pydantic](https://img.shields.io/badge/Pydantic-E92063?style=for-the-badge&logo=pydantic&logoColor=white)
![WebSocket](https://img.shields.io/badge/WebSocket-010101?style=for-the-badge&logo=websocket&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)
![Redis](https://img.shields.io/badge/Redis-DC382D?style=for-the-badge&logo=redis&logoColor=white)
![RabbitMQ](https://img.shields.io/badge/RabbitMQ-FF6600?style=for-the-badge&logo=rabbitmq&logoColor=white)
![Dishka](https://img.shields.io/badge/Dishka-4B32C3?style=for-the-badge&logoColor=white)
![msgspec](https://img.shields.io/badge/msgspec-00ADD8?style=for-the-badge&logoColor=white)
![Pytest](https://img.shields.io/badge/Pytest-0A9EDC?style=for-the-badge&logo=pytest&logoColor=white)
![React](https://img.shields.io/badge/React-20232A?style=for-the-badge&logo=react&logoColor=61DAFB)
![JavaScript](https://img.shields.io/badge/JavaScript-F7DF1E?style=for-the-badge&logo=javascript&logoColor=black)
![CSS3](https://img.shields.io/badge/CSS3-1572B6?style=for-the-badge&logo=css3&logoColor=white)

## Демонстрация

<table>
  <tr>
    <td align="center"><strong>Defend Gameplay</strong></td>
    <td align="center"><strong>Attack gameplay</strong></td>
  </tr>
  <tr>
    <td><img src="./gameplay/defend.gif" alt="Defend Gameplay" width="400"></td>
    <td><img src="./gameplay/attack.gif" alt="Attack gameplay" width="400"></td>
  </tr>
</table>
<table>
  <tr>
    <td align="center"><strong>Benchmark</strong></td>
  </tr>
  <tr>
    <td><img src="./gameplay/benchmark.gif" alt="Benchmark" width="800"></td>
  </tr>
</table>

## О проекте

Этот проект — это, в первую очередь, исследование принципов разработки backend-приложений для real-time игр.

Основной фокус проекта — архитектура бэкенда на **FastAPI**, где реализованы:

- **Управление WebSocket-соединениями** для множества игроков в рамках одной игровой комнаты.
- **Машина состояний (State Machine)**, управляющая логикой игры (ходы, защита, пас, конец раунда).
- **Четко определенный протокол обмена сообщениями** между клиентом и сервером и **State Machine**.

Фронтенд на React выступает в роли клента, который полностью раскрывает и тестирует возможности бэкенда.

## Ключевые архитектурные решения

### Backend

- **Централизованный Connection Manager**
  Для управления жизненным циклом WebSocket-соединений используется единый менеджер, который отвечает за подключение, отключение и рассылку сообщений игрокам в рамках одной игровой комнаты.

- **Паттерн "Заместитель" (Proxy) для управления состоянием игры**
  Для разделения логики управления игрой на различных этапах используется паттерн "Заместитель". Это позволяет инкапсулировать внутреннюю работу игры, упростить обработку входящих команд от пользователей и обеспечить единый интерфейс для управления всеми игровыми состояниями.
- **Четкий Протокол Обмена Данными**
  Все сообщения между клиентом и сервером следуют строго определенному формату с полями `"type"` и `"data"`.(тип действия, новые данные). Это позволяет выстроить единый стиль обраотки сообщений по websocket.

## Установка и Запуск

### Запуск через Docker (Рекомендуемый способ)

- `git clone https://github.com/IlyaTakhtay/Fool_game_for_tg/`
- `cd Fool_game_for_tg`
- `cd backend`
- `docker-compose -f docker-compose.infra.yml up -d --build`
- `docker-compose -f docker-compose.dev.yml up -d --build`

### Локальный запуск backend инстанса (Без Docker)

Backend: `cd backend/requirements`, `pip install -r requirements-dev.txt`, `cd ..`, `uvicorn src.main:app --reload`
Frontend: `cd frontend`, `npm install`, `npm start`

## Project objectives

- [x] Redis.
- [x] Make backend instace without storing any game data.
- [/] Optimize size of data transfer objects (partially done).
- [ ] Implement Authorization to a guest user.
- [ ] Implement Tossing cards from others.
- [ ] Test coverage 80%.
- [ ] CI/CD.
- [/] Benchmark and profiling weak points (partially done).
- [ ] Implement game room settings.
- [ ] Player Statistics.
- [ ] Switch to incremental update communication model.
- [ ] Make as telegramm mini-app.
