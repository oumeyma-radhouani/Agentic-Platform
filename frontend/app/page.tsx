"use client";

import { useState, useEffect, useRef } from "react";
import { 
  Search, Grid3X3, Bell, HelpCircle, Settings, Plus, Play, 
  ArrowLeft, Tag, Mail, Phone, MessageSquare, Paperclip, 
  Send, Bot, ChevronDown, AlertCircle, Mic, Database, Sparkles, BrainCircuit, BarChart3, TrendingUp, Users, Target, Clock, FileText,
  Eye, Download, X 
} from "lucide-react";

const API_BASE_URL = "http://127.0.0.1:8000";
const SESSION_ID = "executive_dashboard_session"; 

type AnalysisRecord = {
  id: string;
  type: "batch" | "audio" | "rag";
  filename: string;
  date: string;
  data: any;
};

export default function Dashboard() {
  const [activeTab, setActiveTab] = useState<"RAPPORTS" | "HISTORIQUE" | "DASHBOARDS">("RAPPORTS");
  
  const [backendStatus, setBackendStatus] = useState("Connexion...");
  const [activeTask, setActiveTask] = useState<"batch" | "audio" | "rag">("batch");
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  
  const [batchResults, setBatchResults] = useState<any>(null);
  const [audioResult, setAudioResult] = useState<string | null>(null);
  const [ragResult, setRagResult] = useState<any>(null);

  const [analysesHistory, setAnalysesHistory] = useState<AnalysisRecord[]>([]);
  
  const [viewingRecord, setViewingRecord] = useState<AnalysisRecord | null>(null);

  const [chatInput, setChatInput] = useState("");
  const [isChatSending, setIsChatSending] = useState(false);
  const [chatMessages, setChatMessages] = useState<Array<{ sender: "user" | "copilot", text: string }>>([
    { sender: "copilot", text: "Bonjour. Je suis NOVA. Je suis prêt à analyser vos données et formuler des recommandations stratégiques." }
  ]);
  const chatEndRef = useRef<HTMLDivElement>(null);

  // 1. CHARGEMENT DES DONNÉES SAUVEGARDÉES (Au lancement)
  useEffect(() => {
    try {
      const savedHistory = localStorage.getItem('nova_analysesHistory');
      if (savedHistory) setAnalysesHistory(JSON.parse(savedHistory));
      
      const savedBatch = localStorage.getItem('nova_batchResults');
      if (savedBatch) setBatchResults(JSON.parse(savedBatch));
      
      const savedAudio = localStorage.getItem('nova_audioResult');
      if (savedAudio) setAudioResult(JSON.parse(savedAudio));
      
      const savedRag = localStorage.getItem('nova_ragResult');
      if (savedRag) setRagResult(JSON.parse(savedRag));
    } catch (e) {
      console.error("Erreur lors de la lecture du cache:", e);
    }

    fetch(`${API_BASE_URL}/api/health`)
      .then((res) => res.json())
      .then((data) => setBackendStatus(data.status === "online" ? "Opérationnel" : "Hors ligne"))
      .catch(() => setBackendStatus("Déconnecté"));

    fetch(`${API_BASE_URL}/api/chat/history?session_id=${SESSION_ID}`)
      .then((res) => res.json())
      .then((data) => {
        if (data.success && data.messages && data.messages.length > 0) {
          setChatMessages(data.messages);
        }
      })
      .catch((err) => console.error("Impossible de charger l'historique", err));
  }, []);

  // 2. SAUVEGARDE AUTOMATIQUE (À chaque modification)
  useEffect(() => {
    if (batchResults) localStorage.setItem('nova_batchResults', JSON.stringify(batchResults));
  }, [batchResults]);

  useEffect(() => {
    if (audioResult) localStorage.setItem('nova_audioResult', JSON.stringify(audioResult));
  }, [audioResult]);

  useEffect(() => {
    if (ragResult) localStorage.setItem('nova_ragResult', JSON.stringify(ragResult));
  }, [ragResult]);

  useEffect(() => {
    if (analysesHistory.length > 0) {
      localStorage.setItem('nova_analysesHistory', JSON.stringify(analysesHistory));
    }
  }, [analysesHistory]);

  // Autoscroll du chat
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth", block: "nearest" });
  }, [chatMessages, isChatSending]);

  useEffect(() => {
    setFile(null);
  }, [activeTask]);

  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file) return;
    setLoading(true);
    setActiveTab("RAPPORTS"); 

    const formData = new FormData();
    formData.append("file", file);
    formData.append("session_id", SESSION_ID);

    try {
      const currentDate = new Date().toLocaleString("fr-FR", { hour: '2-digit', minute:'2-digit', day: '2-digit', month: 'short' });

      if (activeTask === "batch") {
        const res = await fetch(`${API_BASE_URL}/api/batch`, { method: "POST", body: formData });
        if (!res.ok) throw new Error("Erreur serveur");
        const data = await res.json();
        
        setBatchResults(data.data);
        setAnalysesHistory(prev => [{ id: Date.now().toString(), type: "batch", filename: file.name, date: currentDate, data: data.data }, ...prev]);
        setChatMessages(prev => [...prev, { sender: "copilot", text: `J'ai terminé l'analyse sémantique des ${data.data.summary_metrics.total_processed} retours clients. J'ai dégagé plusieurs tendances clés. Souhaitez-vous que je vous détaille les leviers d'amélioration ?` }]);
      
      } else if (activeTask === "audio") {
        const res = await fetch(`${API_BASE_URL}/api/audio`, { method: "POST", body: formData });
        if (!res.ok) throw new Error("Erreur serveur");
        const data = await res.json();
        
        setAudioResult(data.transcript);
        setAnalysesHistory(prev => [{ id: Date.now().toString(), type: "audio", filename: file.name, date: currentDate, data: data.transcript }, ...prev]);
        setChatMessages(prev => [...prev, { sender: "copilot", text: "L'analyse de l'interaction vocale est terminée. Je peux en extraire le ton, les points de friction et générer une synthèse pour le manager." }]);
      
      } else if (activeTask === "rag") {
        const res = await fetch(`${API_BASE_URL}/api/rag`, { method: "POST", body: formData });
        if (!res.ok) throw new Error("Erreur serveur");
        const data = await res.json();
        
        setRagResult(data);
        setAnalysesHistory(prev => [{ id: Date.now().toString(), type: "rag", filename: file.name, date: currentDate, data: data }, ...prev]);
        setChatMessages(prev => [...prev, { sender: "copilot", text: `Le document stratégique "${data.filename}" a été assimilé. Vous pouvez désormais m'interroger sur son contenu pour vos prises de décision.` }]);
      }
    } catch (error: any) {
      console.error(error);
      alert(`Erreur: ${error.message}.`);
    }
    setLoading(false);
  };

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!chatInput.trim() || isChatSending) return;

    const userText = chatInput;
    setChatInput("");
    setChatMessages(prev => [...prev, { sender: "user", text: userText }]);
    setIsChatSending(true);

    try {
      const res = await fetch(`${API_BASE_URL}/api/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: userText, session_id: SESSION_ID })
      });
      const data = await res.json();
      setChatMessages(prev => [...prev, { sender: "copilot", text: data.response }]);
    } catch (error) {
      setChatMessages(prev => [...prev, { sender: "copilot", text: "Je rencontre des difficultés pour me connecter au réseau neuronal." }]);
    }
    setIsChatSending(false);
  };

  const handleDownload = (record: AnalysisRecord) => {
    let content = "";
    if (record.type === "batch") {
      content = `RAPPORT STRATÉGIQUE : VOIX DU CLIENT\nDate : ${record.date}\nFichier source : ${record.filename}\n\n`;
      content += `--- MÉTRIQUES CLÉS ---\n`;
      content += `Total des retours traités : ${record.data.summary_metrics.total_processed}\n`;
      content += `Promoteurs : ${record.data.summary_metrics.total_promoters}\n`;
      content += `Passifs : ${record.data.summary_metrics.total_passives}\n`;
      content += `Détracteurs : ${record.data.summary_metrics.total_detractors}\n`;
      content += `\nSCORE NPS GLOBAL : ${record.data.summary_metrics.nps_score}\n\n`;
      
      if (record.data.strategic_insights) {
          content += `--- INSIGHTS DÉCISIONNELS (BI) ---\n`;
          content += `CA Menacé (Churn) : ${record.data.strategic_insights.bi_metrics?.revenue_at_risk_eur || 0} €\n`;
          content += `Segment Critique : ${record.data.strategic_insights.bi_metrics?.worst_segment || "N/A"} (NPS: ${record.data.strategic_insights.bi_metrics?.worst_segment_nps || 0})\n`;
          content += `Friction Produit Majeure : ${record.data.strategic_insights.bi_metrics?.top_product_issue || "N/A"}\n`;
          content += `Temps moy. résolution (détracteurs) : ${record.data.strategic_insights.bi_metrics?.avg_resolution_time_detractors_h || 0}h\n\n`;
          
          content += `--- RECOMMANDATIONS D'ACTIONS ---\n`;
          record.data.strategic_insights.recommendations.forEach((r: string, idx: number) => {
              content += `Action ${idx + 1} : ${r}\n`;
          });
          content += `\n`;
      }
      
      content += `[Généré par l'Assistant Stratégique NOVA]`;
    } else if (record.type === "audio") {
      content = `RAPPORT DE TRANSCRIPTION : INTELLIGENCE CONVERSATIONNELLE\nDate : ${record.date}\nFichier source : ${record.filename}\n\n`;
      content += `--- CONTENU DE L'ÉCHANGE ---\n`;
      content += `${record.data}\n\n`;
      content += `[Généré par l'Assistant Stratégique NOVA]`;
    } else {
      content = `RAPPORT D'ASSIMILATION : DOCUMENT STRATÉGIQUE\nDate : ${record.date}\nFichier source : ${record.filename}\n\nStatut : Vectorisé et indexé avec succès.\n[Généré par l'Assistant Stratégique NOVA]`;
    }

    const blob = new Blob([content], { type: "text/plain;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `NOVA_Rapport_${record.type}_${Date.now()}.txt`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const getActiveRecord = (): AnalysisRecord | null => {
    if (activeTask === "batch" && batchResults) return { id: "current", type: "batch", filename: file?.name || "export", date: "À l'instant", data: batchResults };
    if (activeTask === "audio" && audioResult) return { id: "current", type: "audio", filename: file?.name || "audio", date: "À l'instant", data: audioResult };
    if (activeTask === "rag" && ragResult) return { id: "current", type: "rag", filename: file?.name || "document", date: "À l'instant", data: ragResult };
    return null;
  };

  const taskConfig = {
    batch: { accept: ".json,.jsonl,.csv", icon: <Users size={14} />, label: "Exports CRM (Retours Clients)" },
    audio: { accept: ".wav,.mp3", icon: <Phone size={14} />, label: "Enregistrements d'appels" },
    rag: { accept: ".pdf,.txt,.docx", icon: <Target size={14} />, label: "Documents Stratégiques" }
  };

  const activeRecord = getActiveRecord();

  return (
    <div className="flex flex-col h-screen w-full font-sans overflow-hidden relative bg-[#020617]">
      <style dangerouslySetInnerHTML={{__html: `
        @keyframes subtleZoom { 0% { transform: scale(1); } 50% { transform: scale(1.1); } 100% { transform: scale(1); } }
        .animate-bg-image { animation: subtleZoom 30s ease-in-out infinite; }
      `}} />
      <div className="absolute inset-0 z-0 animate-bg-image bg-cover bg-center bg-no-repeat" style={{ backgroundImage: "url('/background_gradiant.jpg')" }}></div>
      <div className="absolute inset-0 bg-black/30 z-0 pointer-events-none"></div>

      {viewingRecord && (
        <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-sm z-[100] flex items-center justify-center p-4 animate-in fade-in duration-200">
          <div className="bg-white rounded-2xl shadow-2xl w-full max-w-2xl flex flex-col max-h-[85vh] overflow-hidden border border-slate-200">
            <div className="px-6 py-4 border-b border-slate-100 flex justify-between items-center bg-slate-50">
              <div className="flex items-center gap-3">
                <div className={`w-8 h-8 rounded-full flex items-center justify-center text-white shadow-sm ${viewingRecord.type === 'batch' ? 'bg-[#f37021]' : viewingRecord.type === 'audio' ? 'bg-[#2353a4]' : 'bg-emerald-500'}`}>
                  {viewingRecord.type === 'batch' && <TrendingUp size={14} />}
                  {viewingRecord.type === 'audio' && <Mic size={14} />}
                  {viewingRecord.type === 'rag' && <Database size={14} />}
                </div>
                <div>
                  <h3 className="font-bold text-slate-800 text-sm">Aperçu Détaillé du Rapport</h3>
                  <p className="text-[10px] text-slate-500 font-medium">Source : {viewingRecord.filename} • {viewingRecord.date}</p>
                </div>
              </div>
              <button onClick={() => setViewingRecord(null)} className="p-2 bg-white border border-slate-200 text-slate-400 hover:text-slate-700 hover:bg-slate-100 rounded-full transition-colors">
                <X size={16} />
              </button>
            </div>
            
            <div className="p-6 overflow-y-auto bg-white flex-1 text-sm text-slate-700">
              {viewingRecord.type === 'batch' && (
                <div className="space-y-4">
                  <p className="font-bold text-[#2353a4] uppercase text-xs tracking-wide border-b pb-2">Données Quantitatives Exactes</p>
                  <ul className="space-y-3">
                    <li className="flex justify-between bg-slate-50 p-3 rounded-lg border border-slate-100">
                      <span className="font-semibold text-slate-600">Total retours analysés</span>
                      <span className="font-bold">{viewingRecord.data.summary_metrics.total_processed}</span>
                    </li>
                    <li className="flex justify-between bg-emerald-50 p-3 rounded-lg border border-emerald-100">
                      <span className="font-semibold text-emerald-800">Promoteurs identifiés</span>
                      <span className="font-bold text-emerald-600">{viewingRecord.data.summary_metrics.total_promoters}</span>
                    </li>
                    <li className="flex justify-between bg-amber-50 p-3 rounded-lg border border-amber-100">
                      <span className="font-semibold text-amber-800">Passifs identifiés</span>
                      <span className="font-bold text-amber-600">{viewingRecord.data.summary_metrics.total_passives}</span>
                    </li>
                    <li className="flex justify-between bg-rose-50 p-3 rounded-lg border border-rose-100">
                      <span className="font-semibold text-rose-800">Détracteurs identifiés</span>
                      <span className="font-bold text-rose-600">{viewingRecord.data.summary_metrics.total_detractors}</span>
                    </li>
                  </ul>
                  
                  <div className="mt-6 bg-[#2353a4]/5 p-4 rounded-xl border border-[#2353a4]/20 grid grid-cols-2 gap-4">
                    <div className="flex flex-col justify-center">
                      <span className="font-extrabold text-[#2353a4] text-xs mb-1">SCORE NPS CALCULÉ</span>
                      <span className="text-3xl font-black text-[#2353a4]">{viewingRecord.data.summary_metrics.nps_score}</span>
                    </div>
                    <div className="flex flex-col justify-center border-l border-[#2353a4]/20 pl-4">
                      <span className="font-extrabold text-rose-600 text-xs mb-1">CA MENACÉ (CHURN)</span>
                      <span className="text-2xl font-black text-rose-600">{viewingRecord.data.strategic_insights?.bi_metrics?.revenue_at_risk_eur?.toLocaleString('fr-FR') || "0"} €</span>
                    </div>
                  </div>
                  
                  {viewingRecord.data.strategic_insights && (
                     <div className="mt-6">
                        <p className="font-bold text-[#2353a4] uppercase text-xs tracking-wide border-b pb-2 mb-3">Insights Macro & Recommandations</p>
                        <div className="bg-blue-50/50 p-4 rounded-lg border border-blue-100">
                            <ul className="list-disc pl-5 space-y-2 text-xs leading-relaxed text-slate-700">
                                {viewingRecord.data.strategic_insights.recommendations.map((reco: string, i: number) => (
                                    <li key={i}><strong>Action {i+1} :</strong> {reco}</li>
                                ))}
                            </ul>
                        </div>
                     </div>
                  )}
                </div>
              )}
              {viewingRecord.type === 'audio' && (
                <div className="space-y-4">
                  <p className="font-bold text-[#2353a4] uppercase text-xs tracking-wide border-b pb-2">Retranscription intégrale</p>
                  <p className="leading-relaxed whitespace-pre-wrap font-medium">{viewingRecord.data}</p>
                </div>
              )}
              {viewingRecord.type === 'rag' && (
                <div className="flex flex-col items-center justify-center py-8 text-emerald-600">
                  <Database size={48} className="mb-4 opacity-50" />
                  <p className="font-bold text-lg">Document vectorisé avec succès</p>
                  <p className="text-slate-500 text-sm mt-2 text-center max-w-md">L'ensemble du document a été découpé et inséré dans la mémoire sémantique. L'Assistant Stratégique y a désormais pleinement accès.</p>
                </div>
              )}
            </div>

            <div className="px-6 py-4 bg-slate-50 border-t border-slate-100 flex justify-end gap-3">
              <button onClick={() => setViewingRecord(null)} className="px-4 py-2 text-sm font-bold text-slate-600 bg-white border border-slate-200 rounded-lg hover:bg-slate-100 transition-colors">
                Fermer
              </button>
              <button onClick={() => handleDownload(viewingRecord)} className="px-4 py-2 text-sm font-bold text-white bg-[#2353a4] rounded-lg hover:bg-blue-800 transition-colors flex items-center gap-2 shadow-md">
                <Download size={16} /> Télécharger (.txt)
              </button>
            </div>
          </div>
        </div>
      )}

      <header className="h-14 bg-slate-900/90 backdrop-blur-md flex items-center justify-between px-4 shrink-0 text-white shadow-md z-20 border-b border-white/10">
        <div className="flex items-center gap-4">
          <Grid3X3 size={20} className="text-white/80 hover:text-white cursor-pointer" />
          <div className="flex items-center gap-2">
             <div className="w-7 h-7 bg-white rounded flex items-center justify-center text-[#2353a4] shadow-sm">
               <Sparkles size={16} className="text-[#f37021]" />
             </div>
             <span className="font-bold tracking-widest text-lg hidden sm:block drop-shadow-sm uppercase">NOVA</span>
          </div>
        </div>
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2 text-[10px] uppercase tracking-wider font-semibold bg-white/10 px-2 py-1 rounded shadow-inner border border-white/5">
            <span className={`w-1.5 h-1.5 rounded-full shadow-sm ${backendStatus === "Opérationnel" ? "bg-emerald-400" : "bg-rose-400"}`}></span>
            IA: {backendStatus}
          </div>
          <div className="w-7 h-7 rounded-full bg-slate-300 overflow-hidden cursor-pointer border border-white/20 shadow-sm">
            <img src="https://api.dicebear.com/7.x/avataaars/svg?seed=Manager" alt="Profil" />
          </div>
        </div>
      </header>

      <div className="flex-1 flex gap-4 p-4 overflow-hidden z-10">
        
        <aside className="w-[320px] flex flex-col gap-4 overflow-y-auto shrink-0 pb-4">
          <div className="bg-white/95 backdrop-blur-md rounded-xl shadow-lg border border-white/20 p-4">
            <div className="flex items-center justify-between mb-6">
              <div className="flex items-center gap-2 text-slate-800">
                <ArrowLeft size={18} />
                <h1 className="text-xl font-semibold">Centre d'Analyse</h1>
              </div>
            </div>
            <div className="space-y-2 mb-6">
              <p className="text-[11px] text-slate-400 uppercase tracking-wider font-semibold">Modules d'Intelligence</p>
              <div className="grid grid-cols-1 gap-2">
                <button onClick={() => setActiveTask("batch")} className={`flex items-center gap-2 p-2 rounded-lg text-sm transition-all ${activeTask === "batch" ? "bg-[#2353a4] text-white shadow-md" : "bg-slate-100 text-slate-600 hover:bg-slate-200"}`}><MessageSquare size={16}/> Voix du Client (Sentiments)</button>
                <button onClick={() => setActiveTask("audio")} className={`flex items-center gap-2 p-2 rounded-lg text-sm transition-all ${activeTask === "audio" ? "bg-[#2353a4] text-white shadow-md" : "bg-slate-100 text-slate-600 hover:bg-slate-200"}`}><Mic size={16}/> Intelligence Conversationnelle</button>
                <button onClick={() => setActiveTask("rag")} className={`flex items-center gap-2 p-2 rounded-lg text-sm transition-all ${activeTask === "rag" ? "bg-[#2353a4] text-white shadow-md" : "bg-slate-100 text-slate-600 hover:bg-slate-200"}`}><Database size={16}/> Apprentissage Documentaire</button>
              </div>
            </div>
            <div className="border-t border-slate-100 pt-4">
              <p className="text-[11px] text-slate-400 uppercase tracking-wider mb-1 font-semibold">Source de Données</p>
              <p className="text-sm text-[#f37021] font-semibold flex items-center gap-2">{taskConfig[activeTask].icon} {taskConfig[activeTask].label}</p>
            </div>
          </div>
          <div className="bg-white/95 backdrop-blur-md rounded-xl shadow-lg border border-white/20 overflow-hidden">
             <div className="p-3 border-b border-slate-100 flex justify-between items-center bg-slate-50/50">
                <span className="text-xs font-bold text-slate-600 uppercase tracking-wider">Ingestion</span>
                <ChevronDown size={14} className="text-slate-400" />
             </div>
             <div className="p-4">
                <form onSubmit={handleUpload} className="flex flex-col gap-4">
                  <div className="border-2 border-dashed border-slate-200 rounded-xl p-4 text-center bg-slate-50/50 hover:bg-blue-50/30 transition-colors">
                    <input type="file" accept={taskConfig[activeTask].accept} onChange={(e) => setFile(e.target.files?.[0] || null)} className="block w-full text-xs text-slate-500 file:mr-3 file:py-1.5 file:px-3 file:rounded-md file:border-0 file:text-xs file:font-semibold file:bg-[#2353a4]/10 file:text-[#2353a4] cursor-pointer transition-colors" />
                  </div>
                  <button type="submit" disabled={!file || loading} className="w-full bg-[#f37021] hover:bg-[#d95d13] disabled:bg-slate-300 text-white text-sm font-bold py-2.5 rounded-lg transition-all shadow-md">
                    {loading ? "Génération en cours..." : "Générer les Insights"}
                  </button>
                </form>
             </div>
          </div>
        </aside>

        <main className="flex-1 bg-white/95 backdrop-blur-md rounded-xl shadow-lg border border-white/20 flex flex-col min-w-[400px] overflow-hidden">
          <div className="flex items-center px-4 pt-2 border-b border-slate-200 overflow-x-auto bg-white/50 gap-2 shrink-0">
            <button onClick={() => setActiveTab("RAPPORTS")} className="outline-none">
              <Tab label="RAPPORT ACTUEL" active={activeTab === "RAPPORTS"} />
            </button>
            <button onClick={() => setActiveTab("HISTORIQUE")} className="outline-none">
              <Tab label="HISTORIQUE" active={activeTab === "HISTORIQUE"} />
            </button>
            <button onClick={() => setActiveTab("DASHBOARDS")} className="outline-none">
              <Tab label="TABLEAUX DE BORD" active={activeTab === "DASHBOARDS"} />
            </button>
          </div>

          <div className="flex-1 overflow-y-auto p-6 relative">
            
            {activeTab === "RAPPORTS" && (
              <div className="flex flex-col h-full animate-in fade-in duration-300">
                <h3 className="text-sm font-extrabold text-slate-800 mb-6 tracking-wide">SYNTHÈSE STRATÉGIQUE</h3>
                
                {loading && (
                  <div className="flex flex-col items-center justify-center flex-1 text-[#2353a4]">
                    <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-[#2353a4] mb-4"></div>
                    <p className="text-sm font-semibold">NOVA consolide les données et recherche des corrélations...</p>
                  </div>
                )}

                {!loading && activeTask === "batch" && batchResults && activeRecord && (
                  <div className="flex flex-col gap-4">
                    <div className="flex gap-4 items-start">
                      <div className="w-9 h-9 rounded-full bg-[#f37021] flex items-center justify-center shrink-0 mt-1 shadow-md"><TrendingUp size={18} className="text-white" /></div>
                      <div className="flex-1 bg-white border border-slate-200 rounded-xl p-5 shadow-sm">
                        <div className="flex justify-between items-start mb-4">
                          <div>
                            <p className="text-sm font-bold text-[#2353a4] mb-1">Rapport de Synthèse : Voix du Client</p>
                            <p className="text-xs text-slate-500 font-medium">Analyse sémantique sur {batchResults.summary_metrics.total_processed} retours qualitatifs.</p>
                          </div>
                          <span className="text-[10px] bg-emerald-100 text-emerald-700 font-bold px-2 py-1 rounded">Analyse Complétée</span>
                        </div>
                        
                        {/* --- NOUVELLE GRILLE BI ORIENTED --- */}
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-5 pb-5 border-b border-slate-100">
                          {/* 1. SCORE NPS (Indicateur Macro) */}
                          <div className="bg-slate-50 p-3 rounded-lg text-center border border-slate-100 shadow-sm">
                            <p className="text-[10px] text-slate-500 font-bold uppercase tracking-wider mb-1">Score NPS Global</p>
                            <p className="text-2xl font-extrabold text-[#2353a4]">{batchResults.summary_metrics.nps_score}</p>
                          </div>

                          {/* 2. IMPACT FINANCIER (CA Menacé) */}
                          <div className="bg-rose-50/30 p-3 rounded-lg text-center border border-rose-100 shadow-sm">
                            <p className="text-[10px] text-rose-600 font-bold uppercase tracking-wider mb-1">CA Menacé (Churn)</p>
                            <p className="text-xl font-extrabold text-rose-600 mt-1">
                              {batchResults.strategic_insights?.bi_metrics?.revenue_at_risk_eur?.toLocaleString('fr-FR') || "0"} €
                            </p>
                          </div>

                          {/* 3. SEGMENT CRITIQUE (Analyse croisée) */}
                          <div className="bg-amber-50/30 p-3 rounded-lg text-center border border-amber-100 shadow-sm">
                            <p className="text-[10px] text-amber-600 font-bold uppercase tracking-wider mb-1">Segment à Risque</p>
                            <p className="text-sm font-extrabold text-slate-700 mt-2 truncate" title={batchResults.strategic_insights?.bi_metrics?.worst_segment}>
                              {batchResults.strategic_insights?.bi_metrics?.worst_segment || "En attente"}
                            </p>
                            <p className="text-[9px] text-rose-500 font-bold mt-1">
                              NPS du segment : {batchResults.strategic_insights?.bi_metrics?.worst_segment_nps || "0"}
                            </p>
                          </div>

                          {/* 4. POINT DE FRICTION PRODUIT & SLA */}
                          <div className="bg-slate-50 p-3 rounded-lg text-center border border-slate-100 shadow-sm">
                            <p className="text-[10px] text-slate-500 font-bold uppercase tracking-wider mb-1">Friction Produit</p>
                            <p className="text-sm font-extrabold text-[#f37021] mt-2 truncate" title={batchResults.strategic_insights?.bi_metrics?.top_product_issue}>
                              {batchResults.strategic_insights?.bi_metrics?.top_product_issue || "En attente"}
                            </p>
                            <p className="text-[9px] text-slate-500 font-bold mt-1">
                              Temps de résolution : {batchResults.strategic_insights?.bi_metrics?.avg_resolution_time_detractors_h || "0"}h
                            </p>
                          </div>
                        </div>

                        <div className="bg-blue-50/50 p-4 rounded-lg border border-blue-100 text-sm text-slate-700 mb-4">
                           <p className="font-bold text-[#2353a4] mb-2 flex items-center gap-2"><Sparkles size={14}/> Recommandations Stratégiques (IA) :</p>
                           <ul className="list-disc pl-5 space-y-2 text-xs leading-relaxed">
                              {batchResults.strategic_insights?.recommendations?.map((reco: string, i: number) => (
                                 <li key={i}><strong>Action {i+1} :</strong> {reco}</li>
                              )) || <li>Les recommandations sont en cours de génération...</li>}
                           </ul>
                        </div>
                        
                        <div className="flex gap-3 justify-end border-t border-slate-100 pt-4">
                          <button onClick={() => setViewingRecord(activeRecord)} className="flex items-center gap-2 px-3 py-2 bg-white border border-slate-200 text-slate-700 rounded-lg text-xs font-bold hover:bg-slate-50 transition-colors shadow-sm">
                            <Eye size={14} /> Aperçu détaillé
                          </button>
                          <button onClick={() => handleDownload(activeRecord)} className="flex items-center gap-2 px-3 py-2 bg-[#2353a4] text-white rounded-lg text-xs font-bold hover:bg-blue-800 transition-colors shadow-sm">
                            <Download size={14} /> Exporter (.txt)
                          </button>
                        </div>
                      </div>
                    </div>
                  </div>
                )}

                {!loading && activeTask === "audio" && audioResult && activeRecord && (
                  <div className="flex gap-4">
                    <div className="w-9 h-9 rounded-full bg-[#2353a4] flex items-center justify-center shrink-0 mt-1 shadow-md"><Mic size={18} className="text-white" /></div>
                    <div className="flex-1 bg-white border border-slate-200 rounded-xl p-5 shadow-sm">
                      <p className="text-sm font-bold text-[#2353a4] mb-1">Analyse de l'Interaction Vocale</p>
                      <p className="text-xs text-slate-500 mb-4 font-medium">Extraction du script et détection des intentions.</p>
                      <div className="bg-slate-50 border border-slate-100 p-4 rounded-lg text-slate-700 text-sm leading-relaxed whitespace-pre-wrap mb-4 line-clamp-4">{audioResult}</div>
                      
                      <div className="flex gap-3 justify-end border-t border-slate-100 pt-4">
                        <button onClick={() => setViewingRecord(activeRecord)} className="flex items-center gap-2 px-3 py-2 bg-white border border-slate-200 text-slate-700 rounded-lg text-xs font-bold hover:bg-slate-50 transition-colors shadow-sm">
                          <Eye size={14} /> Aperçu détaillé
                        </button>
                        <button onClick={() => handleDownload(activeRecord)} className="flex items-center gap-2 px-3 py-2 bg-[#2353a4] text-white rounded-lg text-xs font-bold hover:bg-blue-800 transition-colors shadow-sm">
                          <Download size={14} /> Exporter (.txt)
                        </button>
                      </div>
                    </div>
                  </div>
                )}

                {!loading && activeTask === "rag" && ragResult && activeRecord && (
                  <div className="flex gap-4">
                    <div className="w-9 h-9 rounded-full bg-emerald-500 flex items-center justify-center shrink-0 mt-1 shadow-md"><Database size={18} className="text-white" /></div>
                    <div className="flex-1 bg-white border border-slate-200 rounded-xl p-5 shadow-sm">
                      <p className="text-sm font-bold text-[#2353a4] mb-1">Assimilation Stratégique</p>
                      <p className="text-xs text-slate-500 mb-4 font-medium">Le document a été converti en base de connaissances décisionnelle.</p>
                      <div className="flex items-center gap-2 bg-emerald-50 text-emerald-700 border border-emerald-200 p-3 rounded-lg text-sm mb-4">
                        <Sparkles size={18} /> Les données de <strong>{ragResult.filename}</strong> sont maintenant disponibles pour croiser des informations.
                      </div>
                      
                      <div className="flex gap-3 justify-end border-t border-slate-100 pt-4">
                        <button onClick={() => setViewingRecord(activeRecord)} className="flex items-center gap-2 px-3 py-2 bg-white border border-slate-200 text-slate-700 rounded-lg text-xs font-bold hover:bg-slate-50 transition-colors shadow-sm">
                          <Eye size={14} /> Aperçu détaillé
                        </button>
                        <button onClick={() => handleDownload(activeRecord)} className="flex items-center gap-2 px-3 py-2 bg-[#2353a4] text-white rounded-lg text-xs font-bold hover:bg-blue-800 transition-colors shadow-sm">
                          <Download size={14} /> Exporter (.txt)
                        </button>
                      </div>
                    </div>
                  </div>
                )}
                
                {!loading && !batchResults && !audioResult && !ragResult && (
                  <div className="flex flex-col items-center justify-center flex-1 text-slate-400">
                    <BrainCircuit size={48} className="mb-3 opacity-30" />
                    <p className="text-sm font-medium">Connectez une source de données pour générer des recommandations.</p>
                  </div>
                )}
              </div>
            )}

            {activeTab === "HISTORIQUE" && (
              <div className="flex flex-col h-full animate-in fade-in duration-300">
                <div className="flex items-center justify-between mb-6">
                  <h3 className="text-sm font-extrabold text-slate-800 tracking-wide flex items-center gap-2">
                    <Clock size={16} className="text-[#2353a4]"/> ARCHIVES DES ANALYSES
                  </h3>
                  <span className="text-[10px] text-slate-500 font-semibold">{analysesHistory.length} rapport(s) disponible(s)</span>
                </div>

                {analysesHistory.length === 0 ? (
                  <div className="flex flex-col items-center justify-center flex-1 text-slate-400">
                    <FileText size={48} className="mb-3 opacity-30" />
                    <p className="text-sm font-medium">Aucune analyse n'a encore été effectuée durant cette session.</p>
                  </div>
                ) : (
                  <div className="flex flex-col gap-4 overflow-y-auto">
                    {analysesHistory.map((record) => (
                      <div key={record.id} className="bg-white border border-slate-200 rounded-xl p-4 shadow-sm hover:shadow-md transition-shadow group">
                        <div className="flex justify-between items-center mb-3">
                          <div className="flex items-center gap-3">
                            <div className={`w-10 h-10 rounded-full flex items-center justify-center text-white shadow-sm ${record.type === 'batch' ? 'bg-[#f37021]' : record.type === 'audio' ? 'bg-[#2353a4]' : 'bg-emerald-500'}`}>
                              {record.type === 'batch' && <TrendingUp size={16} />}
                              {record.type === 'audio' && <Mic size={16} />}
                              {record.type === 'rag' && <Database size={16} />}
                            </div>
                            <div>
                              <p className="text-sm font-bold text-[#2353a4]">
                                {record.type === 'batch' && 'Voix du Client (Analyse NPS)'}
                                {record.type === 'audio' && 'Interaction Vocale'}
                                {record.type === 'rag' && 'Assimilation Documentaire'}
                              </p>
                              <div className="flex items-center gap-2 mt-1">
                                <span className="text-[10px] bg-slate-100 text-slate-600 px-2 py-0.5 rounded font-semibold flex items-center gap-1">
                                  <Clock size={10} /> {record.date}
                                </span>
                                <span className="text-[10px] text-slate-400 font-medium">Source: {record.filename}</span>
                              </div>
                            </div>
                          </div>
                          
                          <div className="flex items-center gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                            <button onClick={() => setViewingRecord(record)} className="p-2 text-slate-400 hover:text-[#2353a4] hover:bg-blue-50 rounded-lg transition-colors tooltip-trigger" title="Aperçu Détaillé">
                              <Eye size={18} />
                            </button>
                            <button onClick={() => handleDownload(record)} className="p-2 text-slate-400 hover:text-[#f37021] hover:bg-orange-50 rounded-lg transition-colors tooltip-trigger" title="Télécharger">
                              <Download size={18} />
                            </button>
                          </div>
                        </div>
                        
                        <div className="bg-slate-50 rounded-lg p-3 text-xs text-slate-700 border border-slate-100 mt-2">
                          {record.type === 'batch' && (
                            <div className="flex gap-6">
                              <span><strong>Retours traités:</strong> {record.data.summary_metrics.total_processed}</span>
                              <span><strong>Score NPS:</strong> <span className="text-[#2353a4] font-bold">{record.data.summary_metrics.nps_score}</span></span>
                            </div>
                          )}
                          {record.type === 'audio' && (
                            <p className="line-clamp-1 italic">"{record.data}"</p>
                          )}
                          {record.type === 'rag' && (
                            <p className="text-emerald-700 font-medium">Indexation réussie. Le document est prêt pour l'Assistant Stratégique.</p>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}

            {activeTab === "DASHBOARDS" && (
              <div className="flex flex-col h-full animate-in fade-in duration-300">
                <div className="flex items-center justify-between mb-4">
                   <h3 className="text-sm font-extrabold text-slate-800 tracking-wide flex items-center gap-2">
                     <BarChart3 size={16} className="text-[#2353a4]"/> VISION MACRO & KPIS STRATÉGIQUES
                   </h3>
                   <span className="text-[10px] bg-amber-100 text-amber-700 font-bold px-2 py-1 rounded">Intégration Microsoft Power BI</span>
                </div>
                
                <div className="flex-1 w-full bg-slate-100 rounded-xl border border-slate-200 overflow-hidden relative shadow-inner">
                  <iframe 
                    title="Dashboard_Strategique" 
                    width="100%" 
                    height="100%" 
                    src="https://app.powerbi.com/reportEmbed?reportId=VOTRE_ID_DE_RAPPORT&autoAuth=true&ctid=VOTRE_TENANT_ID" 
                    frameBorder="0" 
                    allowFullScreen={true}
                    className="absolute inset-0"
                  ></iframe>
                </div>
              </div>
            )}
            
          </div>
        </main>

        <aside className="w-[340px] bg-white/95 backdrop-blur-md rounded-xl shadow-lg border border-white/20 flex shrink-0 overflow-hidden">
          <div className="w-12 bg-slate-900/95 flex flex-col items-center py-4 shrink-0 border-r border-slate-800">
            <div className="w-8 h-8 rounded-lg bg-[#f37021] flex items-center justify-center cursor-pointer relative shadow-md">
              <MessageSquare size={16} className="text-white" />
            </div>
          </div>
          <div className="flex-1 flex flex-col bg-white/50">
            <div className="flex flex-col items-center py-4 border-b border-slate-100 bg-white/40">
               <div className="w-10 h-10 bg-gradient-to-br from-[#2353a4] to-[#1a4082] rounded-full flex items-center justify-center mb-2 shadow-md">
                 <BrainCircuit size={20} className="text-white" />
               </div>
               <h3 className="font-extrabold text-slate-800 text-sm">Assistant Stratégique</h3>
            </div>
            <div className="flex-1 p-4 overflow-y-auto space-y-4 bg-slate-50/50">
               {chatMessages.map((msg, idx) => (
                 <div key={idx} className={`flex ${msg.sender === "user" ? "justify-end" : "justify-start"}`}>
                   {msg.sender === "copilot" && (
                     <div className="w-6 h-6 rounded-full bg-[#2353a4] flex items-center justify-center shrink-0 mr-2 mt-1"><BrainCircuit size={12} className="text-white" /></div>
                   )}
                   <div className={`text-xs p-3 rounded-2xl max-w-[85%] leading-relaxed ${msg.sender === "user" ? "bg-slate-800 text-white rounded-tr-none" : "bg-white border border-slate-200 text-slate-700 rounded-tl-none shadow-sm"}`}>
                     {msg.text}
                   </div>
                 </div>
               ))}
               {isChatSending && <div className="text-[10px] text-slate-400 italic text-left pl-8 animate-pulse">Consultation de la base de données...</div>}
               <div ref={chatEndRef} />
            </div>
            <form onSubmit={handleSendMessage} className="p-3 bg-white border-t border-slate-200 flex items-center gap-2">
              <input type="text" value={chatInput} onChange={(e) => setChatInput(e.target.value)} placeholder="Demander une recommandation..." className="flex-1 bg-slate-100 border border-slate-200 rounded-full px-4 py-2 text-xs outline-none focus:ring-1 focus:ring-[#2353a4]" />
              <button type="submit" disabled={isChatSending || !chatInput.trim()} className="w-8 h-8 rounded-full bg-[#2353a4] disabled:bg-slate-300 flex items-center justify-center text-white cursor-pointer"><Send size={14} /></button>
            </form>
          </div>
        </aside>
      </div>
    </div>
  );
}

function Tab({ label, active }: any) {
  return (
    <div className={`px-5 py-3.5 text-[11px] font-extrabold tracking-widest border-b-[3px] whitespace-nowrap transition-colors ${
        active ? 'border-[#f37021] text-slate-900 bg-white/50' : 'border-transparent text-slate-500 hover:bg-white/30'
      }`}>
      {label}
    </div>
  );
}