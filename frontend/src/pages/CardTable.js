import React, { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import Table from '../components/GameTable/Table';
import Player from '../components/GameTable/Player';
import Card from '../components/GameTable/Card';
import './CardTable.css';



function CardTable() {
  const { gameId, userId } = useParams(); // получаем параметры из URL
  const [players, setPlayers] = useState([]);
  const [yourCards, setYourCards] = useState(['🂡', '🂢', '🂣', '🂤', '🂥', '🂾', '🂽']);
  const [playedCards, setPlayedCards] = useState([]);
  const [tableData, setTableData] = useState([]);
  const [socket, setSocket] = useState(null); // Добавляем состояние для WebSocket
  const [loading, setLoading] = useState(true); // Состояние для "loading"
  const [connectionStatus, setConnectionStatus] = useState(null); // Состояние для статуса подключения (accept/denied)
  const navigate = useNavigate(); // Для навигации

  
  


  // Устанавливаем WebSocket
  useEffect(() => {
    // setPlayers([
    //   { id: "1", name: "Player 1", cards: 24, status: "unready" },
    //   { id: "2", name: "Player 2", cards: 3, status:"ready" },
    //   { id: "3", name: "Player 3", cards: 4, status: "unready" },
    //   { id: "4", name: "Player 4", cards: 7, status: "unread" },
    // ]);
  
    setTableData([
      { card: "🂡", playerId: "1" },
      { card: "🂢", playerId: "2" },
    ]);
    console.log(`Попытка подключиться к WebSocket:${process.env.REACT_APP_BACKEND_DOMEN}/ws/${gameId}/${userId}`);
    const socket = new WebSocket(`ws://${process.env.REACT_APP_BACKEND_DOMEN}/ws/${gameId}/${userId}`);
  
    socket.onopen = () => {
      console.log("WebSocket открыт");
    };
    
    socket.onmessage = (event) => {
      const data = JSON.parse(event.data);
      console.log("Получены данные:", data);
      
      // Если подключение отклонено, устанавливаем статус "denied"
      if (data.connection === "denied") {
        setConnectionStatus("denied");
        setLoading(false);
        return;
      }

      if (data.connection === "accept") {
        setPlayers(data.players || []);
        setTableData(data.tableData || []);
        setConnectionStatus("accept");
        setLoading(false);
      }

      if (data.player && Array.isArray(data.player)) {
        setPlayers((prevPlayers) => {
          // Создаём новый массив, объединяя текущих игроков с новыми, избегая дубликатов
          const updatedPlayers = [...prevPlayers];
      
          data.player.forEach((newPlayer) => {
            // Проверяем, существует ли уже игрок с таким ID
            if (!updatedPlayers.some(player => player.id === newPlayer.id)) {
              if (!newPlayer.hasOwnProperty('cards')) {
                newPlayer.cards = 0;
              }
                updatedPlayers.push(newPlayer);
            }
          });
      
          return updatedPlayers; // Возвращаем обновлённый массив
        });
      }
    };
  
    socket.onclose = () => {
      console.log("WebSocket закрыт");
    };
  
    socket.onerror = (error) => {
      console.error("Ошибка WebSocket:", error);
      // setConnectionStatus("denied");
      setLoading(false);
    };
  
    setSocket(socket);

    // Закрываем WebSocket при размонтировании компонента
    return () => {
      socket.close();
    };
  }, [gameId, userId]);

  // Обработчики для перетаскивания карт
  const handleDragStart = useCallback((event, card) => {
    event.dataTransfer.setData("text/plain", card);
  }, []);

  const handleDrop = useCallback((event) => {
    event.preventDefault();
    const card = event.dataTransfer.getData("text");
    setPlayedCards(prevPlayedCards => [...prevPlayedCards, card]);
    setYourCards(prevYourCards => prevYourCards.filter(c => c !== card));
  }, []);

  const handleDragOver = useCallback((event) => {
    event.preventDefault();
  }, []);

  if (loading) {
    return <p className="loading-text">Загрузка...</p>;
  }

  if (connectionStatus === "denied") {
    return <p className="error-text">Доступ к игре отклонен: Игровая комната полна.</p>;
  }

  return (
    <div className="card-table">
      <Table 
        playedCards={playedCards} 
        onDrop={handleDrop} 
        onDragOver={handleDragOver} 
      />

    <div className="card-table__players">
      {players && players.length > 0 ? (
        players.map((player, index) => (
          <Player 
            key={player.id}
            player={player} 
            className={`player player--${index + 1}`} 
          />
        ))
      ) : (
        <p className="error-text">Нет игроков для отображения</p>
      )}
    </div>

      <div className="card-table__your-cards">
        {yourCards.map((card, i) => (
          <Card 
            key={i} 
            card={card} 
            onDragStart={(e) => handleDragStart(e, card)} 
            draggable 
            className="card--face"
          />
        ))}
      </div>
    </div>
  );
}

export default CardTable;
