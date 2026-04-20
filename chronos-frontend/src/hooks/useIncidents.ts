import { useQuery } from '@tanstack/react-query';
import { api } from '../lib/api';
import type { IncidentReport, DashboardStats } from '../types';

interface UseIncidentsOptions {
  status?: string;
  root_cause?: string;
  limit?: number;
}

interface UseIncidentsResult {
  incidents: IncidentReport[];
  total: number;
  stats: DashboardStats | undefined;
  isLoading: boolean;
  isStatsLoading: boolean;
  error: Error | null;
  refetch: () => void;
}

export function useIncidents(options: UseIncidentsOptions = {}): UseIncidentsResult {
  const {
    data: listData,
    isLoading,
    error,
    refetch,
  } = useQuery({
    queryKey: ['incidents', options],
    queryFn: () => api.listIncidents(options),
    refetchInterval: 30_000,
    staleTime: 15_000,
  });

  const { data: stats, isLoading: isStatsLoading } = useQuery({
    queryKey: ['stats'],
    queryFn: () => api.getStats(),
    refetchInterval: 30_000,
    staleTime: 15_000,
  });

  return {
    incidents: listData?.incidents ?? [],
    total: listData?.total ?? 0,
    stats,
    isLoading,
    isStatsLoading,
    error: error as Error | null,
    refetch,
  };
}
