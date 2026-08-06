"use client";

import { useState, useEffect, useRef } from "react";
import { 
  Search, Grid3X3, Bell, HelpCircle, Settings, Plus, Play, 
  ArrowLeft, Tag, Mail, Phone, MessageSquare, Paperclip, 
  Send, Bot, ChevronDown, AlertCircle, Mic, Database, Sparkles, BrainCircuit, BarChart3
} from "lucide-react";

const API_BASE_URL = "http://127.0.0.1:8000";
const SESSION_ID = "admin_dashboard_session"; 

export default function Dashboard() {
  // AJOUT : État pour gérer les onglets centraux (Chronologie vs PowerBI)
  const [activeTab, setActiveTab] = useState<"CHRONOLOGIE" | "POWERBI">("CHRONOLOGIE");
  
  const [backendStatus, setBackendStatus] = useState("Connexion...");
  const [activeTask, setActiveTask] = useState<"batch" | "audio" | "rag">("batch");
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  
  const [batchResults, setBatchResults] = useState<any>(null);
  const [audioResult, setAudioResult] = useState<string | null>(null);
  const [ragResult, setRagResult] = useState<any>(null);

  const [chatInput, setChatInput] = useState("");
  const [isChatSending, setIsChatSending] = useState(false);
  const [chatMessages, setChatMessages] = useState<Array<{ sender: "user" | "copilot", text: string }>>([
    { sender: "copilot", text: "Systèmes nominaux. Je suis NOVA, prêt à vous assister pour prendre vos décisions." }
  ]);
  const chatEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    fetch(`${API_BASE_URL}/api/health`)
      .then((res) => res.json())
      .then((data) => setBackendStatus(data.status === "online" ? "Connecté" : "Hors ligne"))
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

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [chatMessages, isChatSending]);

  useEffect(() => {
    setFile(null);
  }, [activeTask]);

  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file) return;
    setLoading(true);
    setActiveTab("CHRONOLOGIE"); // Force l'affichage des résultats si on lance une tâche

    const formData = new FormData();
    formData.append("file", file);
    formData.append("session_id", SESSION_ID);

    try {
      if (activeTask === "batch") {
        const res = await fetch(`${API_BASE_URL}/api/batch`, { method: "POST", body: formData });
        if (!res.ok) throw new Error("Erreur serveur Batch");
        const data = await res.json();
        setBatchResults(data.data);
        setChatMessages(prev => [...prev, { sender: "copilot", text: `L'analyse du lot est terminée. J'ai généré les indicateurs d'aide à la décision.` }]);
      
      } else if (activeTask === "audio") {
        const res = await fetch(`${API_BASE_URL}/api/audio`, { method: "POST", body: formData });
        if (!res.ok) throw new Error("Erreur serveur Audio");
        const data = await res.json();
        setAudioResult(data.transcript);
        setChatMessages(prev => [...prev, { sender: "copilot", text: "J'ai terminé la transcription de l'audio. Souhaitez-vous que j'en extraie un plan d'action ?" }]);
      
      } else if (activeTask === "rag") {
        const res = await fetch(`${API_BASE_URL}/api/rag`, { method: "POST", body: formData });
        if (!res.ok) throw new Error("Erreur serveur RAG");
        const data = await res.json();
        setRagResult(data);
        setChatMessages(prev => [...prev, { sender: "copilot", text: `Le document ${data.filename} a été indexé. Je peux l'utiliser pour croiser les données.` }]);
      }
    } catch (error: any) {
      console.error(error);
      alert(`Erreur Backend: ${error.message}.`);
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
      setChatMessages(prev => [...prev, { sender: "copilot", text: "Erreur de communication avec l'API." }]);
    }
    setIsChatSending(false);
  };

  const taskConfig = {
    batch: { accept: ".json,.jsonl", icon: <Mail size={14} />, label: "Fichier JSONL / JSON" },
    audio: { accept: ".wav,.mp3", icon: <Mic size={14} />, label: "Fichier Audio (WAV, MP3)" },
    rag: { accept: ".pdf,.txt,.docx", icon: <Database size={14} />, label: "Document (PDF, TXT)" }
  };

  return (
    <div className="flex flex-col h-screen w-full font-sans overflow-hidden relative bg-[#020617]">
      <style dangerouslySetInnerHTML={{__html: `
        @keyframes subtleZoom { 0% { transform: scale(1); } 50% { transform: scale(1.1); } 100% { transform: scale(1); } }
        .animate-bg-image { animation: subtleZoom 30s ease-in-out infinite; }
      `}} />
      <div className="absolute inset-0 z-0 animate-bg-image bg-cover bg-center bg-no-repeat" style={{ backgroundImage: "url('/background_gradiant.jpg')" }}></div>
      <div className="absolute inset-0 bg-black/20 z-0 pointer-events-none"></div>

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
            <span className={`w-1.5 h-1.5 rounded-full shadow-sm ${backendStatus === "Connecté" ? "bg-emerald-400" : "bg-rose-400"}`}></span>
            API: {backendStatus}
          </div>
          <div className="w-7 h-7 rounded-full bg-slate-300 overflow-hidden cursor-pointer border border-white/20 shadow-sm">
            <img src="https://api.dicebear.com/7.x/avataaars/svg?seed=Admin" alt="Profil" />
          </div>
        </div>
      </header>

      <div className="flex-1 flex gap-4 p-4 overflow-hidden z-10">
        <aside className="w-[320px] flex flex-col gap-4 overflow-y-auto shrink-0 pb-4">
          <div className="bg-white/95 backdrop-blur-md rounded-xl shadow-lg border border-white/20 p-4">
            <div className="flex items-center justify-between mb-6">
              <div className="flex items-center gap-2 text-slate-800">
                <ArrowLeft size={18} />
                <h1 className="text-xl font-semibold">Workspace NOVA</h1>
              </div>
            </div>
            <div className="space-y-2 mb-6">
              <p className="text-[11px] text-slate-400 uppercase tracking-wider font-semibold">Sélecteur de tâche</p>
              <div className="grid grid-cols-1 gap-2">
                <button onClick={() => setActiveTask("batch")} className={`flex items-center gap-2 p-2 rounded-lg text-sm transition-all ${activeTask === "batch" ? "bg-[#2353a4] text-white shadow-md" : "bg-slate-100 text-slate-600 hover:bg-slate-200"}`}><MessageSquare size={16}/> Analyse de feedbacks</button>
                <button onClick={() => setActiveTask("audio")} className={`flex items-center gap-2 p-2 rounded-lg text-sm transition-all ${activeTask === "audio" ? "bg-[#2353a4] text-white shadow-md" : "bg-slate-100 text-slate-600 hover:bg-slate-200"}`}><Mic size={16}/> Transcription Audio</button>
                <button onClick={() => setActiveTask("rag")} className={`flex items-center gap-2 p-2 rounded-lg text-sm transition-all ${activeTask === "rag" ? "bg-[#2353a4] text-white shadow-md" : "bg-slate-100 text-slate-600 hover:bg-slate-200"}`}><Database size={16}/> Indexation (RAG)</button>
              </div>
            </div>
            <div className="border-t border-slate-100 pt-4">
              <p className="text-[11px] text-slate-400 uppercase tracking-wider mb-1 font-semibold">Format attendu</p>
              <p className="text-sm text-[#f37021] font-semibold flex items-center gap-2">{taskConfig[activeTask].icon} {taskConfig[activeTask].label}</p>
            </div>
          </div>
          <div className="bg-white/95 backdrop-blur-md rounded-xl shadow-lg border border-white/20 overflow-hidden">
             <div className="p-3 border-b border-slate-100 flex justify-between items-center bg-slate-50/50">
                <span className="text-xs font-bold text-slate-600 uppercase tracking-wider">Chargement</span>
                <ChevronDown size={14} className="text-slate-400" />
             </div>
             <div className="p-4">
                <form onSubmit={handleUpload} className="flex flex-col gap-4">
                  <div className="border-2 border-dashed border-slate-200 rounded-xl p-4 text-center bg-slate-50/50 hover:bg-blue-50/30 transition-colors">
                    <input type="file" accept={taskConfig[activeTask].accept} onChange={(e) => setFile(e.target.files?.[0] || null)} className="block w-full text-xs text-slate-500 file:mr-3 file:py-1.5 file:px-3 file:rounded-md file:border-0 file:text-xs file:font-semibold file:bg-[#2353a4]/10 file:text-[#2353a4] cursor-pointer transition-colors" />
                  </div>
                  <button type="submit" disabled={!file || loading} className="w-full bg-[#f37021] hover:bg-[#d95d13] disabled:bg-slate-300 text-white text-sm font-bold py-2.5 rounded-lg transition-all shadow-md">
                    {loading ? "Exécution en cours..." : "Lancer le traitement"}
                  </button>
                </form>
             </div>
          </div>
        </aside>

        {/* COLONNE CENTRALE AVEC LES ONGLETS */}
        <main className="flex-1 bg-white/95 backdrop-blur-md rounded-xl shadow-lg border border-white/20 flex flex-col min-w-[400px] overflow-hidden">
          <div className="flex items-center px-4 pt-2 border-b border-slate-200 overflow-x-auto bg-white/50 gap-2">
            <button onClick={() => setActiveTab("CHRONOLOGIE")} className="outline-none">
              <Tab label="CHRONOLOGIE" active={activeTab === "CHRONOLOGIE"} />
            </button>
            <button onClick={() => setActiveTab("POWERBI")} className="outline-none">
              <Tab label="POWER BI" active={activeTab === "POWERBI"} />
            </button>
          </div>

          <div className="flex-1 overflow-y-auto p-6 flex flex-col">
            
            {/* VUE 1 : CHRONOLOGIE (L'historique des tâches) */}
            {activeTab === "CHRONOLOGIE" && (
              <>
                <h3 className="text-sm font-extrabold text-slate-800 mb-6 tracking-wide">RÉSULTATS DE L'EXÉCUTION</h3>
                {loading && (
                  <div className="flex flex-col items-center justify-center h-64 text-[#2353a4]">
                    <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-[#2353a4] mb-4"></div>
                    <p className="text-sm font-semibold">NOVA structure les décisions...</p>
                  </div>
                )}

                {!loading && activeTask === "batch" && batchResults && (
                  <div className="animate-in fade-in duration-500 flex gap-4">
                    <div className="w-9 h-9 rounded-full bg-[#f37021] flex items-center justify-center shrink-0 mt-1 shadow-md"><AlertCircle size={18} className="text-white" /></div>
                    <div className="flex-1 bg-white border border-slate-200 rounded-xl p-5 shadow-sm">
                      <p className="text-sm font-bold text-[#2353a4] mb-1">Rapport de Décision : {batchResults.summary_metrics.total_processed} retours analysés</p>
                      <p className="text-xs text-slate-500 mb-5 font-medium">Système IA | Statut: <span className="text-[#f37021] font-bold">Terminé</span></p>
                      <div className="grid grid-cols-3 gap-4 mb-5 pb-5 border-b border-slate-100">
                        <div className="bg-slate-50 p-3 rounded-lg text-center border border-slate-100"><p className="text-[10px] text-slate-500 font-bold uppercase tracking-wider mb-1">Promoteurs</p><p className="text-2xl font-extrabold text-emerald-600">{batchResults.summary_metrics.total_promoters}</p></div>
                        <div className="bg-slate-50 p-3 rounded-lg text-center border border-slate-100"><p className="text-[10px] text-slate-500 font-bold uppercase tracking-wider mb-1">Passifs</p><p className="text-2xl font-extrabold text-amber-500">{batchResults.summary_metrics.total_passives}</p></div>
                        <div className="bg-slate-50 p-3 rounded-lg text-center border border-slate-100 ring-1 ring-[#2353a4]/20"><p className="text-[10px] text-slate-500 font-bold uppercase tracking-wider mb-1">NPS Global</p><p className="text-2xl font-extrabold text-[#2353a4]">{batchResults.summary_metrics.nps_score}</p></div>
                      </div>
                    </div>
                  </div>
                )}

                {!loading && activeTask === "audio" && audioResult && (
                  <div className="animate-in fade-in duration-500 flex gap-4">
                    <div className="w-9 h-9 rounded-full bg-[#2353a4] flex items-center justify-center shrink-0 mt-1 shadow-md"><Mic size={18} className="text-white" /></div>
                    <div className="flex-1 bg-white border border-slate-200 rounded-xl p-5 shadow-sm">
                      <p className="text-sm font-bold text-[#2353a4] mb-1">Transcription Audio (Insight Mining)</p>
                      <p className="text-xs text-slate-500 mb-4 font-medium">Modèle IA | Statut: <span className="text-emerald-500 font-bold">Complété</span></p>
                      <div className="bg-slate-50 border border-slate-100 p-4 rounded-lg text-slate-700 text-sm leading-relaxed whitespace-pre-wrap">{audioResult}</div>
                    </div>
                  </div>
                )}

                {!loading && activeTask === "rag" && ragResult && (
                  <div className="animate-in fade-in duration-500 flex gap-4">
                    <div className="w-9 h-9 rounded-full bg-emerald-500 flex items-center justify-center shrink-0 mt-1 shadow-md"><Database size={18} className="text-white" /></div>
                    <div className="flex-1 bg-white border border-slate-200 rounded-xl p-5 shadow-sm">
                      <p className="text-sm font-bold text-[#2353a4] mb-1">Indexation Stratégique</p>
                      <p className="text-xs text-slate-500 mb-4 font-medium">Base de Connaissances | Statut: <span className="text-emerald-500 font-bold">Vectorisé</span></p>
                      <div className="flex items-center gap-2 bg-emerald-50 text-emerald-700 border border-emerald-200 p-3 rounded-lg text-sm">
                        <Sparkles size={18} /> Le document <strong>{ragResult.filename}</strong> a été ingéré pour alimenter les futures prises de décisions de NOVA.
                      </div>
                    </div>
                  </div>
                )}
                
                {!loading && !batchResults && !audioResult && !ragResult && (
                  <div className="flex flex-col items-center justify-center flex-1 text-slate-400">
                    <BrainCircuit size={48} className="mb-3 opacity-30" />
                    <p className="text-sm font-medium">Sélectionnez une source de données pour générer des insights.</p>
                  </div>
                )}
              </>
            )}

            {/* VUE 2 : POWER BI (Dashboard d'aide à la décision) */}
            {activeTab === "POWERBI" && (
              <div className="flex flex-col h-full animate-in fade-in duration-300">
                <div className="flex items-center justify-between mb-4">
                   <h3 className="text-sm font-extrabold text-slate-800 tracking-wide flex items-center gap-2">
                     <BarChart3 size={16} className="text-[#2353a4]"/> TABLEAU DE BORD DÉCISIONNEL
                   </h3>
                   <span className="text-[10px] bg-amber-100 text-amber-700 font-bold px-2 py-1 rounded">Intégration Microsoft</span>
                </div>
                
                {/* L'iframe PowerBI : Vous mettrez l'URL d'intégration ("Embed Link") ici */}
                <div className="flex-1 w-full bg-slate-100 rounded-xl border border-slate-200 overflow-hidden relative shadow-inner">
                  {/* Remplacez "src" par le lien d'intégration de votre rapport Power BI */}
                  <iframe 
                    title="Dashboard_CloudShift" 
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

        {/* COLONNE DROITE (Chat Compact & Décisions) */}
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
               <h3 className="font-extrabold text-slate-800 text-sm">NOVA</h3>
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
               {isChatSending && <div className="text-[10px] text-slate-400 italic text-left pl-8 animate-pulse">Analyse des options...</div>}
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