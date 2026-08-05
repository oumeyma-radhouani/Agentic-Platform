"use client";

import { useState, useEffect } from "react";
import { UploadCloud, LayoutDashboard, MessageSquare, BarChart3, Settings, Bell, Search, User, Bot, X, CheckCircle2, ChevronDown, Sparkles } from "lucide-react";

export default function Dashboard() {
  const [activeTab, setActiveTab] = useState("CONSOLE");
  const [showAssist, setShowAssist] = useState(true);
  const [backendStatus, setBackendStatus] = useState("Connecting...");
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState<any>(null);

  useEffect(() => {
    fetch("http://localhost:8000/api/health")
      .then((res) => res.json())
      .then((data) => setBackendStatus(data.status === "online" ? "Connected" : "Offline"))
      .catch(() => setBackendStatus("Disconnected"));
  }, []);

  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file) return;
    setLoading(true);
    const formData = new FormData();
    formData.append("file", file);

    try {
      const res = await fetch("http://localhost:8000/api/batch", { method: "POST", body: formData });
      const data = await res.json();
      setResults(data.data);
      setShowAssist(true);
    } catch (error) {
      console.error(error);
    }
    setLoading(false);
  };

  return (
    <div className="flex flex-col h-screen w-full bg-[#f8fafc] font-sans overflow-hidden">
      
      {/* 1. TOP NAVIGATION (CloudShift Brand Blue Header) */}
      <header className="h-16 bg-white border-b border-slate-200 flex items-center justify-between px-6 shadow-sm z-20 shrink-0">
        <div className="flex items-center gap-3">
          {/* Cloud Logo Icon using brand blue & orange */}
          <div className="w-9 h-9 bg-[#2353a4] rounded-lg flex items-center justify-center text-white font-bold shadow-md relative">
            C
            <span className="absolute -top-1 -right-1 w-3 h-3 bg-[#f37021] rounded-full border-2 border-white"></span>
          </div>
          <div>
            <span className="font-bold text-[#2353a4] text-lg tracking-tight">Cloud<span className="text-[#f37021]">Shift</span></span>
            <span className="block text-[9px] text-slate-400 font-medium tracking-widest uppercase">Agentic Platform</span>
          </div>
        </div>

        {/* Center Tabs */}
        <div className="hidden md:flex items-center gap-8 h-full">
          <Tab label="TODAY" active={activeTab === "TODAY"} onClick={() => setActiveTab("TODAY")} />
          <Tab label="CONSOLE" active={activeTab === "CONSOLE"} onClick={() => setActiveTab("CONSOLE")} />
          <Tab label="POWER BI DASHBOARD" active={activeTab === "POWER BI"} onClick={() => setActiveTab("POWER BI")} />
        </div>

        {/* Right Actions */}
        <div className="flex items-center gap-5">
          <div className="flex items-center gap-2 text-xs font-medium text-slate-600 bg-slate-50 px-3 py-1.5 rounded-full border border-slate-200">
            <span className={`w-2 h-2 rounded-full ${backendStatus === "Connected" ? 'bg-emerald-500' : 'bg-rose-500'}`}></span>
            API: {backendStatus}
          </div>
          <Search size={18} className="text-slate-400 hover:text-slate-600 cursor-pointer" />
          <div className="relative cursor-pointer">
            <Bell size={18} className="text-slate-400 hover:text-slate-600" />
            <span className="absolute -top-1 -right-1 w-2 h-2 bg-[#f37021] rounded-full border border-white"></span>
          </div>
          <div className="w-8 h-8 rounded-full bg-slate-200 border border-slate-300 overflow-hidden cursor-pointer">
            <img src="https://api.dicebear.com/7.x/avataaars/svg?seed=CloudShiftAdmin" alt="User" />
          </div>
        </div>
      </header>

      {/* MAIN LAYOUT */}
      <div className="flex-1 flex overflow-hidden relative">
        
        {/* 2. LEFT PANEL (Interaction Queue / History) */}
        <aside className="w-80 bg-white border-r border-slate-200 flex flex-col shrink-0 z-10">
          <div className="p-4 border-b border-slate-100 flex items-center justify-between">
            <div className="flex gap-4">
              <span className="text-sm font-semibold text-[#2353a4] border-b-2 border-[#2353a4] pb-1">Batch Jobs</span>
              <span className="text-sm font-medium text-slate-400 pb-1 cursor-pointer hover:text-slate-600">History</span>
            </div>
            <ChevronDown size={16} className="text-slate-400" />
          </div>
          
          <div className="flex-1 overflow-y-auto p-4 space-y-3">
            <QueueCard title="Q2 Sentiment Sync" status="Completed" capacity="100%" active={true} />
            <QueueCard title="Support Tickets (Audio)" status="Processing..." capacity="42%" active={false} />
            <QueueCard title="Churn Analysis" status="In Queue" capacity="0%" active={false} />
          </div>
          
          <div className="p-4 border-t border-slate-100">
            <button className="w-full py-2.5 bg-[#f37021] hover:bg-[#d95d13] text-white text-sm font-semibold rounded-lg transition-colors shadow-sm flex items-center justify-center gap-2">
              <Sparkles size={16} /> New Batch Analysis
            </button>
          </div>
        </aside>

        {/* 3. CENTER WORKSPACE */}
        <main className="flex-1 overflow-y-auto p-8 relative">
          
          <div className="flex justify-between items-center mb-6">
             <div>
               <h2 className="text-2xl font-bold text-slate-800">Customer Satisfaction Console</h2>
               <p className="text-slate-500 text-sm mt-1">Ingest structured datasets to trigger Azure-powered agentic analysis.</p>
             </div>
          </div>

          <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-8 max-w-3xl">
            <form onSubmit={handleUpload} className="flex flex-col gap-6">
              <div className="border-2 border-dashed border-slate-200 rounded-xl p-10 flex flex-col items-center justify-center bg-slate-50/50 hover:bg-slate-50 transition-colors cursor-pointer group">
                <UploadCloud size={40} className="text-slate-400 group-hover:text-[#2353a4] transition-colors mb-4" />
                <p className="text-sm text-slate-700 font-medium mb-1">Drag and drop `.jsonl` or `.json` payloads</p>
                <p className="text-xs text-slate-400 mb-4">Supports high-volume call campaign logs & IS data</p>
                <input
                  type="file"
                  accept=".json,.jsonl"
                  onChange={(e) => setFile(e.target.files?.[0] || null)}
                  className="block w-full max-w-xs text-sm text-slate-500 file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-sm file:font-semibold file:bg-slate-200 file:text-slate-700 hover:file:bg-slate-300 cursor-pointer"
                />
              </div>
              
              <div className="flex justify-end border-t border-slate-100 pt-4">
                <button
                  type="submit"
                  disabled={!file || loading}
                  className="bg-[#2353a4] hover:bg-[#1a4082] disabled:bg-slate-200 text-white font-medium py-2.5 px-6 rounded-lg transition-colors shadow-sm flex items-center gap-2"
                >
                  {loading ? "Executing Pipeline..." : "Execute Batch Run"}
                </button>
              </div>
            </form>
          </div>

          {/* Results Cards */}
          {results && !loading && (
            <div className="mt-8 max-w-3xl grid grid-cols-3 gap-4 animate-in slide-in-from-bottom-4">
              <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm text-center">
                <p className="text-slate-400 text-xs font-bold uppercase tracking-wider mb-1">Promoters</p>
                <p className="text-3xl font-bold text-emerald-600">{results.summary_metrics.total_promoters}</p>
              </div>
              <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm text-center">
                <p className="text-slate-400 text-xs font-bold uppercase tracking-wider mb-1">Passives</p>
                <p className="text-3xl font-bold text-amber-500">{results.summary_metrics.total_passives}</p>
              </div>
              <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm text-center">
                <p className="text-slate-400 text-xs font-bold uppercase tracking-wider mb-1">Detractors</p>
                <p className="text-3xl font-bold text-rose-600">{results.summary_metrics.total_detractors}</p>
              </div>
            </div>
          )}

        </main>

        {/* 4. FLOATING AI ASSISTANT (Brand Orange & Blue Widget) */}
        {showAssist && (
          <div className="absolute top-6 right-6 w-[360px] bg-white rounded-2xl shadow-2xl border border-slate-200 flex flex-col z-50 overflow-hidden animate-in slide-in-from-right-8 duration-300">
            
            {/* Widget Header in Deep Enterprise Blue */}
            <div className="bg-[#2353a4] p-4 flex items-center justify-between text-white">
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 rounded-full bg-[#f37021] flex items-center justify-center shadow-md">
                  <Bot size={18} className="text-white" />
                </div>
                <div>
                  <h3 className="font-semibold text-sm">NOVA Agent Assist</h3>
                  <p className="text-[10px] text-blue-200 flex items-center gap-1">
                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span> Active Decision Support
                  </p>
                </div>
              </div>
              <button onClick={() => setShowAssist(false)} className="text-white/70 hover:text-white transition-colors">
                <X size={18} />
              </button>
            </div>

            {/* Chat Messages */}
            <div className="p-4 bg-slate-50/50 flex-1 min-h-[300px] max-h-[400px] overflow-y-auto space-y-4">
              <div className="flex gap-3">
                 <div className="w-6 h-6 rounded-full bg-blue-100 flex items-center justify-center shrink-0 mt-1">
                    <Bot size={14} className="text-[#2353a4]" />
                 </div>
                 <div className="bg-white border border-slate-200 p-3 rounded-2xl rounded-tl-none shadow-sm text-sm text-slate-700">
                   Systems nominal. Upload your customer feedback payloads to trigger proactive recommendations.
                 </div>
              </div>

              {results && (
                <div className="flex gap-3 animate-in fade-in zoom-in">
                  <div className="w-6 h-6 rounded-full bg-blue-100 flex items-center justify-center shrink-0 mt-1">
                    <Bot size={14} className="text-[#2353a4]" />
                  </div>
                  <div className="bg-white border border-slate-200 p-3 rounded-2xl rounded-tl-none shadow-sm text-sm text-slate-700">
                    <p className="mb-2"><strong>Analysis complete:</strong> Processed {results.summary_metrics.total_processed} records. Current NPS is <span className="font-bold text-[#2353a4]">{results.summary_metrics.nps_score}</span>.</p>
                    <div className="bg-orange-50 border border-orange-200 p-2.5 rounded-xl text-xs text-slate-800">
                      <strong className="text-[#f37021] block mb-0.5">⚡ AI Recommendation:</strong> 
                      Initiate targeted follow-ups for the {results.summary_metrics.total_detractors} identified detractors.
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* Input Bar */}
            <div className="p-3 bg-white border-t border-slate-200">
              <input 
                type="text" 
                placeholder="Ask NOVA Copilot..." 
                className="w-full bg-slate-100 border border-slate-200 rounded-xl px-3 py-2 text-sm focus:ring-2 focus:ring-[#f37021] focus:bg-white outline-none transition-all"
              />
            </div>
          </div>
        )}
        
      </div>
    </div>
  );
}

function Tab({ label, active, onClick }: any) {
  return (
    <div 
      onClick={onClick}
      className={`h-full flex items-center text-xs font-bold tracking-wide cursor-pointer border-b-2 transition-colors ${active ? 'border-[#2353a4] text-[#2353a4]' : 'border-transparent text-slate-400 hover:text-slate-600'}`}
    >
      {label}
    </div>
  );
}

function QueueCard({ title, status, capacity, active }: any) {
  return (
    <div className={`p-3.5 rounded-xl border ${active ? 'border-[#2353a4] bg-blue-50/30' : 'border-slate-200 bg-white hover:border-slate-300'} cursor-pointer transition-all shadow-xs`}>
      <div className="flex justify-between items-start mb-2">
        <div className="flex items-center gap-2.5">
          <div className={`w-7 h-7 rounded-lg flex items-center justify-center text-white text-xs ${active ? 'bg-[#2353a4]' : 'bg-slate-400'}`}>
            <User size={14} />
          </div>
          <div>
            <p className="text-sm font-semibold text-slate-800">{title}</p>
            <p className="text-[10px] text-slate-400 font-medium uppercase tracking-wider">{status}</p>
          </div>
        </div>
      </div>
      <div className="w-full bg-slate-100 rounded-full h-1.5 mt-3 overflow-hidden">
        <div className={`h-1.5 rounded-full ${active ? 'bg-[#f37021]' : 'bg-slate-300'}`} style={{ width: capacity }}></div>
      </div>
    </div>
  );
}