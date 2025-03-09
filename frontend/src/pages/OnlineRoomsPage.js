import './Pages.css';
import React, { useEffect, useState } from 'react';
import SoloButton from '../components/SoloButton';
import BeautyForm from '../components/BeautyForm'
import { useNavigate } from 'react-router-dom';

function GameList() {
  const [games, setGames] = useState([]);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  const handleBackwards = () => {
    navigate('/');
  };

  const generateRandomPlayerId = () => {
    return Math.random().toString(36).substr(2, 9); // Генерация случайного идентификатора
  };

  const handleGameClick = (gameId) => {
    const playerId = generateRandomPlayerId();
    navigate(`/card-table/${gameId}/${playerId}`);
  };

  useEffect(() => {
    async function fetchGames() {
      try {
        const response = await fetch(`http://${process.env.REACT_APP_BACKEND_DOMEN}/games_list`);
        console.log(response)
        const data = await response.json();
        const parsedGames = data.map((game) => ({
          id: game.game_id,
          name: `Игра ${game.game_id}`, // Можно адаптировать
          players: { current: game.players, max: game.room_size },
          isPublic: !game.password, // Если `password: false`, значит игра открытая
        }));
        setGames(parsedGames);
      } catch (error) {
        console.error("Error fetching games:", error);
      } finally {
        setLoading(false);
      }
    }

    fetchGames();
  }, []);

  if (loading) {
    return <p className="loading-text">Загрузка...</p>;
  }

  return (
    <div className = "page-container"> 
    <h2 className="title">Список игр</h2>
      <BeautyForm className='beauty-form--table'>
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
                onClick={() => handleGameClick(game.id)} // Переход по клику на игру
                style={{ cursor: 'pointer' }} // Курсор для указания кликабельности
              >
                <td>{game.name}</td>
                <td>{`${game.players.current}/${game.players.max}`}</td>
                <td>{game.isPublic ? "Открытая" : "Закрытая"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </BeautyForm>
      <SoloButton onClick={handleBackwards} text="Назад" />
    </div>
  );
}

export default GameList;
