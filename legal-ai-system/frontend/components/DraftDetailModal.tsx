'use client';

import { Draft } from '@/lib/types';
import { Button } from '@/components/UI';

interface DraftDetailModalProps {
  draft: Draft | null;
  isOpen: boolean;
  onClose: () => void;
  onEdit?: () => void;
}

export default function DraftDetailModal({
  draft,
  isOpen,
  onClose,
  onEdit,
}: DraftDetailModalProps) {
  if (!isOpen || !draft) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-2xl max-w-4xl max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="sticky top-0 bg-gradient-to-r from-blue-600 to-blue-700 text-white p-6 flex justify-between items-center">
          <div>
            <h2 className="text-2xl font-bold">Draft Details</h2>
            <p className="text-sm text-blue-100 mt-1">Type: {draft.draft_type} | Version: {draft.version}</p>
          </div>
          <button
            onClick={onClose}
            className="text-white hover:bg-blue-800 rounded-lg p-2 transition"
          >
            ✕
          </button>
        </div>

        {/* Content */}
        <div className="p-6 space-y-6">
          {/* Performance Scores */}
          <div className="grid grid-cols-3 gap-4">
            <div className="bg-gradient-to-br from-blue-50 to-blue-100 p-4 rounded-lg border border-blue-200">
              <p className="text-xs text-gray-600 uppercase font-semibold mb-2">Grounding Score</p>
              <p className="text-4xl font-bold text-blue-600">{(draft.grounding_score * 100).toFixed(1)}%</p>
              <p className="text-xs text-gray-600 mt-2">Evidence alignment</p>
            </div>
            <div className="bg-gradient-to-br from-green-50 to-green-100 p-4 rounded-lg border border-green-200">
              <p className="text-xs text-gray-600 uppercase font-semibold mb-2">Completeness Score</p>
              <p className="text-4xl font-bold text-green-600">{(draft.completeness_score * 100).toFixed(1)}%</p>
              <p className="text-xs text-gray-600 mt-2">Content coverage</p>
            </div>
            <div className="bg-gradient-to-br from-purple-50 to-purple-100 p-4 rounded-lg border border-purple-200">
              <p className="text-xs text-gray-600 uppercase font-semibold mb-2">Quality Score</p>
              <p className="text-4xl font-bold text-purple-600">
                {((draft.grounding_score + draft.completeness_score) / 2 * 100).toFixed(1)}%
              </p>
              <p className="text-xs text-gray-600 mt-2">Overall quality</p>
            </div>
          </div>

          {/* Draft Metadata */}
          <div className="grid grid-cols-2 gap-4 p-4 bg-gray-50 rounded-lg">
            <div>
              <p className="text-xs font-semibold text-gray-600 uppercase">Draft Type</p>
              <p className="text-sm text-gray-900 font-medium">{draft.draft_type}</p>
            </div>
            <div>
              <p className="text-xs font-semibold text-gray-600 uppercase">Version</p>
              <p className="text-sm text-gray-900 font-medium">v{draft.version}</p>
            </div>
            <div>
              <p className="text-xs font-semibold text-gray-600 uppercase">Created</p>
              <p className="text-sm text-gray-900">{new Date(draft.created_at).toLocaleString()}</p>
            </div>
            <div>
              <p className="text-xs font-semibold text-gray-600 uppercase">Last Updated</p>
              <p className="text-sm text-gray-900">{new Date(draft.updated_at).toLocaleString()}</p>
            </div>
          </div>

          {/* Draft Content */}
          <div>
            <div className="flex items-center gap-2 mb-3">
              <h3 className="text-lg font-semibold text-gray-900">Draft Content</h3>
              <span className="text-xs bg-blue-100 text-blue-700 px-2 py-1 rounded">
                {draft.draft_content?.length || 0} characters
              </span>
            </div>
            <div className="bg-gray-50 p-4 rounded-lg border border-gray-200 max-h-96 overflow-y-auto">
              <p className="text-sm text-gray-700 whitespace-pre-wrap leading-relaxed">
                {draft.draft_content}
              </p>
            </div>
          </div>

          {/* Supporting Evidence */}
          {draft.supporting_evidence && draft.supporting_evidence.length > 0 && (
            <div>
              <div className="flex items-center gap-2 mb-3">
                <h3 className="text-lg font-semibold text-gray-900">Supporting Evidence</h3>
                <span className="text-xs bg-green-100 text-green-700 px-2 py-1 rounded">
                  {draft.supporting_evidence.length} pieces
                </span>
              </div>
              <div className="space-y-3">
                {draft.supporting_evidence.map((evidence, idx) => (
                  <div
                    key={idx}
                    className="border-l-4 border-blue-500 bg-blue-50 p-4 rounded-r-lg"
                  >
                    <div className="flex items-start justify-between gap-3 mb-2">
                      <p className="text-sm font-semibold text-blue-900">
                        Evidence {idx + 1}
                        {evidence.inspectable && (
                          <span className="ml-2 bg-green-100 text-green-800 px-2 py-0.5 rounded text-xs inline-block">
                            Inspectable
                          </span>
                        )}
                      </p>
                    </div>

                    {/* Evidence Text */}
                    <p className="text-sm text-gray-700 mb-3 bg-white p-2 rounded border border-blue-100">
                      &quot;{evidence.text}&quot;
                    </p>

                    {/* Evidence Metadata */}
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-2 text-xs">
                      <div className="bg-white p-2 rounded border border-blue-100">
                        <p className="text-gray-600">Similarity</p>
                        <p className="font-semibold text-blue-600">
                          {(evidence.similarity_score * 100).toFixed(1)}%
                        </p>
                      </div>
                      <div className="bg-white p-2 rounded border border-blue-100">
                        <p className="text-gray-600">Source</p>
                        <p className="font-semibold text-gray-900">{evidence.source}</p>
                      </div>
                      {evidence.doc_id && (
                        <div className="bg-white p-2 rounded border border-blue-100">
                          <p className="text-gray-600">Doc ID</p>
                          <p className="font-semibold text-gray-900">{evidence.doc_id}</p>
                        </div>
                      )}
                      {evidence.chunk_index !== undefined && evidence.chunk_index >= 0 && (
                        <div className="bg-white p-2 rounded border border-blue-100">
                          <p className="text-gray-600">Chunk</p>
                          <p className="font-semibold text-gray-900">{evidence.chunk_index}</p>
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* No Evidence */}
          {(!draft.supporting_evidence || draft.supporting_evidence.length === 0) && (
            <div className="p-4 bg-yellow-50 border border-yellow-200 rounded-lg text-sm text-yellow-800">
              ⚠️ No supporting evidence available for this draft.
            </div>
          )}
        </div>

        {/* Footer Actions */}
        <div className="sticky bottom-0 bg-gray-50 border-t border-gray-200 p-6 flex gap-3 justify-end">
          <Button variant="secondary" onClick={onClose}>
            Close
          </Button>
          {onEdit && (
            <Button onClick={onEdit}>
              Edit & Improve
            </Button>
          )}
        </div>
      </div>
    </div>
  );
}
