// Thin fetch wrapper around the backend API.

import type {
  AppConfig,
  AuthStatus,
  BadgePrintRequest,
  Category,
  CategoryCreate,
  ImportResult,
  Item,
  ItemCreate,
  ItemUpdate,
  LocationCreate,
  LocationRead,
  LocationTreeNode,
  LocationUpdate,
  Photo,
  PrinterHealth,
  PrinterStatus,
  PrintResult,
  SearchResults,
} from "./types";

const BASE = "/api";

/** Error carrying the HTTP status and the backend's detail message. */
export class ApiError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

// Called when any API request gets a 401 (session expired); the PIN gate
// registers itself here so the lock screen reappears.
let unauthorizedHandler: (() => void) | null = null;

/** Register the callback invoked when the backend rejects the session. */
export function setUnauthorizedHandler(handler: (() => void) | null): void {
  unauthorizedHandler = handler;
}

function notifyUnauthorized(path: string, status: number): void {
  if (status === 401 && !path.startsWith("/auth")) unauthorizedHandler?.();
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });
  if (!response.ok) {
    notifyUnauthorized(path, response.status);
    let detail = response.statusText;
    try {
      detail = (await response.json()).detail ?? detail;
    } catch {
      // response had no JSON body; keep the status text.
    }
    throw new ApiError(response.status, detail);
  }
  if (response.status === 204) {
    return undefined as T;
  }
  return response.json() as Promise<T>;
}

async function upload<T>(
  path: string,
  file: File,
  extra: Record<string, string> = {},
): Promise<T> {
  const form = new FormData();
  form.append("file", file);
  for (const [key, value] of Object.entries(extra)) form.append(key, value);
  const response = await fetch(`${BASE}${path}`, { method: "POST", body: form });
  if (!response.ok) {
    notifyUnauthorized(path, response.status);
    let detail = response.statusText;
    try {
      detail = (await response.json()).detail ?? detail;
    } catch {
      // no JSON body; keep the status text.
    }
    throw new ApiError(response.status, detail);
  }
  return response.json() as Promise<T>;
}

export const api = {
  getTree: () => request<LocationTreeNode[]>("/locations/tree"),
  getLocation: (id: string) => request<LocationRead>(`/locations/${id}`),
  createLocation: (data: LocationCreate) =>
    request<LocationRead>("/locations", { method: "POST", body: JSON.stringify(data) }),
  updateLocation: (id: string, data: LocationUpdate) =>
    request<LocationRead>(`/locations/${id}`, { method: "PATCH", body: JSON.stringify(data) }),
  deleteLocation: (id: string, force = false) =>
    request<void>(`/locations/${id}?force=${force}`, { method: "DELETE" }),

  listItems: (params: { locationId?: string; categoryId?: string } = {}) => {
    const query = new URLSearchParams();
    if (params.locationId) query.set("location_id", params.locationId);
    if (params.categoryId) query.set("category_id", params.categoryId);
    const suffix = query.toString() ? `?${query.toString()}` : "";
    return request<Item[]>(`/items${suffix}`);
  },
  getItem: (id: string) => request<Item>(`/items/${id}`),
  createItem: (data: ItemCreate) =>
    request<Item>("/items", { method: "POST", body: JSON.stringify(data) }),
  updateItem: (id: string, data: ItemUpdate) =>
    request<Item>(`/items/${id}`, { method: "PATCH", body: JSON.stringify(data) }),
  deleteItem: (id: string) => request<void>(`/items/${id}`, { method: "DELETE" }),

  uploadItemPhoto: (itemId: string, file: File) =>
    upload<Photo>(`/items/${itemId}/photos`, file),
  uploadLocationPhoto: (locationId: string, file: File) =>
    upload<Photo>(`/locations/${locationId}/photos`, file),
  deletePhoto: (id: string) => request<void>(`/photos/${id}`, { method: "DELETE" }),

  listCategories: () => request<Category[]>("/categories"),
  createCategory: (data: CategoryCreate) =>
    request<Category>("/categories", { method: "POST", body: JSON.stringify(data) }),

  search: (query: string, categoryId?: string) => {
    const params = new URLSearchParams({ q: query });
    if (categoryId) params.set("category_id", categoryId);
    return request<SearchResults>(`/search?${params.toString()}`);
  },

  importInventory: (data: unknown) =>
    request<ImportResult>("/import", { method: "POST", body: JSON.stringify(data) }),

  getConfig: () => request<AppConfig>("/config"),

  // PIN authentication (session cookie set/cleared by the backend).
  authStatus: () => request<AuthStatus>("/auth/status"),
  login: (pin: string) =>
    request<void>("/auth/login", { method: "POST", body: JSON.stringify({ pin }) }),
  logout: () => request<void>("/auth/logout", { method: "POST" }),
  changePin: (data: { current_pin?: string; new_pin: string }) =>
    request<void>("/auth/pin", { method: "POST", body: JSON.stringify(data) }),

  // Thermal printing (SLP650). The backend proxies the print server;
  // the printer API key never reaches the browser.
  printerStatus: () => request<PrinterStatus>("/print/status"),
  printerHealth: () => request<PrinterHealth>("/print/health"),
  printBadge: (data: BadgePrintRequest) =>
    request<PrintResult>("/print/badge", { method: "POST", body: JSON.stringify(data) }),
  printImage: (file: File, copies = 1) =>
    upload<PrintResult>("/print/image", file, { copies: String(copies) }),
  printLocationLabel: (locationId: string, copies = 1) =>
    request<PrintResult>(`/print/locations/${locationId}`, {
      method: "POST",
      body: JSON.stringify({ qr_base_url: window.location.origin, copies }),
    }),
};

/** URL of the server-rendered label preview PNG for a location. */
export function labelPreviewUrl(locationId: string): string {
  const origin = encodeURIComponent(window.location.origin);
  return `${BASE}/print/locations/${locationId}/preview.png?qr_base_url=${origin}`;
}

/** URLs for the file-download endpoints (used with anchor links). */
export const exportUrls = {
  json: `${BASE}/export`,
  csv: `${BASE}/export.csv`,
};
