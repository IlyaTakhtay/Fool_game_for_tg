import 'assets/styles/Pages.css';
import React, { useEffect, useState } from 'react';
import LoadingAnimation from 'components/UI/LoadingAnimation';
import MenuButton from '../components/UI/MenuButton';
import BeautyForm from '../components/UI/BeautyForm';
import { useNavigate } from 'react-router-dom';
import { ROUTES } from 'constants/routes';
import { API_BASE_URL } from 'constants/api';
import api from 'utils/apiMiddleware';

function GamesList() {
  const [games, setGames] = useState([]);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  const handleBackwards = () => {
    navigate('/');
  };

  const handleGameClick = async (gameId) => {
    try {
      const playerId = sessionStorage.getItem('playerId');
      if (!playerId) {
        console.error('No player_id found in sessionStorage');
        return;
      }

      const joinGameData = await api.post(
        `/join_game?player_id=${playerId}&game_id=${gameId}`
      );
      navigate(`${ROUTES.GAME.replace(':game_id', gameId)}`, {
        state: { websocket: joinGameData.websocketConnection },
      });
    } catch (error) {
      if (error.status === 409) {
        // const errorMessage = error.response?.data?.detail || 'Игра полная';
        // alert(errorMessage);
        // return;
        // TODO: сделать на нотификациях
        navigate(`${ROUTES.GAME.replace(':game_id', gameId)}/`);
      }
      console.error('Error joining game:', error);
    }
  };

  // Получение списка игр через SSE
  useEffect(() => {
    let eventSource = null;
    let isMounted = true;  // Флаг для отслеживания монтирования
    let reconnectTimeout = null;  // Таймаут для переподключения

    const connectSSE = () => {
      // Не устанавливаем соединение, если компонент размонтирован
      if (!isMounted) {
        return;
      }

      // Проверяем наличие player_id
      const playerId = sessionStorage.getItem('playerId');

      if (!playerId) {
        console.error('No player_id found in sessionStorage');
        setLoading(false);  // Прекращаем показывать загрузку, если нет player_id
        return;
      }

      // Закрываем предыдущее соединение, если оно существует
      if (eventSource) {
        eventSource.close();
        eventSource = null;
      }

      try {
        const sseUrl = `${API_BASE_URL}/api/v1/games/stream?player_id=${playerId}`;
        eventSource = new EventSource(sseUrl);

        eventSource.onopen = () => {
          // SSE connection opened successfully
        };

        eventSource.onmessage = (event) => {
          // Проверяем, что компонент все еще смонтирован
          if (!isMounted) return;

          const gamesList = JSON.parse(event.data);
          const parsedGames = gamesList.map((game) => ({
            id: game.game_id,
            name: `Игра ${game.game_id}`,
            players: {
              current: game.players_inside,
              max: game.players_limit
            },
            isPublic: !game.password,
          }));
          setGames(parsedGames);
          setLoading(false);
        };

        eventSource.onerror = (error) => {
          console.error('SSE Error:', error);
          if (eventSource) {
            eventSource.close();
            eventSource = null;
          }

          // Пробуем переподключиться через 5 секунд только если компонент все еще смонтирован
          if (isMounted) {
            if (reconnectTimeout) {
              clearTimeout(reconnectTimeout);
            }
            reconnectTimeout = setTimeout(connectSSE, 5000);
          }
        };

        // Добавляем обработчик для ping событий
        eventSource.addEventListener('ping', () => {
          if (!isMounted) return;
        });

        // Добавляем обработчик для games_update событий
        eventSource.addEventListener('games_update', (event) => {
          if (!isMounted) return;
          const gamesList = JSON.parse(event.data);
          const parsedGames = gamesList.map((game) => ({
            id: game.game_id,
            name: `Игра ${game.game_id}`,
            players: {
              current: game.players_inside,
              max: game.players_limit
            },
            isPublic: !game.password,
          }));
          setGames(parsedGames);
          setLoading(false);
        });

        // Добавляем обработчик для закрытия соединения
        eventSource.addEventListener('close', (event) => {
          if (eventSource) {
            eventSource.close();
            eventSource = null;
          }
        });
      } catch (error) {
        console.error('Error creating SSE connection:', error);
        setLoading(false);
      }
    };

    // Устанавливаем соединение при монтировании
    connectSSE();

    // Функция очистки при размонтировании
    return () => {
      isMounted = false;  // Помечаем компонент как размонтированный

      // Очищаем таймаут переподключения
      if (reconnectTimeout) {
        clearTimeout(reconnectTimeout);
        reconnectTimeout = null;
      }

      // Закрываем соединение
      if (eventSource) {
        eventSource.close();
        eventSource = null;
      }
    };
  }, []); // Пустой массив зависимостей означает, что эффект запустится только при монтировании

  if (loading) {
    return <LoadingAnimation />;
  }

  return (
    <div className="page-container">
      <h2 className="title">Список игр</h2>
      <BeautyForm className="beauty-form--table">
        <table className="beauty-form__table">
          <thead>
            <tr>
              <th>Название</th>
              <th>Игроки</th>
              <th>Доступ</th>
            </tr>
          </thead>
          <tbody>
            {games.map((game) => (
              <tr
                key={game.id}
                onClick={() => handleGameClick(game.id)}
                style={{ cursor: 'pointer' }}
              >
                <td>{game.name}</td>
                <td>{`${game.players.current}/${game.players.max}`}</td>
                <td>{game.isPublic ? 'Открытая' : 'Закрытая'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </BeautyForm>
      <MenuButton onClick={handleBackwards} text="Назад" className="solo"/>
    </div>
  );
}

export default GamesList;
