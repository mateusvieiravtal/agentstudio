import {
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";
import { api } from "./client";
import type { Agent, AgentCreate } from "@/types";

const KEY = ["agents"] as const;

export function useAgents() {
  return useQuery({
    queryKey: KEY,
    queryFn: () => api.get<Agent[]>("/agents"),
  });
}

export function useCreateAgent() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: AgentCreate) => api.post<Agent>("/agents", body),
    onSuccess: () => qc.invalidateQueries({ queryKey: KEY }),
  });
}

export function useUpdateAgent() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, body }: { id: string; body: Partial<AgentCreate> }) =>
      api.patch<Agent>(`/agents/${id}`, body),
    onSuccess: () => qc.invalidateQueries({ queryKey: KEY }),
  });
}

export function useDeleteAgent() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => api.del(`/agents/${id}`),
    onSuccess: () => qc.invalidateQueries({ queryKey: KEY }),
  });
}
