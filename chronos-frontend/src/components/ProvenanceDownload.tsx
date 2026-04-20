import { Download, FileCode, FileText, Hash } from 'lucide-react';
import { api } from '../lib/api';

interface ProvenanceDownloadProps {
  incidentId: string;
}

const FORMATS = [
  {
    key: 'jsonld' as const,
    label: 'JSON-LD',
    description: 'Linked Data (JSON)',
    icon: FileCode,
    ext: 'jsonld',
    mime: 'application/ld+json',
  },
  {
    key: 'ttl' as const,
    label: 'Turtle',
    description: 'RDF Turtle format',
    icon: Hash,
    ext: 'ttl',
    mime: 'text/turtle',
  },
  {
    key: 'provn' as const,
    label: 'PROV-N',
    description: 'W3C PROV notation',
    icon: FileText,
    ext: 'provn',
    mime: 'text/provenance-notation',
  },
];

export default function ProvenanceDownload({ incidentId }: ProvenanceDownloadProps) {
  function handleDownload(format: 'jsonld' | 'ttl' | 'provn') {
    const url = api.getProvenanceUrl(incidentId, format);
    const a = document.createElement('a');
    a.href = url;
    a.download = `chronos-provenance-${incidentId.slice(0, 8)}.${format}`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
  }

  return (
    <div className="space-y-4">
      <div className="p-4 bg-sky-950/30 border border-sky-800/40 rounded-xl">
        <h3 className="text-sm font-semibold text-sky-300 mb-1 flex items-center gap-2">
          <Download className="w-4 h-4" />
          PROV-O Provenance Artifacts
        </h3>
        <p className="text-xs text-sky-400/70 leading-relaxed">
          Download W3C PROV-O compliant provenance records for this incident. These artifacts
          capture the full causal chain of the investigation — including entities, activities,
          agents, and derivation relationships — in machine-readable formats suitable for
          compliance, auditing, and lineage ingestion.
        </p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
        {FORMATS.map(({ key, label, description, icon: Icon, ext }) => (
          <button
            key={key}
            type="button"
            onClick={() => handleDownload(key)}
            className="flex flex-col items-center gap-3 p-4 bg-gray-800 border border-gray-700 rounded-xl hover:border-sky-600 hover:bg-gray-750 transition-all group focus:outline-none focus:ring-2 focus:ring-sky-500"
          >
            <div className="p-3 bg-gray-700 group-hover:bg-sky-900/50 rounded-lg transition-colors">
              <Icon className="w-6 h-6 text-gray-300 group-hover:text-sky-400 transition-colors" />
            </div>
            <div className="text-center">
              <p className="text-sm font-semibold text-gray-200">{label}</p>
              <p className="text-xs text-gray-500">{description}</p>
              <p className="text-xs text-gray-600 font-mono mt-0.5">.{ext}</p>
            </div>
            <div className="flex items-center gap-1 text-xs text-sky-500 group-hover:text-sky-400 transition-colors">
              <Download className="w-3 h-3" />
              Download
            </div>
          </button>
        ))}
      </div>

      <div className="p-3 bg-gray-900 rounded-lg border border-gray-800">
        <p className="text-xs text-gray-500 font-mono break-all">
          Incident ID: {incidentId}
        </p>
      </div>
    </div>
  );
}
