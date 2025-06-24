import React from 'react';
import Card from './Card';
import 'assets/styles/game/Table.css';

function Table({ playedCards, isDefender, isAttacker }) {
  const hasCardsOnTable = playedCards && playedCards.length > 0;
  const showAttackDropZone = isAttacker;

  return (
    <div className="table__center-area">
      {showAttackDropZone && (
        <div
          className="table__new-attack-dropzone table__new-attack-dropzone--active"
          data-is-attack-zone="true"
        >
          {!hasCardsOnTable && 'Бросить карту'}
        </div>
      )}

      <div className="table__played-cards">
        {playedCards && playedCards.map((pair, idx) => {
          if (!pair || !pair.base) return null;
          
          const canDropOnThisCard = isDefender && !pair.cover;
          
          return (
            <div
              key={`${pair.base.rank}-${pair.base.suit}-${idx}`}
              className={`table-card-slot ${canDropOnThisCard ? 'table-card-slot--can-drop' : ''}`}
              data-base-card={canDropOnThisCard ? JSON.stringify(pair.base) : undefined}
            >
              <Card
                card={pair.base}
                draggable={false}
                className="card--face card--on-table"
              />
              {pair.cover && (
                <Card
                  card={pair.cover}
                  draggable={false}
                  className="card--face card--on-table card--cover"
                />
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

export default Table;
