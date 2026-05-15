'use client';

import { useState } from 'react';
import { Button, Alert } from '@/components/UI';
import { recordEdit, updateDraft, getDraft } from '@/lib/api';
import { Draft } from '@/lib/types';

interface EditModalProps {
  draft: Draft | null;
  documentId: number | null;
  isOpen: boolean;
  onClose: () => void;
  onUpdate?: () => void;
}

export default function EditModal({
  draft,
  documentId,
  isOpen,
  onClose,
  onUpdate,
}: EditModalProps) {
  const [originalContent, setOriginalContent] = useState(draft?.draft_content || '');
  const [editedContent, setEditedContent] = useState(draft?.draft_content || '');
  const [reasoning, setReasoning] = useState('');
  const [feedbackCategory, setFeedbackCategory] = useState('grounding');
  const [submitting, setSubmitting] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  // Update content when draft changes
  if (draft && originalContent !== draft.draft_content) {
    setOriginalContent(draft.draft_content);
    setEditedContent(draft.draft_content);
  }

  const handleSubmit = async () => {
    if (!documentId || !draft) {
      setMessage({ type: 'error', text: 'Missing document or draft information' });
      return;
    }
    if (!editedContent.trim() || !reasoning.trim()) {
      setMessage({ type: 'error', text: 'Please fill in all fields' });
      return;
    }

    setSubmitting(true);
    try {
      // 1. Save the edited draft
      await updateDraft(draft.id, {
        draft_content: editedContent
      });

      // 2. Record the edit for learning
      await recordEdit({
        document_id: documentId,
        draft_id: draft.id,
        original_content: originalContent,
        edited_content: editedContent,
        edit_summary: `Updated draft with ${feedbackCategory} improvements`,
        reasoning,
        feedback_category: feedbackCategory,
      });

      // 3. Refresh
      const refreshedDraft = await getDraft(draft.id);
      setOriginalContent(refreshedDraft.draft_content);
      setEditedContent(refreshedDraft.draft_content);

      setMessage({
        type: 'success',
        text: '✅ Draft updated and edit recorded! Changes saved.',
      });

      setReasoning('');
      setFeedbackCategory('grounding');

      // Close after success
      setTimeout(() => {
        onUpdate?.();
        onClose();
      }, 1500);
    } catch (error) {
      setMessage({
        type: 'error',
        text: error instanceof Error ? error.message : 'Failed to save changes',
      });
    } finally {
      setSubmitting(false);
    }
  };

  if (!isOpen || !draft) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-2xl max-w-4xl max-h-[90vh] overflow-y-auto w-full">
        {/* Header */}
        <div className="sticky top-0 bg-gradient-to-r from-green-600 to-green-700 text-white p-6 flex justify-between items-center">
          <div>
            <h2 className="text-2xl font-bold">Edit & Improve Draft</h2>
            <p className="text-sm text-green-100 mt-1">{draft.draft_type} (v{draft.version})</p>
          </div>
          <button
            onClick={onClose}
            className="text-white hover:bg-green-800 rounded-lg p-2 transition"
          >
            ✕
          </button>
        </div>

        {/* Content */}
        <div className="p-6 space-y-6">
          {/* Feedback Category */}
          <div>
            <label className="block text-sm font-semibold mb-2 text-gray-900">Feedback Category</label>
            <select
              value={feedbackCategory}
              onChange={(e) => setFeedbackCategory(e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500"
            >
              <option value="grounding">Grounding - Add/improve evidence citations</option>
              <option value="clarity">Clarity - Improve writing clarity</option>
              <option value="completeness">Completeness - Add missing sections</option>
              <option value="legal_accuracy">Legal Accuracy - Fix legal issues</option>
              <option value="formatting">Formatting - Improve structure/format</option>
              <option value="other">Other</option>
            </select>
          </div>

          {/* Side-by-Side Comparison */}
          <div className="grid grid-cols-2 gap-4">
            {/* Original Content */}
            <div>
              <label className="block text-sm font-semibold mb-2 text-gray-900">Original Draft</label>
              <textarea
                value={originalContent}
                readOnly
                className="w-full px-4 py-2 border border-gray-300 rounded-lg bg-gray-50 h-64 resize-none text-sm"
                placeholder="Original content..."
              />
            </div>

            {/* Edited Content */}
            <div>
              <label className="block text-sm font-semibold mb-2 text-gray-900">Your Edits</label>
              <textarea
                value={editedContent}
                onChange={(e) => setEditedContent(e.target.value)}
                placeholder="Make your edits here..."
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500 h-64 resize-none text-sm"
              />
            </div>
          </div>

          {/* Reasoning */}
          <div>
            <label className="block text-sm font-semibold mb-2 text-gray-900">
              Why did you make these changes? (Required)
            </label>
            <textarea
              value={reasoning}
              onChange={(e) => setReasoning(e.target.value)}
              placeholder="Explain the reasoning behind your changes. This helps the system learn from your edits..."
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500 h-24 resize-none"
            />
          </div>

          {/* Messages */}
          {message && <Alert type={message.type}>{message.text}</Alert>}

          {/* Stats */}
          <div className="grid grid-cols-3 gap-4 p-4 bg-blue-50 rounded-lg">
            <div>
              <p className="text-xs font-semibold text-gray-600 uppercase">Original Length</p>
              <p className="text-lg font-bold text-blue-600">{originalContent.length}</p>
              <p className="text-xs text-gray-600">characters</p>
            </div>
            <div>
              <p className="text-xs font-semibold text-gray-600 uppercase">New Length</p>
              <p className="text-lg font-bold text-green-600">{editedContent.length}</p>
              <p className="text-xs text-gray-600">characters</p>
            </div>
            <div>
              <p className="text-xs font-semibold text-gray-600 uppercase">Change</p>
              <p className={`text-lg font-bold ${editedContent.length >= originalContent.length ? 'text-green-600' : 'text-red-600'}`}>
                {editedContent.length >= originalContent.length ? '+' : ''}{editedContent.length - originalContent.length}
              </p>
              <p className="text-xs text-gray-600">characters</p>
            </div>
          </div>
        </div>

        {/* Footer Actions */}
        <div className="sticky bottom-0 bg-gray-50 border-t border-gray-200 p-6 flex gap-3 justify-end">
          <Button
            variant="secondary"
            onClick={onClose}
            disabled={submitting}
          >
            Cancel
          </Button>
          <Button
            variant="success"
            onClick={handleSubmit}
            disabled={submitting || !editedContent.trim() || !reasoning.trim()}
          >
            {submitting ? 'Saving...' : 'Record Edit & Learn'}
          </Button>
        </div>
      </div>
    </div>
  );
}
