import { useQuery } from "@tanstack/react-query";

import { api } from "@/shared/api";

export const connectionKeys = {
  all: ["connections"] as const,
  list: () => [...connectionKeys.all, "list"] as const,
};

export function useConnections() {
  return useQuery({ queryKey: connectionKeys.list(), queryFn: () => api.connections.list() });
}
