'use client';

import { useState, useEffect } from 'react';
import { Card, Button, Alert } from '@/components/UI';
import {
  listDocuments,
  generateDraft,
} from '@/lib/api';
import { Document, Draft, DraftType } from '@/lib/types';
import { truncateText } from '@/lib/utils';
import DraftDetailModal from '@/components/DraftDetailModal';
import EditModal from '@/components/EditModal';

const DRAFT_TYPES: { value: DraftType; label: string }[] = [
  { value: 'case_summary', label: 'Case Summary' },
  { value: 'notice_summary', label: 'Notice Summary' },
  { value: 'checklist', label: 'Checklist' },
  { value: 'memo', label: 'Memo' },
  { value: 'title_review', label: 'Title Review' },
];

interface GenerateSectionProps {
  onDraftGenerated?: () => void;
}

export default function GenerateSection({ onDraftGenerated }: GenerateSectionProps) {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [selectedDocId, setSelectedDocId] = useState<number | null>(null);
  const [draftType, setDraftType] = useState<DraftType>('case_summary');
  const [useLearning, setUseLearning] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [draft, setDraft] = useState<Draft | null>(null);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
  const [loading, setLoading] = useState(true);
  const [showDetailModal, setShowDetailModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);

  // Load documents
  useEffect(() => {
    const loadDocuments = async () => {
      try {
        setLoading(true);
        const docs = await listDocuments();
        console.log("📄 GenerateSection loaded ALL documents:", docs);
        // Show ALL documents regardless of status to fix selection issue
        setDocuments(docs);
        console.log("✅ Set documents in GenerateSection:", docs.length);
        if (docs.length > 0) {
          setSelectedDocId(docs[0].id);
        }
      } catch (error) {
        setMessage({
          type: 'error',
          text: error instanceof Error ? error.message : 'Failed to load documents',
        });
      } finally {
        setLoading(false);
      }
    };

    loadDocuments();
  }, []);

  const handleGenerateDraft = async () => {
    if (!selectedDocId) return;

    try {
      setGenerating(true);
      setMessage(null);
      setDraft(null);

      const generatedDraft = await generateDraft({
        document_id: selectedDocId,
        draft_type: draftType,
        use_learning: useLearning,
      });
      console.log("🎉 GenerateSection created draft:", generatedDraft);
  
      setDraft(generatedDraft);
      setMessage({ type: 'success', text: `✅ Draft generated successfully! Draft ID: ${generatedDraft.id}` });
      // ✅ Don't refresh to preserve the generated draft view
      // Other sections (History, etc.) will update when user navigates
    } catch (error) {
      const errorText = error instanceof Error ? error.message : 'Generation failed';
      setMessage({ type: 'error', text: errorText });
    } finally {
      setGenerating(false);
    }
  };

  return (
    <div className="space-y-8">
      {/* Generation Controls */}
      <Card>
        <div className="space-y-6">
          {/* Document Selection */}
          <div>
            <label className="block text-sm font-semibold mb-2">Select Document</label>
            {loading ? (
              <div className="text-gray-500">Loading documents...</div>
            ) : documents.length === 0 ? (
              <Alert type="warning">No completed documents available. Please upload and process a document first.</Alert>
            ) : (
              <select
                value={selectedDocId || ''}
                onChange={(e) => setSelectedDocId(Number(e.target.value))}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">-- Select a document --</option>
                {documents.map((doc) => (
                  <option key={doc.id} value={doc.id}>
                    {doc.filename}
                  </option>
                ))}
              </select>
            )}
          </div>

          {/* Draft Type Selection */}
          <div>
            <label className="block text-sm font-semibold mb-2">Draft Type</label>
            <select
              value={draftType}
              onChange={(e) => setDraftType(e.target.value as DraftType)}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              {DRAFT_TYPES.map((type) => (
                <option key={type.value} value={type.value}>
                  {type.label}
                </option>
              ))}
            </select>
          </div>

          {/* Learning Checkbox */}
          <label className="flex items-center gap-2">
            <input
              type="checkbox"
              checked={useLearning}
              onChange={(e) => setUseLearning(e.target.checked)}
              className="w-4 h-4"
            />
            <span className="text-sm">Use learned patterns from previous edits</span>
          </label>

          {/* Generate Button */}
          <Button
            onClick={handleGenerateDraft}
            disabled={!selectedDocId || generating}
            className="w-full"
          >
            {generating ? 'Generating...' : 'Generate Draft'}
          </Button>

          {message && <Alert type={message.type}>{message.text}</Alert>}
        </div>
      </Card>

      {/* Draft Output */}
      {draft && (
        <>
          <Card>
            <div className="flex items-start justify-between gap-6 mb-6">
              <div>
                <h2 className="text-2xl font-bold text-blue-600 mb-1">✅ Draft Generated Successfully</h2>
                <p className="text-sm text-gray-600">Draft ID: {draft.id} | Type: {draft.draft_type} | Version: {draft.version}</p>
              </div>
              <span className="text-4xl">📋</span>
            </div>

            {/* Scores */}
            <div className="grid grid-cols-3 gap-4 mb-6">
              <div className="bg-gradient-to-br from-blue-50 to-blue-100 p-4 rounded-lg border border-blue-200">
                <p className="text-xs text-gray-600 font-semibold uppercase mb-1">Grounding Score</p>
                <p className="text-3xl font-bold text-blue-600">
                  {(draft.grounding_score * 100).toFixed(1)}%
                </p>
                <p className="text-xs text-gray-600 mt-2">Evidence alignment</p>
              </div>
              <div className="bg-gradient-to-br from-green-50 to-green-100 p-4 rounded-lg border border-green-200">
                <p className="text-xs text-gray-600 font-semibold uppercase mb-1">Completeness Score</p>
                <p className="text-3xl font-bold text-green-600">
                  {(draft.completeness_score * 100).toFixed(1)}%
                </p>
                <p className="text-xs text-gray-600 mt-2">Content coverage</p>
              </div>
              <div className="bg-gradient-to-br from-purple-50 to-purple-100 p-4 rounded-lg border border-purple-200">
                <p className="text-xs text-gray-600 font-semibold uppercase mb-1">Overall Quality</p>
                <p className="text-3xl font-bold text-purple-600">
                  {((draft.grounding_score + draft.completeness_score) / 2 * 100).toFixed(1)}%
                </p>
                <p className="text-xs text-gray-600 mt-2">Combined score</p>
              </div>
            </div>

            {/* Draft Preview */}
            <div className="mb-6">
              <div className="flex items-center justify-between mb-3">
                <h3 className="font-semibold text-gray-900">Draft Preview</h3>
                <span className="text-xs bg-gray-100 text-gray-700 px-2 py-1 rounded">
                  {draft.draft_content?.length || 0} characters
                </span>
              </div>
              <div className="bg-gray-50 p-4 rounded-lg border border-gray-200 max-h-64 overflow-y-auto">
                <p className="text-sm text-gray-700 whitespace-pre-wrap leading-relaxed">
                  {draft.draft_content}
                </p>
              </div>
            </div>

            {/* Evidence Summary */}
            {draft.supporting_evidence && draft.supporting_evidence.length > 0 && (
              <div className="mb-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
                <div className="flex items-center justify-between mb-3">
                  <p className="text-sm font-semibold text-blue-900">
                    📚 Supporting Evidence: {draft.supporting_evidence.length} sources
                  </p>
                </div>
                <div className="space-y-2">
                  {draft.supporting_evidence.slice(0, 3).map((evidence, idx) => (
                    <div key={idx} className="text-xs text-gray-700 bg-white p-2 rounded border border-blue-100">
                      <p className="font-semibold mb-1">
                        Evidence {idx + 1} (Similarity: {(evidence.similarity_score * 100).toFixed(1)}%)
                      </p>
                      <p className="text-gray-600">&quot;{truncateText(evidence.text, 100)}&quot;</p>
                    </div>
                  ))}
                  {draft.supporting_evidence.length > 3 && (
                    <p className="text-xs text-blue-600 font-semibold p-2">
                      +{draft.supporting_evidence.length - 3} more sources
                    </p>
                  )}
                </div>
              </div>
            )}

            {/* Actions */}
            <div className="flex gap-3 flex-wrap">
              <Button
                onClick={() => setShowDetailModal(true)}
                variant="secondary"
              >
                View Full Details
              </Button>
              <Button
                onClick={() => setShowEditModal(true)}
                variant="success"
              >
                Edit & Improve
              </Button>
              <Button
                onClick={() => {
                  setDraft(null);
                  setMessage(null);
                }}
                variant="secondary"
              >
                Clear
              </Button>
            </div>
          </Card>

          {/* Modals */}
          <DraftDetailModal
            draft={draft}
            isOpen={showDetailModal}
            onClose={() => setShowDetailModal(false)}
            onEdit={() => {
              setShowDetailModal(false);
              setShowEditModal(true);
            }}
          />
          <EditModal
            draft={draft}
            documentId={selectedDocId}
            isOpen={showEditModal}
            onClose={() => setShowEditModal(false)}
            onUpdate={() => {
              onDraftGenerated?.();
            }}
          />
        </>
      )}
    </div>
  );
}