// A colored category chip; clickable when onClick is provided.

import type { Category } from "../api/types";

interface Props {
  category: Category;
  active?: boolean;
  onClick?: () => void;
  showCount?: boolean;
}

export function CategoryChip({ category, active = false, onClick, showCount = false }: Props) {
  return (
    <button
      type="button"
      className={active ? "catchip active" : "catchip"}
      onClick={onClick}
      style={onClick ? undefined : { cursor: "default" }}
    >
      <span className="dot" style={{ background: category.color }} />
      {category.name}
      {showCount && <span className="qty">{category.item_count}</span>}
    </button>
  );
}
