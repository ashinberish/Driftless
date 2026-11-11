import type { ConnectionCreate, ConnectionSpec } from "@driftless/api-client";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { api } from "@/shared/api";

export const connectionKeys = {
  all: ["connections"] as const,
  list: () => [...connectionKeys.all, "list"] as const,
  detail: (id: string) => [...connectionKeys.all, "detail", id] as const,
  connectors: ["connectors"] as const,
};

export function useConnectors() {
  return useQuery({
    queryKey: connectionKeys.connectors,
    queryFn: () => api.connectors.list(),
    staleTime: Infinity, // engine list changes only on deploy
  });
}

export function useConnections() {
  return useQuery({ queryKey: connectionKeys.list(), queryFn: () => api.connections.list() });
}

export function useConnection(id: string) {
  return useQuery({ queryKey: connectionKeys.detail(id), queryFn: () => api.connections.get(id) });
}

export function useCreateConnection() {
  const client = useQueryClient();
  return useMutation({
    mutationFn: (body: ConnectionCreate) => api.connections.create(body),
    onSuccess: () => client.invalidateQueries({ queryKey: connectionKeys.all }),
  });
}

export function useDeleteConnection() {
  const client = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => api.connections.remove(id),
    onSuccess: () => client.invalidateQueries({ queryKey: connectionKeys.all }),
  });
}

/** Test settings that are not saved yet (Connect screen). */
export function useTestSpec() {
  return useMutation({ mutationFn: (spec: ConnectionSpec) => api.connections.testSpec(spec) });
}

export function useTestConnection(id: string) {
  return useMutation({ mutationFn: () => api.connections.test(id) });
}

export function useDiscover(id: string) {
  return useMutation({ mutationFn: (schemas?: string[]) => api.connections.discover(id, schemas) });
}
