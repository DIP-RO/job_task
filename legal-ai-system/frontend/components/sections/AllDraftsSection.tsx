'use client';

import { useState, useEffect } from 'react';
import { Card } from '@/components/UI';
import { listDocuments, getDraftsForDocument, getDocument } from '@/lib/api';
import { Document, Draft } from '@/lib/types';

// Interface for a draft with its parent document
interface DraftWithDocument extends Draft {
  parentDocument: Document;
}

export default function AllDraftsSection() {
  const [allDrafts, setAllDrafts] = useState<DraftWithDocument[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadAllDrafts = async () => {
      try {
        setLoading(true);
        // 1. Load ALL documents
        const allDocuments = await listDocuments(0, 100); // Load up to 100 docs
        const draftsWithDocs: DraftWithDocument[] = [];

        // 2. For every document, load ALL its drafts
        for (const doc of allDocuments) {
          try {
            const document = await getDocument(doc.id);
            const docDrafts = await getDraftsForDocument(doc.id);
            
            // Add parent document reference to every draft
            for (const draft of docDrafts) {
              draftsWithDocs.push({
                ...draft,
                parentDocument: document,
              });
            }
          } catch (err) {
            console.error(`Failed to load drafts for doc ${doc.id}:`, err);
          }
        }

        // Sort drafts by newest first
        draftsWithDocs.sort((a, b) => 
          new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
        );

        setAllDrafts(draftsWithDocs);
        console.log("📚 AllDraftsSection loaded all drafts:", draftsWithDocs);
      } catch (error) {
        console.error("Failed to load all drafts:", error);
      } finally {
        setLoading(false);
      }
    };

    loadAllDrafts();
  }, []);

  if (loading) {
    return <div className="text-gray-500">Loading all generated drafts...</div>;
  }

  if (allDrafts.length === 0) {
    return (
      <Card>
        <div className="p-6 text-gray-500">No drafts generated yet. Create your first draft above!</div>
      </Card>
    );
  }

  return (
    <>
      {allDrafts.map((draft) => (
        <Card key={draft.id} className="overflow-hidden">
          {/* Draft Header */}
          <div className="bg-gradient-to-r from-blue-600 to-indigo-600 px-6 py-4 text-white">
            <div className="flex flex-col md:flex-row md:justify-between md:items-start gap-2">
              <div>
                <h3 className="text-xl font-bold">Draft #{draft.id}: {draft.draft_type.replace(/_/g, ' ')}</h3>
                <p className="text-blue-100 text-sm">Parent Document: {draft.parentDocument.filename}</p>
              </div>
              <div className="flex gap-3">
                <span className="bg-white/20 px-3 py-1 rounded-full text-sm">Version {draft.version}</span>
                <span className="bg-white/20 px-3 py-1 rounded-full text-sm">
                  {new Date(draft.created_at).toLocaleDateString()}
                </span>
              </div>
            </div>
          </div>

          {/* Draft Scores */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 p-6 bg-gray-50 border-b">
            <div className="text-center">
              <p className="text-sm font-medium text-gray-500">Grounding Score</p>
              <p className="text-3xl font-bold text-blue-600">{(draft.grounding_score || 0).toFixed(1)}%</p>
            </div>
            <div className="text-center">
              <p className="text-sm font-medium text-gray-500">Completeness Score</p>
              <p className="text-3xl font-bold text-green-600">{(draft.completeness_score || 0).toFixed(1)}%</p>
            </div>
            <div className="text-center">
              <p className="text-sm font-medium text-gray-500">Legal Accuracy Score</p>
              <p className="text-3xl font-bold text-purple-600">{(draft.legal_accuracy_score || 0).toFixed(1)}%</p>
            </div>
          </div>

          {/* Draft Content + Citations + Source */}
          <div className="p-6 space-y-6">
            {/* Full Draft Content */}
            <div>
              <h4 className="text-lg font-semibold mb-2 text-gray-900">Full Draft Content</h4>
              <textarea
                readOnly
                className="w-full min-h-[300px] p-4 bg-white border border-gray-200 rounded-lg text-gray-700 resize-vertical"
                value={draft.draft_content || "No draft content available"}
              />
            </div>

            {/* Citations (if any) */}
            {draft.evidence_citations && draft.evidence_citations.length > 0 && (
              <div>
                <h4 className="text-lg font-semibold mb-2 text-gray-900">Citations & Sources</h4>
                <ul className="list-disc pl-5 space-y-1 text-gray-600">
                  {draft.evidence_citations.map((citation, idx) => (
                    <li key={idx}><strong>{citation.ref_id}:</strong> &quot;{citation.quote}&quot; (Source: {citation.source})</li>
                  ))}
                </ul>
              </div>
            )}

            {/* Source Document Reference */}
            <div>
              <h4 className="text-lg font-semibold mb-2 text-gray-900">Source Document</h4>
              <div className="p-4 bg-gray-50 border border-gray-200 rounded-lg">
                <p className="text-gray-700"><strong>Filename:</strong> {draft.parentDocument.filename}</p>
                <p className="text-gray-700"><strong>Uploaded:</strong> {new Date(draft.parentDocument.created_at).toLocaleString()}</p>
                <p className="text-gray-700"><strong>Status:</strong> {draft.parentDocument.processing_status}</p>
              </div>
            </div>
          </div>
        </Card>
      ))}
    </>
  );
}