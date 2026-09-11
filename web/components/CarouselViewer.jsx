import React, { useState, useRef } from "react";
import { media } from "../lib";
import { Icon } from "./ui";

export default function CarouselViewer({ pack, onEdit }) {
  const touchStart = useRef(null);
  const [index, setIndex] = useState(0);
  const [overlay, setOverlay] = useState(false);
  const slot = pack.slots[index] || pack.slots[0];
  const move = (n) =>
    setIndex((i) => (i + n + pack.slots.length) % pack.slots.length);
  return (
    <section
      className="carousel-viewer"
      aria-label="Lecteur du carrousel"
      onKeyDown={(e) => {
        if (e.target.tagName === "INPUT") return;
        if (e.key === "ArrowRight") {
          e.preventDefault();
          move(1);
        }
        if (e.key === "ArrowLeft") {
          e.preventDefault();
          move(-1);
        }
      }}
    >
      <div
        className="viewer-stage"
        onTouchStart={(e) => {
          touchStart.current = [e.touches[0].clientX, e.touches[0].clientY];
        }}
        onTouchEnd={(e) => {
          if (!touchStart.current) return;
          const [x, y] = touchStart.current;
          const dx = e.changedTouches[0].clientX - x;
          const dy = e.changedTouches[0].clientY - y;
          if (Math.abs(dx) > 45 && Math.abs(dx) > Math.abs(dy) * 1.5)
            move(dx < 0 ? 1 : -1);
          touchStart.current = null;
        }}
      >
        <button
          className="viewer-arrow"
          aria-label="Image précédente"
          onClick={() => move(-1)}
        >
          ‹
        </button>
        <div
          className="viewer-photo"
          style={{ aspectRatio: pack.ratio.replace(":", " / ") }}
        >
          {slot.active ? (
            <button
              aria-label={`Ouvrir ${slot.subject}`}
              onClick={() => onEdit(slot.key)}
            >
              <img src={media(slot.active)} alt={slot.subject} />
            </button>
          ) : (
            <div className="image-placeholder">
              <Icon name="clock" />
              <p>{slot.subject}</p>
              <small>Cette image attend sa génération.</small>
            </div>
          )}
          {overlay && (
            <div className="preview-overlay" aria-hidden="true">
              <span>realify / aperçu</span>
              <div>
                ♡<br />↗<br />
                ···
              </div>
              <p>
                {pack.post?.title || pack.title}
                <small>Repères indicatifs · vérifier dans TikTok</small>
              </p>
            </div>
          )}
        </div>
        <button
          className="viewer-arrow"
          aria-label="Image suivante"
          onClick={() => move(1)}
        >
          ›
        </button>
      </div>
      <div className="viewer-caption">
        <div>
          <span className="eyebrow">
            IMAGE {index + 1} / {pack.slots.length}
          </span>
          <h3>{slot.subject}</h3>
        </div>
        <div className="viewer-actions">
          <button
            className="text-button"
            aria-pressed={overlay}
            onClick={() => setOverlay(!overlay)}
          >
            Repères TikTok
          </button>
          {slot.active && (
            <a
              className="text-button"
              href={`${media(slot.active)}?download=1`}
            >
              <Icon name="down" />
              Cette image
            </a>
          )}
        </div>
      </div>
      <div className="viewer-strip">
        {pack.slots.map((s, i) => (
          <button
            key={s.key}
            aria-label={`Voir l’image ${i + 1}`}
            aria-pressed={index === i}
            onClick={() => setIndex(i)}
          >
            {s.active ? (
              <img src={media(s.active)} alt="" />
            ) : (
              <Icon name="clock" />
            )}
            <span>{i + 1}</span>
          </button>
        ))}
      </div>
    </section>
  );
}
