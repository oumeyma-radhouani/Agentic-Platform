"use client";

import { useState, useEffect } from "react";

export default function Dashboard() {
  const [backendStatus, setBackendStatus] = useState("Connecting...");
  const [azureStatus, setAzureStatus] = useState("Checking...");
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState<any>(null);

  // Ping the FastAPI Health endpoint on load
  useEffect(() => {
    fetch("http://localhost:8000/api/health")
      .then((res) => res.json())
      .then((data) => {
        setBackendStatus(data.status === "online" ? "Nominal" : "Offline");
        setAzureStatus(data.azure_ready ? "Connected" : "Missing Keys");
      })
      .catch(() => {
        setBackendStatus("Disconnected");
        setAzureStatus("Disconnected");
      });
  }, []);

  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file) return;

    setLoading(true);
    const formData = new FormData();
    formData.append("file", file);

    try {
      const res = await fetch("http://localhost:8000/api/batch", {
        method: "POST",
        body: formData,
      });
      const data = await res.json();
      setResults(data.data);
    } catch (error) {
      console.error(error);
      alert("Failed to connect to FastAPI backend.");
    }
    setLoading(false);
  };

  return (
    <div className="min-h-screen bg-[#0d1117] text-[#c9d1d9] p-8 font-sans">
      {/* Header */}
      <header className="flex justify-between items-end mb-10 border-b border-[#30363d] pb-6">
        <div>
          <h1 className="text-3xl font-bold text-[#f0f6fc]">NOVA TERMINAL</h1>
          <p className="text-[#8b949e] tracking-widest text-sm mt-1 uppercase">
            // Command Center
          </p>
        </div>
        <div className="text-right">
          <p className="text-sm">
            Backend API: <span className={backendStatus === "Nominal" ? "text-green-400" : "text-red-400"}>{backendStatus}</span>
          </p>
          <p className="text-sm">
            Azure Node: <span className={azureStatus === "Connected" ? "text-blue-400" : "text-red-400"}>{azureStatus}</span>
          </p>
        </div>
      </header>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        
        {/* Upload Column */}
        <div className="lg:col-span-1 bg-[#161b22] p-6 rounded-xl border border-[#30363d]">
          <h2 className="text-xl font-bold text-white mb-4">Batch Ingestion</h2>
          <form onSubmit={handleUpload} className="flex flex-col gap-4">
            <input
              type="file"
              accept=".json,.jsonl"
              onChange={(e) => setFile(e.target.files?.[0] || null)}
              className="block w-full text-sm text-gray-400 file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-sm file:font-semibold file:bg-[#21262d] file:text-white hover:file:bg-[#30363d] cursor-pointer"
            />
            <button
              type="submit"
              disabled={!file || loading}
              className="bg-[#238636] hover:bg-[#2ea043] disabled:bg-gray-700 text-white font-bold py-2 px-4 rounded-md transition-colors"
            >
              {loading ? "NOVA is analyzing..." : "Execute Analysis"}
            </button>
          </form>
        </div>

        {/* Results Column */}
        <div className="lg:col-span-2">
          {loading && (
            <div className="flex items-center justify-center h-full">
              <div className="animate-pulse text-[#a371f7] text-lg font-mono">
                Transmitting payload to Azure OpenAI...
              </div>
            </div>
          )}

          {results && !loading && (
            <div className="space-y-6 animate-in fade-in duration-500">
              
              {/* Agent Rationale Card */}
              <div className="bg-[#1c2128] border-l-4 border-[#a371f7] p-6 rounded-r-xl shadow-lg">
                <h3 className="text-[#a371f7] font-bold mb-2">✨ Agent Summary</h3>
                <p className="text-gray-300">
                  Successfully processed {results.summary_metrics.total_processed} records. 
                  Calculated Net Promoter Score (NPS) is <strong className="text-white">{results.summary_metrics.nps_score}</strong>.
                </p>
              </div>

              {/* Metrics Grid */}
              <div className="grid grid-cols-3 gap-4">
                <div className="bg-[#161b22] p-6 rounded-xl border border-[#30363d] text-center">
                  <p className="text-[#8b949e] text-sm uppercase tracking-wider">Promoters</p>
                  <p className="text-3xl font-bold text-green-400">{results.summary_metrics.total_promoters}</p>
                </div>
                <div className="bg-[#161b22] p-6 rounded-xl border border-[#30363d] text-center">
                  <p className="text-[#8b949e] text-sm uppercase tracking-wider">Passives</p>
                  <p className="text-3xl font-bold text-yellow-400">{results.summary_metrics.total_passives}</p>
                </div>
                <div className="bg-[#161b22] p-6 rounded-xl border border-[#30363d] text-center">
                  <p className="text-[#8b949e] text-sm uppercase tracking-wider">Detractors</p>
                  <p className="text-3xl font-bold text-red-400">{results.summary_metrics.total_detractors}</p>
                </div>
              </div>

            </div>
          )}

          {!results && !loading && (
            <div className="flex items-center justify-center h-full border-2 border-dashed border-[#30363d] rounded-xl text-gray-500">
              Awaiting JSONL payload...
            </div>
          )}
        </div>
      </div>
    </div>
  );
}