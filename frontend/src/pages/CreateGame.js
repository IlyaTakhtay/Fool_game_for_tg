import React, { useState, useEffect } from 'react';
import MenuButton from '../components/UI/MenuButton';
import BeautyForm from '../components/UI/BeautyForm';
import 'assets/styles/CreateGame.css';
import { useNavigate } from 'react-router-dom';
import { ROUTES } from 'constants/routes';
import api from 'utils/apiMiddleware';

// Компонент для группы полей
function FieldGroup({ label, children }) {
  return (
    <div className="create-game-form__field-group">
      <label className="create-game-form__label">{label}</label>
      {children}
    </div>
  );
}

function CreateGame() {
  const [playersCount, setPlayersCount] = useState(2); // Количество игроков
  const navigate = useNavigate();

  // Проверка активной игры при загрузке страницы
  useEffect(() => {
    const checkActiveGame = async () => {
      try {
        const playerId = sessionStorage.getItem('playerId'); // ID игрока из sessionStorage
        if (!playerId) {
          console.error('Player ID отсутствует в sessionStorage');
          return;
        }

        // Запрос на бэкенд для проверки активной игры
        const response = await api.get(`/player_game?player_id=${playerId}`);
        console.log('Активная игра найдена:', response);

        // Если есть активная игра, выполняем редирект
        const { gameId } = response;
        navigate(`${ROUTES.GAME.replace(':game_id', gameId)}`, {
          state: { websocket: response.websocketConnection },
        });
      } catch (error) {
        if (error.response?.status === 404) {
          console.log('Активная игра не найдена, продолжение на странице создания игры.');
        } else {
          console.error('Ошибка при проверке активной игры:', error.message);
        }
      }
    };

    checkActiveGame();
  }, [navigate]);

  // Универсальный обработчик для навигации
  const handleNavigation = (path, data = null) => () => {
    navigate(path, { state: data });
  };

  // Обработка отправки формы
  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const playerId = sessionStorage.getItem('playerId');
      if (!playerId) {
        console.error('Player ID отсутствует в sessionStorage');
        return;
      }

      // Создание игры
      const createGameData = await api.post(`/create_game?set_players_limit=${playersCount}`);
      console.log('Игра создана:', createGameData);
      const { gameId } = createGameData;

      // Подключение к игре
      const joinGameData = await api.post(
        `/join_game?player_id=${playerId}&game_id=${gameId}`
      );
      sessionStorage.setItem('activeGameId', gameId);
      console.log('Результат подключения к игре:', joinGameData);

      // Редирект в игру
      handleNavigation(`${ROUTES.GAME.replace(':game_id', gameId)}`, {
        websocket: joinGameData.websocketConnection,
      })();
    } catch (error) {
      console.error('Ошибка при создании или подключении к игре', error.message);
    }
  };

  // Обработка кнопки "Назад"
  const handleBackwards = handleNavigation('/');

  return (
    <div className="page-container">
      <h1 className="title">Создание игры</h1>
      <BeautyForm>
        {/* Поля формы */}
        <div className="beauty-form__fields">
          <FieldGroup label="Количество игроков:">
            <select
              className="create-game-form__select"
              value={playersCount}
              onChange={(e) => setPlayersCount(Number(e.target.value))}
            >
              {[2, 3, 4, 5, 6].map((count) => (
                <option key={count} value={count}>{count}</option>
              ))}
            </select>
          </FieldGroup>
        </div>

        {/* Кнопки действий */}
        <div className="beauty-form__buttons">
          <MenuButton type="button" onClick={handleBackwards} text="Назад" />
          <MenuButton type="submit" onClick={handleSubmit} text="Создать" />
        </div>
      </BeautyForm>
    </div>
  );
}

export default CreateGame;
