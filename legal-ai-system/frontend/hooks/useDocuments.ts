'use client';

import { useState, useCallback } from 'react';
import { Document } from '@/lib/types';
import { listDocuments } from '@/lib/api';

export const useDocuments = () => {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchDocuments = useCallback(async (skip = 0, limit = 10) => {
    try {
      setLoading(true);
      setError(null);
      const data = await listDocuments(skip, limit);
      setDocuments(data);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to fetch documents';
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  }, []);

  return { documents, loading, error, fetchDocuments };
};
