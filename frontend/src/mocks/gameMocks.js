// Генерируем случайные аватары для игроков
const generateAvatar = (seed) => `https://api.dicebear.com/7.x/avataaars/svg?seed=${seed}`;

export const mockPlayers = [
  {
    id: "1",
    name: "Player 1",
    cards: 6,
    position: 1,
    status: 'ready',
    profileImage: generateAvatar('player1')
  },
  {
    id: "2",
    name: "Player 2",
    cards: 5,
    position: 3,
    status: 'unready',
    profileImage: generateAvatar('player2')
  },
  {
    id: "3",
    name: "Player 3",
    cards: 7,
    position: 6,
    status: 'unready',
    profileImage: generateAvatar('player3')
  },
  {
    id: "4",
    name: "Player 4",
    cards: 5,
    position: 2,
    status: 'unready',
    profileImage: generateAvatar('player4')
  },
];

export const mockYourCards = [
  { rank: 'ace', suit: 'spades' },
  { rank: '6', suit: 'spades' },
  { rank: '7', suit: 'spades' },
  { rank: '8', suit: 'spades' },
  { rank: '9', suit: 'spades' },
  { rank: 'queen', suit: 'spades' },
  { rank: 'jack', suit: 'spades' },
];

export const mockTableCards = [
  { card: { rank: 'ace', suit: 'diamonds' }, playerId: "1" },
  { card: { rank: 'king', suit: 'hearts' }, playerId: "2" },
];

export const mockGameState = {
  deckCount: 15,
  trumpSuit: 'hearts',
  currentPlayerPosition: 4,
  maxPositions: 6,
  playerId: "0",
  totalDeckCards: 36,
};

// Дополнительные моки для разных сценариев
export const mockGameScenarios = {
  gameStart: {
    players: mockPlayers.map(p => ({ ...p, cards: 6, status: 'unready' })),
    yourCards: mockYourCards.slice(0, 6),
    tableCards: [],
    deckCount: 24,
  },

  midGame: {
    players: mockPlayers,
    yourCards: mockYourCards,
    tableCards: mockTableCards,
    deckCount: 15,
  },

  endGame: {
    players: mockPlayers.map(p => ({ ...p, cards: 1, status: 'unready' })),
    yourCards: [mockYourCards[0]],
    tableCards: mockTableCards.slice(0, 1),
    deckCount: 0,
  }
};
