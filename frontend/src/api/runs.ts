import { useMutation, useQuery } from "@tanstack/react-query";
import { api } from "./client";
import type { Run } from "@/types";

export function useStartRun() {
  return useMutation({
    mutationFn: (body: { pipeline_id: string; input: string }) =>
      api.post<Run>("/runs", body),
  });
}

export function useRun(id: string | undefined) {
  return useQuery({
    queryKey: ["runs", id],
    queryFn: () => api.get<Run>(`/runs/${id}`),
    enabled: !!id,
  });
}

export function useResumeRun() {
  return useMutation({
    mutationFn: ({ id, input }: { id: string; input: string }) =>
      api.post<Run>(`/runs/${id}/resume`, { input }),
  });
}

export function runStreamUrl(runId: string): string {
  return `/api/v1/runs/${runId}/stream`;
}
