'use client';

import { useState, useEffect } from 'react';
import { Card, Button, Alert } from '@/components/UI';
import { listDocuments, getDraftsForDocument, deleteDraft, deleteDocument } from '@/lib/api';
import { formatDate } from '@/lib/utils';
import { Draft } from '@/lib/types';

type FilterType = 'all' | 'documents' | 'drafts';

interface HistoryItem {
  id: string;
  type: 'document' | 'draft';
  title: string;
  details: string;
  timestamp: Date;

  documentId?: number;
  draftId?: number;
  draft?: Draft;
}

export default function HistorySection({
  onViewDetails,
  onViewDocumentDetails,
  onUpdate,
  onDeleteDocument,
}: {
  onViewDetails: (documentId: number, draftId: number, draft: Draft) => void;
  onViewDocumentDetails: (documentId: number) => void;
  onUpdate: (documentId: number, draftId: number, draft: Draft) => void;
  onDeleteDocument: (documentId: number) => void;
}) {
  const [items, setItems] = useState<HistoryItem[]>([]);
  const [filter, setFilter] = useState<FilterType>('all');
  const [loading, setLoading] = useState(true);
  const [refreshKey, setRefreshKey] = useState(0); // ✅ Add refresh key to force reload

  useEffect(() => {
    const loadHistory = async () => {
      try {
        setLoading(true);
        const documents = await listDocuments(0, 50);
        const historyItems: HistoryItem[] = [];

        // Add documents
        if (filter === 'all' || filter === 'documents') {
          documents.forEach((doc) => {
            historyItems.push({
              id: `doc-${doc.id}`,
              type: 'document',
              title: `Document: ${doc.filename}`,
              details: `Status: ${doc.processing_status} | Uploaded: ${formatDate(doc.created_at)}`,
              timestamp: new Date(doc.created_at),
              documentId: doc.id,
            });
          });
        }

        // Add drafts - PROPERLY populate documentId and draftId so buttons appear
        if (filter === 'all' || filter === 'drafts') {
          for (const doc of documents) {
            try {
              const drafts = await getDraftsForDocument(doc.id);
              drafts.forEach((draft) => {
                historyItems.push({
                  id: `draft-${draft.id}`,
                  type: 'draft',
                  title: `Draft (${draft.draft_type}): ${draft.draft_content?.substring(0, 50) || 'Untitled draft'}...`,
                  details: `Grounding: ${(draft.grounding_score * 100).toFixed(1)}% | Completeness: ${(draft.completeness_score * 100).toFixed(1)}% | Created: ${formatDate(draft.created_at)}`,
                  timestamp: new Date(draft.created_at),
                  documentId: doc.id,  // ✅ Set documentId for drafts
                  draftId: draft.id,   // ✅ Set draftId for drafts
                  draft: draft,        // ✅ Include full draft object
                });
              });
            } catch (error) {
              console.warn(`Failed to load drafts for doc ${doc.id}:`, error);
            }
          }
        }

        historyItems.sort((a, b) => b.timestamp.getTime() - a.timestamp.getTime());
        setItems(historyItems);
      } catch (error) {
        console.error('Failed to load history:', error);
      } finally {
        setLoading(false);
      }
    };

    loadHistory();
  }, [filter, refreshKey]); // ✅ Depend on refreshKey to reload when it changes

  const filters: { value: FilterType; label: string }[] = [
    { value: 'all', label: 'All Items' },
    { value: 'documents', label: 'Documents' },
    { value: 'drafts', label: 'Drafts' },
  ];

  const [error, setError] = useState<string | null>(null);

  const handleDelete = async (item: HistoryItem) => {
    try {
      setError(null);
      if (item.type === 'draft' && item.draftId && item.documentId) {
        await deleteDraft(item.draftId);
        console.log(`Successfully deleted draft ${item.draftId}`);
      } else if (item.type === 'document' && item.documentId) {
        await deleteDocument(item.documentId);
        onDeleteDocument(item.documentId);
        console.log(`Successfully deleted document ${item.documentId}`);
      }
      // refresh list by incrementing refreshKey to re-trigger useEffect
      setRefreshKey(prev => prev + 1);
    } catch (e) {
      console.error('Delete failed:', e);
      setError(e instanceof Error ? e.message : 'Failed to delete item');
    }
  };

  const handleViewDocument = (item: HistoryItem) => {
    if (item.type === 'document' && item.documentId) {
      onViewDocumentDetails(item.documentId);
    }
  };

  return (
    <Card>

      {/* Filter Buttons */}
      <div className="flex gap-2 mb-6">
        {filters.map((f) => (
          <Button
            key={f.value}
            variant={filter === f.value ? 'primary' : 'secondary'}
            size="sm"
            onClick={() => setFilter(f.value)}
          >
            {f.label}
          </Button>
        ))}
      </div>

      {/* Items List */}
      {loading ? (
        <div className="text-center py-8 text-gray-500">Loading history...</div>
      ) : items.length === 0 ? (
        <div className="text-center py-8 text-gray-500">No history items found</div>
      ) : (
        <div className="space-y-3">
                  {error && (
                    <Alert type="error" className="mb-4">
                      {error}
                    </Alert>
                  )}

                  {items.map((item) => (
                    <div
                      key={item.id}
                      className={`border rounded-lg p-4 ${
                        item.type === 'document'
                          ? 'border-blue-200 bg-blue-50'
                          : 'border-green-200 bg-green-50'
                      }`}
                    >
                      <div className="flex items-start justify-between gap-4">
                        <div className="min-w-0">
                          <h3 className="font-semibold text-gray-900">{item.title}</h3>
                          <p className="text-sm text-gray-600 mt-1">{item.details}</p>

                          {item.type === 'draft' && item.documentId && item.draftId && item.draft && (
                            <div className="flex flex-wrap gap-2 mt-3">
                              <Button
                                size="sm"
                                variant="secondary"
                                onClick={() => onViewDetails(item.documentId!, item.draftId!, item.draft!)}
                              >
                                View Details
                              </Button>

                              <Button
                                size="sm"
                                variant="primary"
                                onClick={() => onUpdate(item.documentId!, item.draftId!, item.draft!)}
                              >
                                Edit
                              </Button>

                              <Button
                                size="sm"
                                variant="danger"
                                onClick={() => handleDelete(item)}
                              >
                                Delete
                              </Button>
                            </div>
                          )}

                          {item.type === 'document' && item.documentId && (
                            <div className="flex flex-wrap gap-2 mt-3">
                              <Button
                                size="sm"
                                variant="secondary"
                                onClick={() => handleViewDocument(item)}
                              >
                                View Details
                              </Button>

                              <Button
                                size="sm"
                                variant="danger"
                                onClick={() => handleDelete(item)}
                              >
                                Delete
                              </Button>
                            </div>
                          )}
                        </div>

                        <span className="text-xs text-gray-500 shrink-0">
                          {item.type === 'document' ? '📄' : '✍️'}
                        </span>
                      </div>
                    </div>
                  ))}
        </div>
      )}
    </Card>
  );
}