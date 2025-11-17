import http from 'k6/http';
import ws from 'k6/ws';
import { Counter, Rate } from 'k6/metrics';
import { sleep } from 'k6';

const messagesSent = new Counter('messages_sent');
const messagesReceived = new Counter('messages_received');
const gamesCompleted = new Counter('games_completed');
const validMoves = new Counter('valid_moves');
const gameStateUpdates = new Counter('game_state_updates');
const errorRate = new Rate('error_messages');

export const options = {
  scenarios: {
    game_pairs: {
      executor: 'per-vu-iterations',
      vus: 100,           // 100 VU = 50 игр (по 2 игрока)
      iterations: 1,
      maxDuration: '3m',
    },
  },
  thresholds: {
    error_messages: ['rate<0.1'],
    games_completed: ['count>49'], // Expecting 50 games to complete
    // WebSocket RPS thresholds
    messages_sent: ['rate>20'],     // At least 20 messages sent per second
    messages_received: ['rate>20'], // At least 20 messages received per second
  },
};

const BASE_URL = 'http://localhost:8000/api/v1';

export function setup() {
  const pairCount = 50;
  const gameIds = [];
  console.log(`\n=== SETUP: creating ${pairCount} games ===`);
  for (let i = 0; i < pairCount; i++) {
    const res = http.post(`${BASE_URL}/create_game?set_players_limit=2`, null, { headers: { 'Content-Type': 'application/json' } });
    if (res.status === 200) {
      const gameId = JSON.parse(res.body).game_id;
      console.log(`[SETUP] Game[${i}] created: ${gameId}`);
      gameIds.push(gameId);
    } else {
      console.error(`[SETUP] Failed to create game[${i}]. Status: ${res.status}, Body: ${res.body}`);
    }
  }
  if (gameIds.length === 0) {
    throw new Error('No games were created in setup');
  }
  return { gameIds };
}

export default function (data) {
  sleep(Math.random() * 2); // Stagger VUs

  const pairIndex = Math.floor((__VU - 1) / 2);
  const gameId = data.gameIds[pairIndex % data.gameIds.length];
  const role = (__VU % 2) === 1 ? 'P1' : 'P2';
  const playerName = `${role}_Game${pairIndex}`;
  const pairLabel = `PAIR_${pairIndex}_${role}`;

  console.log(`\n🎮 [${pairLabel}] VU=${__VU} starting gameId=${gameId}`);

  const authRes = http.post(`${BASE_URL}/auth_guest`, JSON.stringify({ player_name: playerName }), { headers: { 'Content-Type': 'application/json' } });
  if (authRes.status !== 200) {
    errorRate.add(1);
    console.error(`[${pairLabel}] Auth failed: ${authRes.status}`);
    return;
  }
  const playerId = JSON.parse(authRes.body).player_id;

  const joinRes = http.post(`${BASE_URL}/join_game?player_id=${playerId}&game_id=${gameId}`, null, { headers: { 'Content-Type': 'application/json' } });
  if (joinRes.status !== 200) {
    errorRate.add(1);
    console.error(`[${pairLabel}] Join failed: ${joinRes.status}`);
    return;
  }
  const wsUrl = JSON.parse(joinRes.body).websocket_connection.replace(/^http/, 'ws');

  let isSocketClosed = false;
  const res = ws.connect(wsUrl, function (socket) {
    let gameState = {};
    let turnInterval;

    socket.on('open', () => {
      console.log(`✓ [${pairLabel}] WS CONNECTED`);
      socket.send(JSON.stringify({ type: 'player_connected' }));
      messagesSent.add(1);
      turnInterval = socket.setInterval(takeTurn, 50);
    });

    socket.on('message', (data) => {
      messagesReceived.add(1);
      try {
        const msg = JSON.parse(data);
        if (msg.type === 'game_ended' || msg.type === 'GameOverState') {
          console.log(`🏁 [${pairLabel}] GAME ENDED`);
          gamesCompleted.add(1);
          socket.close();
          return;
        }

        if (msg.type === 'error') {
          const errorCode = msg.data?.code || 'UNKNOWN_ERROR';
          const benignErrorCodes = [
            'PLAY_CARD_ERROR',
            'INVALID_DEFENSE_VALUE',
            'WRONG_TURN_ACTION',
            'PASS_TURN_ERROR',
            'INVALID_ACTION'
          ];

          if (benignErrorCodes.includes(errorCode)) {
            console.warn(`⚠️ [${pairLabel}] Bot logic error: ${msg.data?.message} (${errorCode})`);
          } else {
            console.error(`❌ [${pairLabel}] Server error: ${msg.data?.message} (${errorCode})`);
            errorRate.add(1);
          }
          return;
        }
        
        if (msg.type === 'connection_confirmed') {
          gameState = msg.data;
        }
      } catch (e) {
        console.error(`❌ [${pairLabel}] Error parsing message: ${e.message}`);
      }
    });

    socket.on('close', (code) => {
      console.log(`🚪 [${pairLabel}] WS CLOSED code=${code}`);
      if (turnInterval) socket.clearInterval(turnInterval);
      isSocketClosed = true;
    });

    socket.on('error', (e) => {
      console.error(`❌ [${pairLabel}] WS Error: ${e.error()}`);
      errorRate.add(1);
      if (turnInterval) socket.clearInterval(turnInterval);
      isSocketClosed = true;
    });

    function takeTurn() {
      if (!gameState || Object.keys(gameState).length === 0) return;

      const { current_state, status, allowed_actions = [], position, attacker_position, defender_position, cards = [], table_cards = [], room_players = [], trump_suit } = gameState;

      if (current_state === 'LobbyState') {
        if (status === 'unready' && allowed_actions.includes('READY')) {
          console.log(`📤 [${pairLabel}] Sending READY`);
          socket.send(JSON.stringify({ type: 'change_status', data: { status: 'ready' } }));
          messagesSent.add(1);
        }
        return;
      }

      if (current_state === 'PlayRoundWithoutThrowState') {
        const myHand = cards.sort((a, b) => getRankValue(a.rank) - getRankValue(b.rank));
        const isMyTurnToDefend = defender_position === position && allowed_actions.includes('DEFEND');
        const isMyTurnToAttack = attacker_position === position && allowed_actions.includes('ATTACK');

        if (isMyTurnToDefend) {
          const undefended = table_cards.find(p => p.attack_card && !p.defend_card);
          if (undefended) {
            const attCard = undefended.attack_card;
            const defenders = myHand.filter(c => (c.suit === attCard.suit && getRankValue(c.rank) > getRankValue(attCard.rank)) || (c.suit === trump_suit && attCard.suit !== trump_suit)).sort((a, b) => getRankValue(a.rank) - getRankValue(b.rank));
            const higherTrumps = myHand.filter(c => c.suit === trump_suit && getRankValue(c.rank) > getRankValue(attCard.rank)).sort((a, b) => getRankValue(a.rank) - getRankValue(b.rank));
            const defCard = attCard.suit === trump_suit ? higherTrumps[0] : defenders[0];

            if (defCard) {
              socket.send(JSON.stringify({ type: 'play_card', data: { attack_card: attCard, defend_card: defCard } }));
              messagesSent.add(1);
              return;
            }
          }
          if (allowed_actions.includes('TAKE') || allowed_actions.includes('PASS')) {
            socket.send(JSON.stringify({ type: 'pass_turn' }));
            messagesSent.add(1);
            return;
          }
        }

        // 2. ATTACK
        if (isMyTurnToAttack) {
          let cardToPlay = null;
          if (table_cards.length === 0) {
            // Initial attack: play the weakest card.
            cardToPlay = myHand[0];
            if (cardToPlay) {
              console.log(`⚔️ [${pairLabel}] Attacking with ${cardToPlay.rank} of ${cardToPlay.suit}`);
              socket.send(JSON.stringify({ type: 'play_card', data: { attack_card: cardToPlay, defend_card: null } }));
              messagesSent.add(1);
              return;
            }
          }
          // After initial attack, or if no card to attack with, just pass to be safe.
          if (allowed_actions.includes('PASS')) {
            console.log(`⏭️ [${pairLabel}] Attacker is passing.`);
            socket.send(JSON.stringify({ type: 'pass_turn' }));
            messagesSent.add(1);
            return;
          }
        }

        if (allowed_actions.includes('PASS')) {
          socket.send(JSON.stringify({ type: 'pass_turn' }));
          messagesSent.add(1);
          return;
        }
      }
    }
  });

  let waitCounter = 0;
  while (!isSocketClosed && waitCounter < 180) {
    sleep(0.1);
    waitCounter+= 0.1;
  }
}

function getRankValue(rank) {
  const numericValue = parseInt(rank, 10);
  if (!isNaN(numericValue)) {
    return numericValue;
  }
  return 0;
}

export function teardown() {
  console.log('\n=== TEST COMPLETE ===\n');
}
