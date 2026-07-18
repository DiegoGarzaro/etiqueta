// TypeScript mirrors of the backend Pydantic schemas.

export type LocationType =
  | "comodo"
  | "armario"
  | "gaveta"
  | "prateleira"
  | "caixa"
  | "organizador";

export interface PathSegment {
  id: string;
  name: string;
  code: string;
}

export interface LocationRead {
  id: string;
  name: string;
  type: LocationType;
  parent_id: string | null;
  code: string;
  full_code: string;
  path: PathSegment[];
  notes: string | null;
  direct_item_count: number;
  total_item_count: number;
  photos: Photo[];
}

export interface LocationTreeNode extends LocationRead {
  children: LocationTreeNode[];
}

export interface Category {
  id: string;
  name: string;
  color: string;
  icon: string | null;
  item_count: number;
}

export interface Photo {
  id: string;
  url: string;
  thumb_url: string;
  content_type: string;
  width: number;
  height: number;
}

export interface LocationSummary {
  id: string;
  name: string;
  code: string;
  full_code: string;
  path: PathSegment[];
}

export interface Item {
  id: string;
  name: string;
  description: string | null;
  quantity: number;
  notes: string | null;
  location: LocationSummary;
  categories: Category[];
  photos: Photo[];
}

export interface SearchResults {
  query: string;
  total: number;
  items: Item[];
}

export interface LocationCreate {
  name: string;
  type: LocationType;
  parent_id: string | null;
  notes?: string | null;
}

export interface ItemCreate {
  name: string;
  description?: string | null;
  quantity: number;
  notes?: string | null;
  location_id: string;
  category_ids: string[];
}

export interface ItemUpdate {
  name?: string;
  description?: string | null;
  quantity?: number;
  notes?: string | null;
  location_id?: string;
  category_ids?: string[];
}

export interface LocationUpdate {
  name?: string;
  notes?: string | null;
  parent_id?: string | null;
}

export interface CategoryCreate {
  name: string;
  color: string;
  icon?: string | null;
}

export interface ImportResult {
  categories: number;
  locations: number;
  items: number;
  photos: number;
}

export interface AppConfig {
  public_base_url: string | null;
}

export interface AuthStatus {
  auth_required: boolean;
  authenticated: boolean;
}

export interface PrinterStatus {
  base_url: string;
  key_configured: boolean;
  ok: boolean | null;
  error: string | null;
}

export interface PrinterHealth {
  ok: boolean;
  [key: string]: unknown;
}

export interface PrintResult {
  engine: string;
  [key: string]: unknown;
}

export interface BadgePrintRequest {
  name: string;
  company?: string;
  qr_data?: string;
  copies?: number;
}

export const LOCATION_TYPE_LABELS: Record<LocationType, string> = {
  comodo: "Cômodo",
  armario: "Armário",
  gaveta: "Gaveta",
  prateleira: "Prateleira",
  caixa: "Caixa",
  organizador: "Organizador",
};
