// Inline line icons (1.75px stroke, rounded) used across the app.

import type { ReactElement } from "react";
import type { LocationType } from "../api/types";

type IconProps = { size?: number };

const base = (size: number) => ({
  width: size,
  height: size,
  viewBox: "0 0 24 24",
  fill: "none",
  stroke: "currentColor",
  strokeWidth: 1.75,
  strokeLinecap: "round" as const,
  strokeLinejoin: "round" as const,
});

export const SearchIcon = ({ size = 22 }: IconProps) => (
  <svg {...base(size)}>
    <circle cx="11" cy="11" r="7" />
    <path d="m21 21-4.3-4.3" />
  </svg>
);

export const TreeIcon = ({ size = 22 }: IconProps) => (
  <svg {...base(size)}>
    <rect x="3" y="3" width="7" height="7" rx="1.5" />
    <path d="M10 6.5h6a2 2 0 0 1 2 2V11M14 14h7v7h-7z" />
    <path d="M6.5 10v4a2 2 0 0 0 2 2H11" />
  </svg>
);

export const TagsIcon = ({ size = 22 }: IconProps) => (
  <svg {...base(size)}>
    <path d="M3 7.5A1.5 1.5 0 0 1 4.5 6h6l8 8-6 6-8-8z" />
    <circle cx="8" cy="11" r="1.3" />
  </svg>
);

export const ScanIcon = ({ size = 22 }: IconProps) => (
  <svg {...base(size)}>
    <path d="M4 8V6a2 2 0 0 1 2-2h2M16 4h2a2 2 0 0 1 2 2v2M20 16v2a2 2 0 0 1-2 2h-2M8 20H6a2 2 0 0 1-2-2v-2" />
    <path d="M4 12h16" />
  </svg>
);

export const BoxIcon = ({ size = 24 }: IconProps) => (
  <svg {...base(size)}>
    <path d="M21 8 12 3 3 8v8l9 5 9-5z" />
    <path d="M3 8l9 5 9-5M12 13v8" />
  </svg>
);

const typeIcons: Record<LocationType, ReactElement> = {
  comodo: <path d="M6 3h12v18H6zM14 12h.5" />,
  armario: <path d="M5 3h14v18H5zM12 3v18M9 11h.5M15 11h.5" />,
  gaveta: <path d="M4 5h16v14H4zM4 12h16M9.5 8.5h5M9.5 15.5h5" />,
  prateleira: <path d="M3 6h18M3 12h18M3 18h18" />,
  caixa: <path d="M21 8 12 3 3 8v8l9 5 9-5zM3 8l9 5 9-5M12 13v8" />,
  organizador: <path d="M4 4h16v16H4zM4 12h16M12 4v16" />,
};

export const LocationTypeIcon = ({
  type,
  size = 20,
}: IconProps & { type: LocationType }) => <svg {...base(size)}>{typeIcons[type]}</svg>;

export const SettingsIcon = ({ size = 22 }: IconProps) => (
  <svg {...base(size)}>
    <path d="M4 6h10M18 6h2M4 12h2M10 12h10M4 18h6M14 18h6" />
    <circle cx="16" cy="6" r="2" />
    <circle cx="8" cy="12" r="2" />
    <circle cx="12" cy="18" r="2" />
  </svg>
);

export const CheckIcon = ({ size = 14 }: IconProps) => (
  <svg {...base(size)} strokeWidth={3}>
    <path d="M20 6 9 17l-5-5" />
  </svg>
);
