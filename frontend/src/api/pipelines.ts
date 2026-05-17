import {
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";
import { api } from "./client";
import type { Pipeline, PipelineCreate } from "@/types";

const KEY = ["pipelines"] as const;

export function usePipelines() {
  return useQuery({
    queryKey: KEY,
    queryFn: () => api.get<Pipeline[]>("/pipelines"),
  });
}

export function usePipeline(id: string | undefined) {
  return useQuery({
    queryKey: ["pipelines", id],
    queryFn: () => api.get<Pipeline>(`/pipelines/${id}`),
    enabled: !!id,
  });
}

export function useCreatePipeline() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: PipelineCreate) => api.post<Pipeline>("/pipelines", body),
    onSuccess: () => qc.invalidateQueries({ queryKey: KEY }),
  });
}

export function useUpdatePipeline() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, body }: { id: string; body: Partial<PipelineCreate> }) =>
      api.patch<Pipeline>(`/pipelines/${id}`, body),
    onSuccess: (_, vars) => {
      qc.invalidateQueries({ queryKey: KEY });
      qc.invalidateQueries({ queryKey: ["pipelines", vars.id] });
    },
  });
}

export function useDeletePipeline() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => api.del(`/pipelines/${id}`),
    onSuccess: () => qc.invalidateQueries({ queryKey: KEY }),
  });
}
