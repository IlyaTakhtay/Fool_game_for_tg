import './CreatingRoom.css';
import React, { useState } from 'react';
import SoloButton from '../components/SoloButton';
import { useNavigate } from 'react-router-dom';

function CreatingRoom() {
  const [isPublic, setIsPublic] = useState(true);
  const [gameName, setGameName] = useState('');
  const [playersCount, setPlayersCount] = useState(2);
  const [privateField, setPrivateField] = useState('');
  const navigate = useNavigate();

  // Generate a random game name
  const generateGameName = () => {
    const randomName = `Game_${Math.floor(Math.random() * 100000)}`;
    setGameName(randomName);
  };

  const generatePlayerId = () => {
    return Math.floor(Math.random() * 100000);
  };


  // Handle form submission
  const handleSubmit = async (e) => {
    e.preventDefault();
    const gameData = {
      name: gameName,
      isPublic,
      room_size: playersCount,
      ...(isPublic === false && { privateField }),
    };
    console.log("Создать игру:", gameData);
    try {
      // Отправка POST-запроса на сервер
      let playerId = generatePlayerId()
      const response = await fetch(`http://${process.env.REACT_APP_BACKEND_DOMEN}/create_game/${playerId}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(gameData),
      });
  
      if (!response.ok) {
        throw new Error('Ошибка при создании игры');
      }
  
      // Получаем game_id из ответа сервера
      const responseData = await response.json();
      const { game_id } = responseData; // Предположим, что сервер возвращает game_id
  
      console.log("Игра создана, game_id:", game_id);
  

      // Редирект на страницу с WebSocket по game_id и player_id
      navigate(`/card-table/${game_id}/${playerId}`);
      } catch (error) {
        console.error('Ошибка при создании игры:', error);
      }
  };

 

  const handleBackwards = (e) => {
    navigate('/');
  }

  return (
    <div className="page-container">
      <h1 className="title">Создание игры</h1>
      <form onSubmit={handleSubmit} className="create-game-form">
      {/* Toggle for public/private */}
      <div className="create-game-form__form-group">
        <label className="create-game-form__label">Доступ:</label>
        <div className="create-game-form__toggle-bar">
          <button 
            type="button" 
            className={`create-game-form__toggle-option ${isPublic ? 'active' : ''}`} 
            onClick={() => setIsPublic(true)}
          >
            Public
          </button>
          <button 
            type="button" 
            className={`create-game-form__toggle-option ${!isPublic ? 'active' : ''}`} 
            onClick={() => setIsPublic(false)}
          >
            Private
          </button>
        </div>
      </div>

      {/* Game name input */}
      <div className="create-game-form__form-group">
        <label className="create-game-form__label">Название команды:</label>
        <input 
          type="text" 
          className="create-game-form__input"
          value={gameName} 
          onChange={(e) => setGameName(e.target.value)} 
          placeholder="Введите название или автогенерируйте" 
        />
        <button type="button" onClick={generateGameName} className="create-game-form__generate-btn">Автогенерация</button>
      </div>

      {/* Players count drop-down */}
      <div className="create-game-form__form-group">
        <label className="create-game-form__label">Количество игроков:</label>
        <select 
          className="create-game-form__select"
          value={playersCount} 
          onChange={(e) => setPlayersCount(Number(e.target.value))}
        >
          {[2, 3, 4, 5, 6].map((count) => (
            <option key={count} value={count}>{count}</option>
          ))}
        </select>
      </div>

      {/* Private field */}
      {!isPublic && (
        <div className="create-game-form__form-group">
          <label className="create-game-form__label">Дополнительная информация:</label>
          <input 
            type="text" 
            className="create-game-form__input"
            value={privateField} 
            onChange={(e) => setPrivateField(e.target.value)} 
            placeholder="Введите доп. информацию"
          />
        </div>
      )}

      {/* Action buttons */}
      <div className="create-game-form__button-group">
        <SoloButton type="button" onClick={handleBackwards} text="Назад" />
        <SoloButton type="submit" text="Создать" />
      </div>
      </form>
    </div>
  );
}

export default CreatingRoom;
