'use client';

import { useState, useEffect } from 'react';
import Header from '@/components/Header';
import Navigation from '@/components/Navigation';
import UploadSection from '@/components/sections/UploadSection';
import GenerateSection from '@/components/sections/GenerateSection';
import EditSection from '@/components/sections/EditSection';
import HistorySection from '@/components/sections/HistorySection';
import AllDraftsSection from '@/components/sections/AllDraftsSection';
import { checkApiHealth } from '@/lib/api';
import EditModal from '@/components/EditModal';
import { Draft } from '@/lib/types';

export default function Home() {
  const [apiHealthy, setApiHealthy] = useState<boolean | null>(null);
  const [refreshKey, setRefreshKey] = useState(0);

  const [selectedDocumentId, setSelectedDocumentId] = useState<number | null>(null);
  const [selectedDraft, setSelectedDraft] = useState<Draft | null>(null);
  const [showEditModal, setShowEditModal] = useState(false);

  useEffect(() => {
    const checkHealth = async () => {
      try {
        await checkApiHealth();
        setApiHealthy(true);
      } catch (error) {
        setApiHealthy(false);
      }
    };

    checkHealth();
  }, []);

  // Function to trigger refresh after upload/action so new docs/drafts appear everywhere
  const triggerRefresh = () => {
    setRefreshKey(prev => prev + 1);
  };

  // Handle opening edit modal with draft
  const handleOpenEditModal = (documentId: number, _draftId: number, draft: Draft) => {
    setSelectedDocumentId(documentId);
    setSelectedDraft(draft);
    setShowEditModal(true);
  };

  return (
    <div className="min-h-screen flex flex-col bg-gray-50">
      <Header apiHealthy={apiHealthy} />

      <main className="flex-1 container mx-auto px-4 py-8 max-w-6xl space-y-12">
        {/* Upload Section - always visible */}
        <section>
          <h2 className="text-2xl font-bold mb-4 text-gray-900">Upload Document</h2>
          <UploadSection onUploadComplete={triggerRefresh} />
        </section>

        {/* Generate Section - always visible */}
        <section>
          <h2 className="text-2xl font-bold mb-4 text-gray-900">Generate New Draft</h2>
          <GenerateSection key={`generate-${refreshKey}`} onDraftGenerated={triggerRefresh} />
        </section>

        {/* All Generated Drafts Section - individual section for EVERY draft */}
        <section>
          <h2 className="text-2xl font-bold mb-4 text-gray-900">All Generated Drafts (All Documents)</h2>
          <div className="space-y-8">
            {/* This component renders every draft from every document with full details */}
            <AllDraftsSection key={`alldrafts-${refreshKey}`} />
          </div>
        </section>

        {/* History Section - moved before Edit Section */}
        <section>
          <h2 className="text-2xl font-bold mb-4 text-gray-900">📚 History & All Documents</h2>
          <HistorySection
            key={`history-${refreshKey}`}
            onViewDetails={(documentId, draftId, draft) => {
              handleOpenEditModal(documentId, draftId, draft);
            }}
            onViewDocumentDetails={(documentId) => {
              setSelectedDocumentId(documentId);
              // Scroll to Edit section
              setTimeout(() => {
                document.getElementById('edit-section')?.scrollIntoView({ behavior: 'smooth' });
              }, 100);
            }}
            onUpdate={(documentId, draftId, draft) => {
              handleOpenEditModal(documentId, draftId, draft);
            }}
            onDeleteDocument={(documentId) => {
              if (selectedDocumentId === documentId) {
                setSelectedDocumentId(null);
                setSelectedDraft(null);
              }
              triggerRefresh();
            }}
          />
        </section>

        {/* Edit Section - for viewing document details */}
        <section id="edit-section">
          <h2 className="text-2xl font-bold mb-4 text-gray-900">📝 View Document Details</h2>
          <EditSection
            key={`edit-${refreshKey}`}
            initialDocumentId={selectedDocumentId ?? undefined}
          />
        </section>
      </main>

      {/* Edit Modal - for editing drafts */}
      {showEditModal && (
        <EditModal
          draft={selectedDraft}
          documentId={selectedDocumentId}
          isOpen={showEditModal}
          onClose={() => setShowEditModal(false)}
          onUpdate={() => {
            triggerRefresh();
          }}
        />
      )}

    </div>
  );
}