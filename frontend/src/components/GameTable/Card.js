import React from 'react';
import { getCardSvgPath } from 'utils/cardSvgLinker';

export default function Card({ card, ...props }) {
  return (
    <img
      src={getCardSvgPath(card)}
      alt={`${card.rank} of ${card.suit}`}
      className="card-svg"
      {...props}
    />
  );
}
