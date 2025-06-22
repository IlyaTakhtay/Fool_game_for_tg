import React from "react";
import Player from "./Player";
import "assets/styles/game/PlayerPositionOnTable.css";


// players: массив игроков
// Обновлённая функция преобразования позиций
function fromAbsoluteToLocalPosition(position, maxPositions, myPosition) {
    return (position - myPosition + maxPositions) % maxPositions;
}

export default function PlayerPositionsOnTable({
    players,
    maxPositions = 6,
    currentPlayerPosition,
    attackerPosition,
    defenderPosition
}) {
    console.log('PlayerPositionsOnTable received:', {
        players,
        maxPositions,
        currentPlayerPosition,
        attackerPosition,
        defenderPosition
    });
    // Сортируем игроков по локальным позициям
    const sortedPlayers = [...players].sort((a, b) =>
        fromAbsoluteToLocalPosition(a.position, maxPositions, currentPlayerPosition) -
        fromAbsoluteToLocalPosition(b.position, maxPositions, currentPlayerPosition)
    );

    return (
        <div className="card-table__players">
            {sortedPlayers.map(player => {
                const localPosition = fromAbsoluteToLocalPosition(
                    player.position,
                    maxPositions,
                    currentPlayerPosition
                );

                const isAttacker = player.position === attackerPosition;
                const isDefender = player.position === defenderPosition;

                return (
                    <Player
                        key={player.id}
                        player={player}
                        className={`player player--${localPosition + 1}`}
                        isCurrent={player.position === currentPlayerPosition}
                        isAttacker={isAttacker}
                        isDefender={isDefender}
                    />
                );
            })}
        </div>
    );
}
