import React, { useState, useCallback, useEffect, useRef } from 'react';
import { useParams, useLocation } from 'react-router-dom';
import LoadingScreen from 'components/UI/LoadingScreen';
import ConnectionStatus from 'components/UI/ConnectionStatus';
import Table from '../components/GameTable/Table';
import PlayerPositionsOnTable from 'components/GameTable/PlayerPositionOnTable';
import DeckWithTrump from 'components/GameTable/Deck';
import backImage from "assets/images/imperial_back.png";
import DiscardDeck from 'components/GameTable/DiscardDeck';
import Card from '../components/GameTable/Card';
import { getCardSvgPath } from 'utils/cardSvgLinker';
import 'assets/styles/game/Game.css';

// Импорт моков (для fallback)
import { mockGameScenarios } from '../mocks/gameMocks';

const TOTAL_DECK_CARDS = 36;

function Game() {
  const { game_id } = useParams();
  const location = useLocation();
  const websocketUrl = location.state?.websocket;
  // const websocketUrl = null;
  const ws = useRef(null);

  // WebSocket состояние
  const [connectionStatus, setConnectionStatus] = useState('Connecting');
  const [isUsingMocks, setIsUsingMocks] = useState(!websocketUrl);

  // Игровое состояние
  const scenario = 'midGame';
  const currentScenario = mockGameScenarios[scenario];

  const [gameState, setGameState] = useState({
    players: isUsingMocks ? currentScenario.players : [],
    yourCards: isUsingMocks ? currentScenario.yourCards : [],
    tableCards: isUsingMocks ? currentScenario.tableCards : [],
    deckSize: isUsingMocks ? currentScenario.deckCount : 0,
    trumpSuit: isUsingMocks ? currentScenario.trumpSuit : '',
    gamePhase: 'waiting',
    playerStatus: 'waiting'
  });

  // Добавляем состояние для отображения кнопки готовности
  const [showReadyButton, setShowReadyButton] = useState(true);

  // Отправка сообщений через WebSocket
  const sendWebSocketMessage = useCallback((message) => {
    if (ws.current?.readyState === WebSocket.OPEN) {
      console.log('Отправляем WebSocket сообщение:', message);
      ws.current.send(JSON.stringify(message));
    } else {
      console.warn('WebSocket не подключен, сообщение не отправлено:', message);
    }
  }, []);

  // Функции для отправки конкретных сообщений
  const sendPlayerReady = useCallback(() => {
    console.log('Отправляем статус готовности');
    sendWebSocketMessage({
      type: 'change_status',
      data: {
        player_id: sessionStorage.getItem('playerId'),
        status: 'ready'
      }
    });
    setGameState(prev => {
      console.log('Обновляем состояние на ready:', {
        oldStatus: prev.playerStatus,
        newStatus: 'ready',
        playerId: sessionStorage.getItem('playerId')
      });
      return { ...prev, playerStatus: 'ready' };
    });
  }, [sendWebSocketMessage]);

  const sendPlayerNotReady = useCallback(() => {
    console.log('Отправляем статус не готовности');
    sendWebSocketMessage({
      type: 'change_status',
      data: {
        player_id: sessionStorage.getItem('playerId'),
        status: 'not_ready'
      }
    });
    setGameState(prev => {
      console.log('Обновляем состояние на not_ready:', {
        oldStatus: prev.playerStatus,
        newStatus: 'not_ready',
        playerId: sessionStorage.getItem('playerId')
      });
      return { ...prev, playerStatus: 'not_ready' };
    });
  }, [sendWebSocketMessage]);

  // Обработчики для кнопки готовности
  const handleReadyClick = useCallback(() => {
    const isCurrentlyReady = gameState.playerStatus === 'ready';
    console.log('Нажата кнопка готовности:', {
      currentStatus: gameState.playerStatus,
      willBecomeReady: !isCurrentlyReady
    });
    if (!isCurrentlyReady) {
      sendPlayerReady();
    } else {
      sendPlayerNotReady();
    }
  }, [gameState.playerStatus, sendPlayerReady, sendPlayerNotReady]);

  // Обработка входящих WebSocket сообщений
  const handleWebSocketMessage = useCallback((event) => {
    const message = JSON.parse(event.data);
    const currentPlayerId = sessionStorage.getItem("playerId");

    switch (message.type) {
      case "connection_confirmed":
        console.log('Received game state:', {
          deckSize: message.data.deck_size,
          trumpSuit: message.data.trump_suit,
          trumpRank: message.data.trump_rank,
          fullMessage: message.data
        });

        // Находим текущего игрока и его статус
        const currentPlayer = message.data.room_players?.find(
          p => p.player_id === sessionStorage.getItem('playerId')
        );
        console.log('Статус игрока при подключении:', {
          playerId: currentPlayerId,
          status: currentPlayer?.status,
          isCurrentPlayer: !!currentPlayer
        });

        const playerStatus = currentPlayer?.status || 'not_ready';
        setGameState((prev) => {
          const newState = {
            ...prev,
            yourCards: message.data.cards || [],
            players: (message.data.room_players || []).map(player => ({
              id: player.player_id,
              name: player.name,
              cards: player.cards_count,
              position: player.position,
              status: player.status
            })),
            deckSize: message.data.deck_size,
            trumpSuit: message.data.trump_suit,
            trumpRank: message.data.trump_rank,
            attackerPosition: message.data.attacker_position,
            defenderPosition: message.data.defender_position,
            tableCards: (message.data.table_cards || []).map(pair => ({
              base: pair.attack_card,
              cover: pair.defend_card || null
            })),
            playerStatus: playerStatus
          };
          console.log('Обновлено состояние игры:', {
            trumpSuit: newState.trumpSuit,
            trumpRank: newState.trumpRank,
            deckSize: newState.deckSize,
            playerStatus: newState.playerStatus,
            allPlayersStatuses: newState.players.map(p => ({ id: p.id, status: p.status }))
          });
          return newState;
        });
        break;

      case 'card_played':
        console.log('CARD_PLAYED message received:', message.data);
        console.log('CARD_PLAYED table_cards:', message.data.table_cards);
        setGameState(prev => ({
          ...prev,
          tableCards: (message.data.table_cards || []).map(pair => ({
            base: pair.attack_card,
            cover: pair.defend_card || null
          })),
          attackerId: message.data.attacker_id,
          defenderId: message.data.defender_id,
        }));
        break;

      case 'player_joined':
        setGameState(prev => {
          const existingPlayerIndex = prev.players.findIndex(p => p.id === message.data.player_id);
          const updatedPlayers = existingPlayerIndex >= 0
            ? prev.players.map((p, index) => index === existingPlayerIndex
              ? { ...p, status: message.data.status, cards: message.data.cards_count, position: message.data.position }
              : p)
            : [...prev.players, {
              id: message.data.player_id,
              name: message.data.name,
              status: message.data.status,
              cards: message.data.cards_count,
              position: message.data.position
            }];
          return { ...prev, players: updatedPlayers };
        });
        break;

      case 'player_disconnected':
        console.log('Игрок отключился:', message.data);
        setGameState(prev => ({
          ...prev,
          players: prev.players.filter(p => p.id !== message.data.player_id)
        }));
        break;

      case 'player_status':
      case 'player_status_changed':
        console.log('Получено изменение статуса игрока:', {
          playerId: message.data.player_id,
          newStatus: message.data.status,
          isCurrentPlayer: message.data.player_id === currentPlayerId,
          currentGameState: gameState.playerStatus
        });

        setGameState(prev => ({
          ...prev,
          players: prev.players.map(p =>
            p.id === message.data.player_id
              ? { ...p, status: message.data.status }
              : p
          ),
          ...(message.data.player_id === currentPlayerId ? { playerStatus: message.data.status } : {})
        }));
        break;

      case 'game_phase_changed':
        console.log('Фаза игры изменена:', {
          newPhase: message.data.phase,
          currentPlayerStatus: gameState.playerStatus
        });
        setGameState(prev => ({
          ...prev,
          gamePhase: message.data.phase
        }));
        // Показываем кнопку готовности только в лобби
        setShowReadyButton(message.data.phase === 'LobbyState');
        break;

      default:
        console.warn('Неизвестный тип сообщения:', message.type);
    }
  }, []);

  // WebSocket подключение
  useEffect(() => {
    if (!websocketUrl) {
      console.log('WebSocket URL не найден, используем моки');
      setIsUsingMocks(true);
      setConnectionStatus('Connected');
      return;
    }

    // Добавляем токен к URL WebSocket
    const token = localStorage.getItem('token');
    const wsUrlWithToken = token ? `${websocketUrl}?token=${token}` : websocketUrl;

    console.log('Подключаемся к WebSocket:', wsUrlWithToken);
    ws.current = new WebSocket(wsUrlWithToken);

    ws.current.onopen = () => {
      console.log('WebSocket подключен');
      setConnectionStatus('Connected');
      setIsUsingMocks(false);

      // Отправляем сообщение о подключении сразу после установки соединения
      const connectMessage = {
        type: 'player_connected',
        data: {
          gameId: game_id,
          playerId: sessionStorage.getItem('playerId')
        }
      };
      console.log('Отправляем сообщение о подключении:', connectMessage);
      ws.current.send(JSON.stringify(connectMessage));
    };

    ws.current.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data);
        console.log('WebSocket сообщение получено:', message);
        handleWebSocketMessage(event);
      } catch (error) {
        console.error('Ошибка парсинга WebSocket сообщения:', error);
      }
    };

    ws.current.onclose = (event) => {
      console.log('WebSocket отключен:', event.code, event.reason);
      setConnectionStatus('Disconnected');
    };

    ws.current.onerror = (error) => {
      console.error('WebSocket ошибка:', error);
      setConnectionStatus('Error');
    };

    return () => {
      if (ws.current) {
        // Отправляем сообщение об отключении перед закрытием
        if (ws.current.readyState === WebSocket.OPEN) {
          const disconnectMessage = {
            type: 'player_disconnected',
            data: {
              gameId: game_id,
              playerId: sessionStorage.getItem('playerId')
            }
          };
          console.log('Отправляем сообщение об отключении:', disconnectMessage);
          ws.current.send(JSON.stringify(disconnectMessage));
        }
        ws.current.close(1000, 'Component unmounting');
      }
    };
  }, [websocketUrl, game_id, sendWebSocketMessage, handleWebSocketMessage]);

  // Количество сброшенных карт
  const calculateDiscardCount = useCallback(() => {
    const playersCardsSum = gameState.players.reduce((sum, player) => sum + (player.cards || 0), 0);
    const yourCardsCount = gameState.yourCards.length;
    // Считаем ВСЕ карты на столе (и base, и cover)
    const tableCardsCount = gameState.tableCards.reduce((sum, pair) => {
      let count = 0;
      if (pair && pair.base) count += 1;
      if (pair && pair.cover) count += 1;
      return sum + count;
    }, 0);
    return Math.max(0, TOTAL_DECK_CARDS - (playersCardsSum + yourCardsCount + tableCardsCount + gameState.deckSize));
  }, [gameState]);

  // Drag-n-drop обработчики
  const handleDragStart = useCallback((event, card) => {
    event.dataTransfer.setData("application/json", JSON.stringify(card));
  }, []);

  const handleDrop = useCallback((event, targetBaseCard) => {
    event.preventDefault();
    const card = JSON.parse(event.dataTransfer.getData("application/json"));

    if (isUsingMocks) {
      setGameState(prev => {
        let tableCards;
        if (targetBaseCard) {
          tableCards = prev.tableCards.map(pair => {
            if (
              pair.base.rank === targetBaseCard.rank &&
              pair.base.suit === targetBaseCard.suit &&
              !pair.cover
            ) {
              return { ...pair, cover: card };
            }
            return pair;
          });
        } else {
          tableCards = [...prev.tableCards, { base: card, cover: null }];
        }
        const yourCards = prev.yourCards.filter(
          c => c.rank !== card.rank || c.suit !== card.suit
        );
        return { ...prev, tableCards, yourCards };
      });
    } else {
      if (targetBaseCard) {
        // Защита (покрытие карты)
        sendWebSocketMessage({
          type: 'play_card',
          attack_card: targetBaseCard,
          defend_card: card
        });
      } else {
        // Атака (новая карта)
        sendWebSocketMessage({
          type: 'play_card',
          attack_card: card
        });
      }
      // Оптимистичное обновление (по желанию)
      setGameState(prev => {
        let tableCards;
        if (targetBaseCard) {
          tableCards = prev.tableCards.map(pair => {
            if (
              pair.base.rank === targetBaseCard.rank &&
              pair.base.suit === targetBaseCard.suit &&
              !pair.cover
            ) {
              return { ...pair, cover: card };
            }
            return pair;
          });
        } else {
          tableCards = [...prev.tableCards, { base: card, cover: null }];
        }
        const yourCards = prev.yourCards.filter(
          c => c.rank !== card.rank || c.suit !== card.suit
        );
        return { ...prev, tableCards, yourCards };
      });
    }
  }, [isUsingMocks, sendWebSocketMessage, game_id]);

  const handleDragOver = useCallback((event) => {
    event.preventDefault();
  }, []);

  // Показываем загрузку если подключаемся
  if (connectionStatus === 'Connecting' || connectionStatus === 'Reconnecting') {
    return <LoadingScreen status={connectionStatus} />;
  }

  return (
    <div className="card-table">
      <ConnectionStatus status={connectionStatus} isUsingMocks={isUsingMocks} />

      {/* Добавляем отладочную информацию */}
      {process.env.NODE_ENV === 'development' && (
        <div style={{ position: 'absolute', top: '40px', left: '10px', color: 'white', fontSize: '12px', zIndex: 1000 }}>
          <div>Trump Suit: {gameState.trumpSuit || 'not set'}</div>
          <div>Trump Rank: {gameState.trumpRank || 'not set'}</div>
          <div>Deck Size: {gameState.deckSize}</div>
        </div>
      )}

      {/* Кнопка готовности всегда видна */}
      <button
        onClick={handleReadyClick}
        className={`ready-button ${gameState.playerStatus === 'ready' ? 'ready-button--active' : ''}`}
      >
        {gameState.playerStatus === 'ready' ? 'Не готов' : 'Готов'}
      </button>

      {/* Показываем статус готовности других игроков */}
      <PlayerPositionsOnTable
        players={gameState.players}
        maxPositions={isUsingMocks ? 6 : 6}
        currentPlayerPosition={isUsingMocks ? 4 : 4}
        showStatus={showReadyButton} // Показываем статусы только в лобби
      />

      <Table
        playedCards={gameState.tableCards}
        onDrop={handleDrop}
        onDragOver={handleDragOver}
      />

      <DeckWithTrump
        count={gameState.deckSize}
        backImage={backImage}
        trumpCardImage={gameState.trumpSuit && gameState.trumpRank ?
          getCardSvgPath({
            rank: gameState.trumpRank,
            suit: gameState.trumpSuit.toLowerCase() === 'd' ? 'diamonds' :
              gameState.trumpSuit.toLowerCase() === 'h' ? 'hearts' :
                gameState.trumpSuit.toLowerCase() === 's' ? 'spades' :
                  gameState.trumpSuit.toLowerCase() === 'c' ? 'clubs' :
                    gameState.trumpSuit
          }) :
          backImage}
        trumpSuit={gameState.trumpSuit}
      />
      {/* Добавляем лог после рендера DeckWithTrump */}
      {console.log('DeckWithTrump props:', {
        count: gameState.deckSize,
        trumpSuit: gameState.trumpSuit,
        trumpRank: gameState.trumpRank,
        trumpCardImage: gameState.trumpSuit && gameState.trumpRank ?
          getCardSvgPath({ rank: gameState.trumpRank, suit: gameState.trumpSuit }) :
          'backImage'
      })}

      <DiscardDeck
        cardImage={require('assets/images/imperial_back.png')}
        count={calculateDiscardCount()}
        height={145}
        width={200}
      />

      <div className="card-table__your-cards">
        {gameState.yourCards.map((card) => (
          <Card
            key={`${card.rank}-${card.suit}`}
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

export default Game;
