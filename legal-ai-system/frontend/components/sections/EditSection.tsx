'use client';

import { useState, useEffect } from 'react';
import { Card, Alert } from '@/components/UI';
import { listDocuments, getDocument } from '@/lib/api';
import { Document } from '@/lib/types';

export default function EditSection({
  initialDocumentId,
}: {
  initialDocumentId?: number;
}) {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [selectedDocId, setSelectedDocId] = useState<number | null>(null);
  const [currentDocument, setCurrentDocument] = useState<Document | null>(null);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
  const [loading, setLoading] = useState(true);

  // Load documents (and allow preselect from props)
  useEffect(() => {
    const loadDocuments = async () => {
      try {
        setLoading(true);
        const docs = await listDocuments();
        setDocuments(docs);

        const docIdToSelect = initialDocumentId ?? (docs.length > 0 ? docs[0].id : null);
        setSelectedDocId(docIdToSelect);
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
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [initialDocumentId]);

  // Load current document details when selected
  useEffect(() => {
    const loadDocument = async () => {
      if (!selectedDocId) return;
      try {
        const doc = await getDocument(selectedDocId);
        setCurrentDocument(doc);
      } catch (error) {
        setMessage({
          type: 'error',
          text: error instanceof Error ? error.message : 'Failed to load document details',
        });
      }
    };

    loadDocument();
  }, [selectedDocId]);

  return (
    <div className="space-y-8">
      <Card>
        <div className="space-y-6">
          {/* Document Selection */}
          <div>
            <label className="block text-sm font-semibold mb-2 text-gray-900">Select Document</label>
            {loading ? (
              <div className="text-gray-500">Loading documents...</div>
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

          {/* Document Details */}
          {currentDocument && (
            <div className="mt-6 p-4 border border-blue-200 rounded-lg bg-gradient-to-br from-blue-50 to-blue-100">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">📋 Document Details</h3>
              
              {/* Grid Layout */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                <div className="bg-white p-3 rounded-lg border border-blue-200">
                  <p className="text-xs font-semibold text-gray-700 uppercase mb-1">Filename</p>
                  <p className="text-sm text-gray-900 break-all">{currentDocument.filename}</p>
                </div>
                <div className="bg-white p-3 rounded-lg border border-blue-200">
                  <p className="text-xs font-semibold text-gray-700 uppercase mb-1">Status</p>
                  <p className={`text-sm font-semibold ${
                    currentDocument.processing_status === 'completed' ? 'text-green-600' :
                    currentDocument.processing_status === 'processing' ? 'text-yellow-600' :
                    'text-red-600'
                  }`}>
                    {currentDocument.processing_status.toUpperCase()}
                  </p>
                </div>
                <div className="bg-white p-3 rounded-lg border border-blue-200">
                  <p className="text-xs font-semibold text-gray-700 uppercase mb-1">Uploaded</p>
                  <p className="text-sm text-gray-900">{new Date(currentDocument.created_at).toLocaleString()}</p>
                </div>
                <div className="bg-white p-3 rounded-lg border border-blue-200">
                  <p className="text-xs font-semibold text-gray-700 uppercase mb-1">File Type</p>
                  <p className="text-sm text-gray-900">{currentDocument.file_type.toUpperCase()}</p>
                </div>
                {currentDocument.file_size && (
                  <div className="bg-white p-3 rounded-lg border border-blue-200">
                    <p className="text-xs font-semibold text-gray-700 uppercase mb-1">File Size</p>
                    <p className="text-sm text-gray-900">{(currentDocument.file_size / 1024).toFixed(2)} KB</p>
                  </div>
                )}
                {currentDocument.ocr_quality_score !== null && currentDocument.ocr_quality_score !== undefined && (
                  <div className="bg-white p-3 rounded-lg border border-blue-200">
                    <p className="text-xs font-semibold text-gray-700 uppercase mb-1">OCR Quality</p>
                    <p className="text-sm text-gray-900 font-semibold">{(currentDocument.ocr_quality_score * 100).toFixed(1)}%</p>
                  </div>
                )}
              </div>

              {/* Extracted Text */}
              {currentDocument.raw_text && (
                <div className="bg-white p-4 rounded-lg border border-blue-200 mt-4">
                  <p className="text-sm font-semibold text-gray-900 mb-3">📄 Extracted Text</p>
                  <div className="max-h-96 overflow-y-auto">
                    <p className="text-sm text-gray-700 whitespace-pre-wrap leading-relaxed">
                      {currentDocument.raw_text}
                    </p>
                  </div>
                  <p className="text-xs text-gray-500 mt-2">
                    Total length: {currentDocument.raw_text.length} characters
                  </p>
                </div>
              )}
            </div>
          )}

          {!currentDocument && selectedDocId && (
            <Alert type="warning">Loading document details...</Alert>
          )}

          {message && <Alert type={message.type}>{message.text}</Alert>}
        </div>
      </Card>
    </div>
  );
}