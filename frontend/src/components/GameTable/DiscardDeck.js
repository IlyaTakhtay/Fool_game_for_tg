import React, { useMemo } from "react";
import 'assets/styles/game/DiscardDeck.css';

export default function DiscardDeck({ count, cardImage, width = 400, height = 300 }) {
  // Мемоизируем генерацию карт, чтобы они не пересоздавались при каждом рендере
  const cards = useMemo(() => {
    return Array.from({ length: count }).map((_, i) => {
      const left = Math.random() * (width + 30);
      const top = Math.random() * (height + 10);
      const rotate = Math.random() * 60 - 30;
      return { left, top, rotate };
    });
  }, [count, width, height]); // Пересоздаем только если изменились эти параметры

  return (
    <div
      className="discard-deck"
      style={{
        width,
        height,
      }}
    >
      {cards.map((card, i) => (
        <img
          key={i}
          src={cardImage}
          alt="card"
          className="discard-deck__card"
          style={{
            top: `${card.top}px`,
            transform: `rotate(${card.rotate}deg)`,
          }}
        />
      ))}
    </div>
  );
}
