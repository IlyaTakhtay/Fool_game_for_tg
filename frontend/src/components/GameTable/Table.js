import React from 'react';
import Card from './Card';

function Table({ playedCards, onDrop, onDragOver }) {
  console.log('Table render playedCards:', playedCards);
  return (
    <div className="table__center-area">
      {/* Drop-зона для новой атаки (если нужно) */}
      <div
        className="table__new-attack-dropzone"
        onDrop={e => onDrop(e, null)}
        onDragOver={onDragOver}
        style={{ minHeight: 40, marginBottom: 8, border: '1px dashed #aaa', textAlign: 'center', color: '#888' }}
      >
        Кинуть новую карту на стол
      </div>
      <div className="table__played-cards">
        {playedCards && playedCards.map((pair, idx) => {
          if (!pair || !pair.base) return null;
          return (
            <div
              key={`${pair.base.rank}-${pair.base.suit}-${idx}`}
              className="table-card-slot"
              onDrop={pair.cover ? undefined : (e) => onDrop(e, pair.base)}
              onDragOver={pair.cover ? undefined : onDragOver}
              style={{ position: 'relative', display: 'inline-block', margin: 8 }}
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
                  style={{
                    position: 'absolute',
                    left: 20,
                    top: 20,
                    zIndex: 2
                  }}
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
