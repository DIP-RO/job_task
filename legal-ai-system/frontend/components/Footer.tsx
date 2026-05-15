'use client';

export default function Footer() {
  const currentYear = new Date().getFullYear();

  return (
    <footer className="bg-gray-900 text-gray-300 mt-12">
      <div className="container mx-auto px-4 py-8 max-w-6xl">
        <div className="grid md:grid-cols-3 gap-8 mb-8">
          <div>
            <h3 className="font-bold text-white mb-4">About</h3>
            <p className="text-sm">
              Legal AI Document Processing System for intelligent document analysis
              and draft generation.
            </p>
          </div>
          <div>
            <h3 className="font-bold text-white mb-4">Features</h3>
            <ul className="text-sm space-y-2">
              <li>✓ Multi-format document processing</li>
              <li>✓ Semantic search with grounding</li>
              <li>✓ AI-powered draft generation</li>
              <li>✓ Learning from operator feedback</li>
            </ul>
          </div>
          <div>
            <h3 className="font-bold text-white mb-4">Tech Stack</h3>
            <ul className="text-sm space-y-2">
              <li>Next.js + TypeScript</li>
              <li>FastAPI Backend</li>
              <li>ChromaDB Vector Store</li>
              <li>OpenAI GPT-4</li>
            </ul>
          </div>
        </div>
        <div className="border-t border-gray-800 pt-8 text-center text-sm">
          <p>
            © {currentYear} Legal AI Document Processing System.{' '}
            <span className="text-gray-500">Pearson Specter Litt</span>
          </p>
        </div>
      </div>
    </footer>
  );
}
