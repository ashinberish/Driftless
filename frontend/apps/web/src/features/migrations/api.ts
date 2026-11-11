import { ApiError, type MigrationCreate } from "@driftless/api-client";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { api } from "@/shared/api";

export const migrationKeys = {
  all: ["migrations"] as const,
  list: () => [...migrationKeys.all, "list"] as const,
  detail: (id: string) => [...migrationKeys.all, "detail", id] as const,
  assessment: (id: string) => [...migrationKeys.all, "assessment", id] as const,
};

export function useMigrations() {
  return useQuery({ queryKey: migrationKeys.list(), queryFn: () => api.migrations.list() });
}

export function useMigration(id: string) {
  return useQuery({ queryKey: migrationKeys.detail(id), queryFn: () => api.migrations.get(id) });
}

/** Latest assessment, or ``null`` when the migration has never been checked. */
export function useLatestAssessment(id: string) {
  return useQuery({
    queryKey: migrationKeys.assessment(id),
    queryFn: async () => {
      try {
        return await api.migrations.latestAssessment(id);
      } catch (error) {
        if (error instanceof ApiError && error.status === 404) return null;
        throw error;
      }
    },
  });
}

export function useRunAssessment(id: string) {
  const client = useQueryClient();
  return useMutation({
    mutationFn: () => api.migrations.assess(id),
    onSuccess: (run) => {
      client.setQueryData(migrationKeys.assessment(id), run);
      // Status changed; the assessment itself is already fresh, so don't refetch it.
      void client.invalidateQueries({ queryKey: migrationKeys.list() });
      void client.invalidateQueries({ queryKey: migrationKeys.detail(id) });
    },
  });
}

/** Create a draft, then assess it right away — the "Continue" button on Connect. */
export function useCreateAndAssess() {
  const client = useQueryClient();
  return useMutation({
    mutationFn: async (body: MigrationCreate) => {
      const migration = await api.migrations.create(body);
      const run = await api.migrations.assess(migration.id);
      return { migration, run };
    },
    onSuccess: ({ migration, run }) => {
      client.setQueryData(migrationKeys.assessment(migration.id), run);
      void client.invalidateQueries({ queryKey: migrationKeys.list() });
    },
  });
}
