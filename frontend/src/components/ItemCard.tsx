// A single item row: thumbnail, name, location tag, quantity, categories.

import { Link } from "react-router-dom";
import type { Item } from "../api/types";
import { BoxIcon } from "./Icons";
import { Tag } from "./Tag";

export function ItemCard({ item }: { item: Item }) {
  return (
    <div className="item-card">
      {item.photos.length > 0 ? (
        <img className="thumb" src={item.photos[0].thumb_url} alt="" loading="lazy" />
      ) : (
        <div className="thumb" aria-hidden="true">
          <BoxIcon size={24} />
        </div>
      )}
      <div className="body">
        <Link to={`/itens/${item.id}`} className="name">
          {item.name}
        </Link>
        <div className="meta">
          <Link to={`/locais/${item.location.id}`} aria-label={`Abrir ${item.location.name}`}>
            <Tag code={item.location.full_code} />
          </Link>
          {item.quantity !== 1 && <span className="qty">×{item.quantity}</span>}
        </div>
        {item.categories.length > 0 && (
          <div className="meta">
            {item.categories.map((category) => (
              <span key={category.id} className="catchip" style={{ cursor: "default" }}>
                <span className="dot" style={{ background: category.color }} />
                {category.name}
              </span>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
