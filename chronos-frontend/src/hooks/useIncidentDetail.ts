import { useQuery } from '@tanstack/react-query';
import { api } from '../lib/api';
import type { IncidentReport } from '../types';

interface UseIncidentDetailResult {
  incident: IncidentReport | undefined;
  isLoading: boolean;
  error: Error | null;
  refetch: () => void;
}

export function useIncidentDetail(id: string | undefined): UseIncidentDetailResult {
  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ['incident', id],
    queryFn: () => api.getIncident(id!),
    enabled: !!id,
    staleTime: 10_000,
  });

  return {
    incident: data,
    isLoading,
    error: error as Error | null,
    refetch,
  };
}
