// Helpers for working with the location tree on the client.

import type { LocationTreeNode, LocationType } from "../api/types";

export interface FlatLocation {
  id: string;
  name: string;
  depth: number;
  full_code: string;
  type: LocationType;
}

/** Flatten the nested tree into a depth-tagged list for select inputs. */
export function flattenTree(nodes: LocationTreeNode[], depth = 0): FlatLocation[] {
  return nodes.flatMap((node) => [
    { id: node.id, name: node.name, depth, full_code: node.full_code, type: node.type },
    ...flattenTree(node.children, depth + 1),
  ]);
}

/** Find a node by id anywhere in the tree. */
export function findNode(nodes: LocationTreeNode[], id: string): LocationTreeNode | null {
  for (const node of nodes) {
    if (node.id === id) return node;
    const found = findNode(node.children, id);
    if (found) return found;
  }
  return null;
}

/** Ids of a node and all of its descendants (a location cannot move into these). */
export function subtreeIds(node: LocationTreeNode): Set<string> {
  const ids = new Set<string>([node.id]);
  for (const child of node.children) {
    for (const id of subtreeIds(child)) ids.add(id);
  }
  return ids;
}
