'use client';

import { useState, useRef } from 'react';
import { Card, Button, Alert } from '@/components/UI';
import { uploadDocument, processDocument } from '@/lib/api';
import { formatDate } from '@/lib/utils';
import { useDocuments } from '@/hooks/useDocuments';

interface UploadSectionProps {
  onUploadComplete?: () => void;
}

export default function UploadSection({ onUploadComplete }: UploadSectionProps) {
  const [isDragging, setIsDragging] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const { documents, fetchDocuments, loading: documentLoading } = useDocuments();

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleFileUpload = async (file: File) => {
    if (!file) return;

    if (file.size > 50 * 1024 * 1024) {
      setMessage({ type: 'error', text: 'File is too large. Maximum size is 50MB.' });
      return;
    }

    try {
      setUploading(true);
      setMessage(null);

      // Upload
      const uploadedDoc = await uploadDocument(file);
      setMessage({ type: 'success', text: `Document uploaded successfully (ID: ${uploadedDoc.id})` });

      // Process
      await processDocument(uploadedDoc.id, 'case_summary');
      setMessage({ type: 'success', text: 'Document processed successfully!' });

      // Refresh list
      await fetchDocuments();
      // Wait 1 second to ensure backend processing completed, then trigger parent refresh
      setTimeout(async () => {
        await fetchDocuments();
        onUploadComplete?.();
      }, 1000);
    } catch (error) {
      const errorText = error instanceof Error ? error.message : 'Upload failed';
      setMessage({ type: 'error', text: errorText });
    } finally {
      setUploading(false);
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    const file = e.dataTransfer.files[0];
    if (file) {
      handleFileUpload(file);
    }
  };

  return (
    <div className="space-y-8">
      {/* Upload Area */}
      <Card>

        <div
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          className={`border-2 border-dashed rounded-lg p-12 text-center cursor-pointer transition-all ${
            isDragging ? 'border-blue-500 bg-blue-50' : 'border-gray-300 hover:border-blue-400'
          }`}
        >
          <input
            ref={fileInputRef}
            type="file"
            className="hidden"
            onChange={(e) => e.target.files?.[0] && handleFileUpload(e.target.files[0])}
            accept=".pdf,.txt,.docx,.png,.jpg,.jpeg,.tiff"
          />

          <div className="text-5xl mb-4">📄</div>
          <h3 className="text-xl font-semibold mb-2">Drag and drop your document here</h3>
          <p className="text-gray-600 mb-4">or click to select a file</p>
          <p className="text-sm text-gray-500">
            Supported formats: PDF, TXT, DOCX, PNG, JPG, JPEG, TIFF (Max 50MB)
          </p>

          <Button
            onClick={() => fileInputRef.current?.click()}
            className="mt-4"
            disabled={uploading}
          >
            {uploading ? 'Uploading...' : 'Select File'}
          </Button>
        </div>

        {message && (
          <Alert type={message.type} className="mt-4">
            {message.text}
          </Alert>
        )}
      </Card>

      {/* Documents List */}
      <Card>
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-2xl font-bold text-blue-600">Uploaded Documents</h2>
          {!documentLoading && (
            <Button
              variant="secondary"
              size="sm"
              onClick={() => fetchDocuments()}
            >
              Refresh
            </Button>
          )}
        </div>

        {documentLoading ? (
          <div className="text-center py-8 text-gray-500">Loading documents...</div>
        ) : documents.length === 0 ? (
          <div className="text-center py-8 text-gray-500">No documents uploaded yet</div>
        ) : (
          <div className="space-y-4">
            {documents.map((doc) => (
              <div
                key={doc.id}
                className="border border-gray-200 rounded-lg p-4 hover:bg-gray-50 transition-colors"
              >
                <div className="flex justify-between items-start mb-3">
                  <div className="flex-1">
                    <h3 className="font-semibold text-lg text-gray-900">{doc.filename}</h3>
                    <p className="text-sm text-gray-600">
                      Uploaded: {formatDate(doc.created_at)}
                      {doc.processed_at && ` • Processed: ${formatDate(doc.processed_at)}`}
                    </p>
                  </div>
                  <div className="flex gap-2 flex-shrink-0">
                    <span className={`px-3 py-1 rounded-full text-xs font-semibold ${
                      doc.processing_status === 'completed' 
                        ? 'bg-green-100 text-green-800'
                        : doc.processing_status === 'processing'
                        ? 'bg-yellow-100 text-yellow-800'
                        : 'bg-red-100 text-red-800'
                    }`}>
                      {doc.processing_status.toUpperCase()}
                    </span>
                  </div>
                </div>

                <div className="flex gap-2 text-sm text-gray-600 mb-4">
                  <span>📄 Type: {doc.file_type}</span>
                  <span>
                    🔍 OCR Quality:{' '}
                    {doc.ocr_quality_score === null || doc.ocr_quality_score === undefined
                      ? 'N/A'
                      : `${(doc.ocr_quality_score * 100).toFixed(1)}%`}
                  </span>
                  {doc.file_size && (
                    <span>📊 Size: {(doc.file_size / 1024).toFixed(2)} KB</span>
                  )}
                </div>

                {/* Action Buttons */}
                <div className="flex gap-2 flex-wrap">
                  <Button
                    size="sm"
                    variant="secondary"
                    onClick={() => {
                      // Scroll to edit section to view document details
                      document.getElementById('edit-section')?.scrollIntoView({ behavior: 'smooth' });
                      // You can trigger onViewDocumentDetails if parent passes it
                    }}
                  >
                    📋 View Details
                  </Button>
                  <Button
                    size="sm"
                    variant="danger"
                    onClick={async () => {
                      if (confirm(`Are you sure you want to delete "${doc.filename}"?`)) {
                        try {
                          await (await import('@/lib/api')).deleteDocument(doc.id);
                          setMessage({ type: 'success', text: `Document deleted successfully` });
                          await fetchDocuments();
                        } catch (error) {
                          setMessage({
                            type: 'error',
                            text: error instanceof Error ? error.message : 'Failed to delete document'
                          });
                        }
                      }
                    }}
                  >
                    🗑️ Delete
                  </Button>
                </div>
              </div>
            ))}
          </div>
        )}
      </Card>
    </div>
  );
}