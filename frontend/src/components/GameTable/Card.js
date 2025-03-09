import React from 'react';

function Card({ card, className, draggable, onDragStart }) {
  return (
    <div className={className} draggable={draggable} onDragStart={onDragStart}>
      {card}
    </div>
  );
}

export default Card;
