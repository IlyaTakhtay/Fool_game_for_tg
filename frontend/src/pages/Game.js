import React, { useState, useCallback, useEffect, useRef } from 'react';
import { useParams, useLocation } from 'react-router-dom';
import LoadingScreen from 'components/UI/LoadingScreen';
import ConnectionStatus from 'components/UI/ConnectionStatus';
import Table from '../components/GameTable/Table';
import PlayerPositionsOnTable from 'components/GameTable/PlayerPositionOnTable';
import DeckWithTrump from 'components/GameTable/Deck';
import backImage from 'assets/images/imperial_back.png';
import DiscardDeck from 'components/GameTable/DiscardDeck';
import Card from '../components/GameTable/Card';
import { getCardSvgPath } from 'utils/cardSvgLinker';
import 'assets/styles/game/Game.css';
import { ToastContainer, toast } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';
import { mockGameScenarios } from '../mocks/gameMocks';

const TOTAL_DECK_CARDS = 36;

function Game() {
  const { game_id } = useParams();
  const location = useLocation();
  const websocketUrl = location.state?.websocket;
  const ws = useRef(null);

  const [connectionStatus, setConnectionStatus] = useState('Connecting');
  const [isUsingMocks, setIsUsingMocks] = useState(!websocketUrl);

  const scenario = 'midGame';
  const currentScenario = mockGameScenarios[scenario];

  const [gameState, setGameState] = useState({
    players: isUsingMocks ? currentScenario.players : [],
    yourCards: isUsingMocks ? currentScenario.yourCards : [],
    tableCards: isUsingMocks ? currentScenario.tableCards : [],
    deckSize: isUsingMocks ? currentScenario.deckCount : 0,
    trumpSuit: isUsingMocks ? currentScenario.trumpSuit : '',
    gamePhase: 'LobbyState',
    playerStatus: 'waiting',
    yourAllowedActions: [],
  });

  const [showReadyButton, setShowReadyButton] = useState(true);

  const sendWebSocketMessage = useCallback((message) => {
    if (ws.current?.readyState === WebSocket.OPEN) {
      ws.current.send(JSON.stringify(message));
    } else {
      console.warn('WebSocket не подключен, сообщение не отправлено:', message);
    }
  }, []);

  const sendPlayerReady = useCallback(() => {
    sendWebSocketMessage({
      type: 'change_status',
      data: { player_id: sessionStorage.getItem('playerId'), status: 'ready' },
    });
  }, [sendWebSocketMessage]);

  const sendPlayerNotReady = useCallback(() => {
    sendWebSocketMessage({
      type: 'change_status',
      data: { player_id: sessionStorage.getItem('playerId'), status: 'not_ready' },
    });
  }, [sendWebSocketMessage]);

  const handleReadyClick = useCallback(() => {
    const isCurrentlyReady = gameState.playerStatus === 'ready';
    if (!isCurrentlyReady) {
      sendPlayerReady();
    } else {
      sendPlayerNotReady();
    }
  }, [gameState.playerStatus, sendPlayerReady, sendPlayerNotReady]);

  const handlePassClick = useCallback(() => {
    sendWebSocketMessage({ type: 'pass_turn' });
  }, [sendWebSocketMessage]);

  const handleWebSocketMessage = useCallback((event) => {
    try {
      const message = JSON.parse(event.data);
      const currentPlayerId = sessionStorage.getItem("playerId");

      switch (message.type) {
        case "error":
          const errorCode = message.data.code || "INTERNAL_ERROR";
          toast.error(message.data.message, {
            position: "top-right",
            autoClose: 3000,
            hideProgressBar: false,
            closeOnClick: true,
            pauseOnHover: true,
            draggable: true,
            progress: undefined,
            theme: "dark",
            toastId: errorCode,
            className: `game-error-toast-${errorCode.toLowerCase()}`,
            data: { 'error-code': errorCode },
          });
          break;

        case "connection_confirmed":
          const isCurrentPlayerAttacker = message.data.position === message.data.attacker_position;
          const isCurrentPlayerDefender = message.data.position === message.data.defender_position;
          
          const attackerFromPlayers = isCurrentPlayerAttacker 
            ? { player_id: currentPlayerId, position: message.data.position }
            : message.data.room_players?.find(p => p.position === message.data.attacker_position);
            
          const defenderFromPlayers = isCurrentPlayerDefender
            ? { player_id: currentPlayerId, position: message.data.position }
            : message.data.room_players?.find(p => p.position === message.data.defender_position);

          const attackerId = attackerFromPlayers?.player_id;
          const defenderId = defenderFromPlayers?.player_id;
          const playerStatus = message.data.status || 'not_ready';
          
          setGameState((prev) => {
            const allPlayers = [
              {
                id: currentPlayerId,
                name: `Player ${currentPlayerId}`,
                cards: message.data.cards?.length || 0,
                position: message.data.position,
                status: playerStatus
              },
              ...(message.data.room_players || []).map(player => ({
                id: player.player_id,
                name: player.name,
                cards: player.cards_count,
                position: player.position,
                status: player.status
              }))
            ].sort((a, b) => a.position - b.position);

            return {
              ...prev,
              yourCards: message.data.cards || [],
              players: allPlayers,
              deckSize: message.data.deck_size,
              trumpSuit: message.data.trump_suit,
              trumpRank: message.data.trump_rank,
              attackerPosition: message.data.attacker_position,
              defenderPosition: message.data.defender_position,
              current_attacker_id: attackerId,
              current_defender_id: defenderId,
              player_id: currentPlayerId,
              player_position: message.data.position,
              tableCards: (message.data.table_cards || []).map(pair => ({
                base: pair.attack_card,
                cover: pair.defend_card || null
              })),
              playerStatus: playerStatus,
              gamePhase: message.data.current_state || 'LobbyState',
              yourAllowedActions: message.data.allowed_actions || [],
              isAttacker: isCurrentPlayerAttacker,
              isDefender: isCurrentPlayerDefender
            };
          });
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
          setGameState(prev => ({
            ...prev,
            players: prev.players.filter(p => p.id !== message.data.player_id)
          }));
          break;

        case 'self_status_update':
          setGameState(prev => ({
            ...prev,
            playerStatus: message.data.status,
            yourAllowedActions: message.data.allowed_actions || prev.yourAllowedActions
          }));
          break;

        case 'player_status_changed':
          setGameState(prev => ({
            ...prev,
            players: prev.players.map(p => 
              p.id === message.data.player_id 
                ? { ...p, status: message.data.status } 
                : p
            )
          }));
          break;
        
        default:
          console.warn('Неизвестный тип сообщения от WebSocket:', message.type);
      }
    } catch (error) {
      console.error('Ошибка обработки WebSocket сообщения:', error);
    }
  }, []);

  useEffect(() => {
    if (!websocketUrl) {
      setIsUsingMocks(true);
      setConnectionStatus('Connected');
      return;
    }

    const token = localStorage.getItem('token');
    const wsUrlWithToken = token ? `${websocketUrl}?token=${token}` : websocketUrl;

    ws.current = new WebSocket(wsUrlWithToken);
    ws.current.onopen = () => {
      setConnectionStatus('Connected');
      setIsUsingMocks(false);
      sendWebSocketMessage({ type: 'player_connected' });
    };
    ws.current.onmessage = handleWebSocketMessage;
    ws.current.onclose = () => setConnectionStatus('Disconnected');
    ws.current.onerror = () => setConnectionStatus('Error');

    return () => {
      ws.current?.close(1000, 'Component unmounting');
    };
  }, [websocketUrl, sendWebSocketMessage, handleWebSocketMessage]);

  const calculateDiscardCount = useCallback(() => {
    const otherPlayersCardsSum = gameState.players
      .filter(p => p.id !== gameState.player_id)
      .reduce((sum, player) => sum + (player.cards || 0), 0);
      
    const yourCardsCount = gameState.yourCards.length;
    const tableCardsCount = gameState.tableCards.reduce((sum, pair) => sum + (pair.base ? 1 : 0) + (pair.cover ? 1 : 0), 0);
    const totalCardsInPlay = otherPlayersCardsSum + yourCardsCount + tableCardsCount + gameState.deckSize;

    return Math.max(0, TOTAL_DECK_CARDS - totalCardsInPlay);
  }, [gameState.players, gameState.yourCards, gameState.tableCards, gameState.deckSize, gameState.player_id]);

  const canAttack = gameState.yourAllowedActions.includes('ATTACK');
  const canDefend = gameState.yourAllowedActions.includes('DEFEND');
  const canPass = gameState.yourAllowedActions.includes('PASS');

  const performMove = useCallback((droppedCard, targetBaseCard) => {
    const isDefending = !!targetBaseCard;
    if ((isDefending && !canDefend) || (!isDefending && !canAttack)) {
      return;
    }

    if (!isUsingMocks) {
      sendWebSocketMessage({
        type: 'play_card',
        ...(isDefending ? { attack_card: targetBaseCard, defend_card: droppedCard } : { attack_card: droppedCard })
      });
    }

    setGameState(prev => {
      const newYourCards = prev.yourCards.filter(c => !(c.rank === droppedCard.rank && c.suit === droppedCard.suit));
      let newTableCards;
      if (isDefending) {
        newTableCards = prev.tableCards.map(pair => 
          pair.base.rank === targetBaseCard.rank && pair.base.suit === targetBaseCard.suit
            ? { ...pair, cover: droppedCard }
            : pair
        );
      } else {
        newTableCards = [...prev.tableCards, { base: droppedCard, cover: null }];
      }
      return { ...prev, yourCards: newYourCards, tableCards: newTableCards };
    });
  }, [canAttack, canDefend, isUsingMocks, sendWebSocketMessage]);

  const handleCustomCardDrop = useCallback((event, droppedCard) => {
    const dropTarget = document.elementFromPoint(event.clientX, event.clientY);
    const attackZone = dropTarget?.closest('[data-is-attack-zone="true"]');
    const defenseSlot = dropTarget?.closest('[data-base-card]');
    let wasSuccessful = false;

    if (defenseSlot && canDefend) {
      const targetCard = JSON.parse(defenseSlot.dataset.baseCard);
      performMove(droppedCard, targetCard);
      wasSuccessful = true;
    } else if (attackZone && canAttack) {
      performMove(droppedCard, null);
      wasSuccessful = true;
    }
    return wasSuccessful;
  }, [performMove, canAttack, canDefend]);

  if (connectionStatus === 'Connecting') {
    return <LoadingScreen status={connectionStatus} />;
  }

  return (
    <div className="game">
      <ToastContainer limit={3} newestOnTop={true} />
      <div className="card-table">
        <ConnectionStatus status={connectionStatus} isUsingMocks={isUsingMocks} />

        {canPass && (
          <button onClick={handlePassClick} className="ready-button pass-button">Пас</button>
        )}
        {gameState.yourAllowedActions.includes('READY') && (
          <button onClick={handleReadyClick} className="ready-button">Готов</button>
        )}
        {gameState.yourAllowedActions.includes('UNREADY') && (
          <button onClick={handleReadyClick} className="ready-button ready-button--active">Не готов</button>
        )}

        <PlayerPositionsOnTable
          players={gameState.players.filter(p => p.id !== gameState.player_id)}
          maxPositions={6}
          currentPlayerPosition={gameState.player_position}
          showStatus={showReadyButton}
          attackerPosition={gameState.attackerPosition}
          defenderPosition={gameState.defenderPosition}
        />

        <Table
          playedCards={gameState.tableCards}
          isDefender={canDefend}
          isAttacker={canAttack}
        />

        <DeckWithTrump
          count={gameState.deckSize}
          backImage={backImage}
          trumpCardImage={gameState.trumpSuit && gameState.trumpRank ? getCardSvgPath({ rank: gameState.trumpRank, suit: gameState.trumpSuit }) : backImage}
          trumpSuit={gameState.trumpSuit}
        />

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
              draggable={canAttack || canDefend}
              className="card--face"
              onCustomDrop={handleCustomCardDrop}
            />
          ))}
        </div>
      </div>
    </div>
  );
}

export default Game;
