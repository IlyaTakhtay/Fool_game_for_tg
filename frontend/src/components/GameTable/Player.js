import React from 'react';
import Card from './Card';

function Player({ player, className }) {
  const statusClass = player.status === 'ready' ? 'border-green' : 'border-red';
  return (
    <div className={className}>
      <div className="player__info">
        <img src={player.profileImage} alt={`Профиль ${player.name}`} className={`player__profile-image ${statusClass}`} />
        <p>{player.name}</p>
      </div>
      <div className="player__cards">
        {Array.from({ length: player.cards }, (_, index) => (
          <Card key={index} className="card--back" />
        ))}
      </div>
    </div>
  );
}

export default Player;
