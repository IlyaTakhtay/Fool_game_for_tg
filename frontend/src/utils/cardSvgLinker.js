/**
 * Возвращает путь к SVG-файлу карты по объекту { rank, suit }
 * @param {Object} card - объект карты
 * @param {string|number} card.rank - ранг ('9', '10', 'jack', 'queen', 'king', 'ace')
 * @param {string} card.suit - масть ('hearts', 'spades', 'clubs', 'diamonds')
 * @returns {string} относительный путь к SVG-файлу
 */
export function getCardSvgPath({ rank, suit }) {
  if (!rank || !suit) {
    return require('assets/images/imperial_back.png'); // заглушка, если ошибка в параметрах TODO: сделать кастом заглушку
  }
  // Приведение ранга к нужному виду
  const rankMap = {
    'J': 'jack',
    'Q': 'queen',
    'K': 'king',
    'A': 'ace',
    'j': 'jack',
    'q': 'queen',
    'k': 'king',
    'a': 'ace',
    'Jack': 'jack',
    'Queen': 'queen',
    'King': 'king',
    'Ace': 'ace',
    'jack': 'jack',
    'queen': 'queen',
    'king': 'king',
    'ace': 'ace',
    '11': 'jack',
    '12': 'queen',
    '13': 'king',
    '14': 'ace',
    11: 'jack',
    12: 'queen',
    13: 'king',
    14: 'ace',
    9: '9',
    10: '10',
    '9': '9',
    '10': '10'
  };

  // Приведение масти к нужному виду
  const suitMap = {
    'S': 'spades',
    'H': 'hearts',
    'D': 'diamonds',
    'C': 'clubs',
    's': 'spades',
    'h': 'hearts',
    'd': 'diamonds',
    'c': 'clubs',
    'Spades': 'spades',
    'Hearts': 'hearts',
    'Diamonds': 'diamonds',
    'Clubs': 'clubs',
    'spades': 'spades',
    'hearts': 'hearts',
    'diamonds': 'diamonds',
    'clubs': 'clubs'
  };

  const normRank = rankMap[rank] || String(rank).toLowerCase();
  const normSuit = suitMap[suit] || String(suit).toLowerCase();

  // Собираем путь (если svg-файлы в public/assets/images/cards)
  return require(`assets/images/cards/English_pattern_${normRank}_of_${normSuit}.svg`);
}
