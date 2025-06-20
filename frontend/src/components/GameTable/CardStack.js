import React, { useState } from "react";
import "assets/styles/game/CardStack.css";

export default function CardStack({
  count = 0,
  backImage,
  maxVisible = 6,
  dense = false,
  overdraftShow = true,
  rotateTooltip = false,
  tootipStartValue = 0
}) {
  const visible = Math.min(count, maxVisible);
  const [hover, setHover] = useState(false);

  // Если нет карт, не рендерим компонент
  if (count <= 0) {
    return null;
  }

  return (
    <div
      className={`card-stack${dense ? " card-stack--dense" : ""}`}
      onMouseEnter={() => setHover(true)}
      onMouseLeave={() => setHover(false)}
      style={{ position: "relative" }}
    >
      {Array.from({ length: visible }).map((_, i) => (
        <img
          key={i}
          src={backImage}
          alt="card"
          className="card-stack__card"
          style={{ zIndex: i }}
        />
      ))}
      {count > maxVisible && overdraftShow && (
        <span className="card-stack__more">+{count - maxVisible}</span>
      )}
      {hover && (
        <div
          className={
            "card-stack__tooltip" +
            (rotateTooltip ? " card-stack__tooltip--rotated" : "")
          }
        >
          Всего карт: {count + tootipStartValue}
        </div>
      )}
    </div>
  );
}
