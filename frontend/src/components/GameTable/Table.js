import React from 'react';
import Card from './Card';

function Table({ playedCards, onDrop, onDragOver }) {
    return (
      <div 
        className="table__center-area"
        onDrop={onDrop}
        onDragOver={onDragOver}
      >
        <div className="table__played-cards">
          {playedCards.length > 0 
            ? playedCards.map((card, index) => (
                <Card 
                  key={index} 
                  card={card} 
                  className="card table__card" 
                  draggable={false} 
                />
              )) 
            : "Карты на столе"}
        </div>
      </div>
    );
  }

export default Table;
