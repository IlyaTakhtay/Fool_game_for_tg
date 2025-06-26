# FoolGame mini-app
_Full-stack реализация карточной игры "Дурак" с real-time мультиплеером на FastAPI и React._

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi)
![Pydantic](https://img.shields.io/badge/Pydantic-E92063?style=for-the-badge&logo=pydantic)
![WebSocket](https://img.shields.io/badge/WebSocket-010101?style=for-the-badge&logo=websocket)
![CSS3](https://img.shields.io/badge/CSS3-1572B6?style=for-the-badge&logo=css3)
![JavaScript](https://img.shields.io/badge/JavaScript-F7DF1E?style=for-the-badge&logo=javascript)
![React](https://img.shields.io/badge/React-20232A?style=for-the-badge&logo=react&logoColor=61DAFB)

## Демонстрация
<table>
  <tr>
    <td align="center"><strong>Лобби и подключение к игре</strong></td>
    <td align="center"><strong>Игровой процесс</strong></td>
  </tr>
  <tr>
    <td><img src="https://raw.githubusercontent.com/IlyaTakhtay/Fool_game_for_tg/main/gameplay/defend.gif" alt="Defend Gameplay" width="400"></td>
    <td><img src="https://raw.githubusercontent.com/IlyaTakhtay/Fool_game_for_tg/main/gameplay/attack.gif" alt="Attack gameplay" width="400"></td>
  </tr>
</table>


## О проекте

Этот проект — это, в первую очередь, исследование принципов разработки backend-приложений для real-time игр.

Основной фокус проекта — архитектура бэкенда на **FastAPI**, где реализованы:
*   **Управление WebSocket-соединениями** для множества игроков в рамках одной игровой комнаты.
*   **Машина состояний (State Machine)**, управляющая логикой игры (ходы, защита, пас, конец раунда).
*   **Четко определенный протокол обмена сообщениями** между клиентом и сервером и **(State Machine)**.

Фронтенд на React выступает в роли клента, который полностью раскрывает и тестирует возможности бэкенда.

## Ключевые архитектурные решения

### Backend

*   **Централизованный Connection Manager**
    Для управления жизненным циклом WebSocket-соединений используется единый менеджер, который отвечает за подключение, отключение и рассылку сообщений игрокам в рамках одной игровой комнаты.

*   **Паттерн "Заместитель" (Proxy) для управления состоянием игры**
    Для разделения логики управления игрой на различных этапах используется паттерн "Заместитель". Это позволяет инкапсулировать внутреннюю работу игры, упростить обработку входящих команд от пользователей и обеспечить единый интерфейс для управления всеми игровыми состояниями.
    
*   **Четкий Протокол Обмена Данными**
    Все сообщения между клиентом и сервером следуют строго определенному формату с полями `"type"` и `"data"`.(тип действия, новые данные). Это позволяет выстроить единый стиль обраотки сообщений по websocket.
## Установка и Запуск
### Запуск через Docker (Рекомендуемый способ)
* `git clone https://github.com/IlyaTakhtay/Fool_game_for_tg/`
* `cd Fool_game_for_tg\backend`
* `docker-compose up --build`
### Локальный запуск (Без Docker)
Backend: `cd backend\config`, `pip install -r requirements.txt` + `cd backend\api`, `uvicorn main:app --reload`
Frontend: `cd frontend`, `npm install`, `npm start`

## Планы на будущее
- [ ] Redis.
- [ ] Fast API Authorization to guest.
- [ ] Test coverage 80%
- [ ] Hand cards filtering + hand cards owerflow problem
- [ ] Replishing, drawback, and on table drop cards animations
- [ ] Implement Tossing cards from others
- [ ] Updated rooms settings
- [ ] Make as telegramm mini-app
- [ ] Player Statistics
