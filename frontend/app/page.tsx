"use client";

import { useState, useEffect, useRef } from "react";
import { 
  Search, Grid3X3, Bell, HelpCircle, Settings, Plus, Play, 
  ArrowLeft, Tag, Mail, Phone, MessageSquare, Paperclip, 
  Send, Bot, ChevronDown, AlertCircle, Mic, Database, Sparkles, BrainCircuit, BarChart3, TrendingUp, Users, Target, Clock, FileText,
  Eye, Download, X, AlertTriangle, Euro, LogOut, UserRound, LockKeyhole
} from "lucide-react";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

type AnalysisRecord = {
  id: string;
  type: "batch" | "audio" | "rag";
  filename: string;
  date: string;
  data: any;
};

type AuthenticatedUser = {
  id: string;
  username: string;
  display_name: string;
  role: "admin" | "member";
};

export default function Dashboard() {
  const [authStatus, setAuthStatus] = useState<"checking" | "anonymous" | "authenticated">("checking");
  const [currentUser, setCurrentUser] = useState<AuthenticatedUser | null>(null);
  const [loginUsername, setLoginUsername] = useState("");
  const [loginPassword, setLoginPassword] = useState("");
  const [loginError, setLoginError] = useState("");
  const [loginLoading, setLoginLoading] = useState(false);
  
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
    { sender: "copilot", text: "Système NOVA initialisé. En attente de données pour exécution du modèle." }
  ]);
  const chatEndRef = useRef<HTMLDivElement>(null);

  // AUTH & HEALTH CHECK
  useEffect(() => {
    fetch(`${API_BASE_URL}/api/health`)
      .then((res) => res.json())
      .then((data) => setBackendStatus(data.status === "online" ? "Opérationnel" : "Hors ligne"))
      .catch(() => setBackendStatus("Déconnecté"));

    fetch(`${API_BASE_URL}/api/auth/me`, { credentials: "include" })
      .then(async (res) => {
        if (res.status === 401) return null;
        if (!res.ok) throw new Error("Authentication service unavailable");
        return res.json();
      })
      .then((data) => {
        if (data?.authenticated && data.user) {
          setCurrentUser(data.user);
          setAuthStatus("authenticated");
        } else {
          setAuthStatus("anonymous");
        }
      })
      .catch(() => {
        setLoginError("Le service d'authentification est indisponible.");
        setAuthStatus("anonymous");
      });
  }, []);

  // LOAD CACHE ON LOGIN
  useEffect(() => {
    if (!currentUser) return;
    const cachePrefix = `nova_${currentUser.id}`;
    
    try {
      const savedHistory = localStorage.getItem(`${cachePrefix}_analysesHistory`);
      if (savedHistory) setAnalysesHistory(JSON.parse(savedHistory));
      const savedBatch = localStorage.getItem(`${cachePrefix}_batchResultsSummary`);
      if (savedBatch) setBatchResults(JSON.parse(savedBatch));
      const savedAudio = localStorage.getItem(`${cachePrefix}_audioResult`);
      if (savedAudio) setAudioResult(JSON.parse(savedAudio));
      const savedRag = localStorage.getItem(`${cachePrefix}_ragResult`);
      if (savedRag) setRagResult(JSON.parse(savedRag));
    } catch (e) {
      console.error("Erreur cache:", e);
    }

    fetch(`${API_BASE_URL}/api/chat/history`, { credentials: "include" })
      .then((res) => res.json())
      .then((data) => {
        if (data.success && data.messages?.length > 0) setChatMessages(data.messages);
      })
      .catch(() => {});
  }, [currentUser]);

  // SAVE CACHE
  useEffect(() => {
    if (batchResults && currentUser) localStorage.setItem(`nova_${currentUser.id}_batchResultsSummary`, JSON.stringify(batchResults));
  }, [batchResults, currentUser]);

  useEffect(() => {
    if (audioResult && currentUser) localStorage.setItem(`nova_${currentUser.id}_audioResult`, JSON.stringify(audioResult));
  }, [audioResult, currentUser]);

  useEffect(() => {
    if (ragResult && currentUser) localStorage.setItem(`nova_${currentUser.id}_ragResult`, JSON.stringify(ragResult));
  }, [ragResult, currentUser]);

  useEffect(() => {
    if (analysesHistory.length > 0 && currentUser) localStorage.setItem(`nova_${currentUser.id}_analysesHistory`, JSON.stringify(analysesHistory));
  }, [analysesHistory, currentUser]);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth", block: "nearest" });
  }, [chatMessages, isChatSending]);

  useEffect(() => {
    setFile(null);
  }, [activeTask]);

  const resetAuthenticatedState = () => {
    setCurrentUser(null);
    setAuthStatus("anonymous");
    setBatchResults(null);
    setAudioResult(null);
    setRagResult(null);
    setAnalysesHistory([]);
  };

  const handleLogin = async (event: React.FormEvent) => {
    event.preventDefault();
    setLoginLoading(true);
    setLoginError("");
    try {
      const response = await fetch(`${API_BASE_URL}/api/auth/login`, {
        method: "POST",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username: loginUsername, password: loginPassword }),
      });
      const data = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(data.detail || "Connexion impossible.");
      setCurrentUser(data.user);
      setAuthStatus("authenticated");
      setLoginPassword("");
    } catch (error: any) {
      setLoginError(error.message);
    } finally {
      setLoginLoading(false);
    }
  };

  const handleLogout = async () => {
    try {
      await fetch(`${API_BASE_URL}/api/auth/logout`, { method: "POST", credentials: "include" });
    } finally {
      resetAuthenticatedState();
    }
  };

  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file) return;
    setLoading(true);
    setActiveTab("RAPPORTS"); 

    const formData = new FormData();
    formData.append("file", file);

    try {
      const currentDate = new Date().toLocaleString("fr-FR", { hour: '2-digit', minute:'2-digit', day: '2-digit', month: 'short' });

      if (activeTask === "batch") {
        const res = await fetch(`${API_BASE_URL}/api/batch`, { method: "POST", credentials: "include", body: formData });
        if (!res.ok) throw new Error("Erreur serveur");
        const data = await res.json();
        
        setBatchResults(data.data);
        setAnalysesHistory(prev => [{ id: Date.now().toString(), type: "batch", filename: file.name, date: currentDate, data: data.data }, ...prev]);
        setChatMessages(prev => [...prev, { sender: "copilot", text: `Traitement terminé. Extraction sémantique appliquée sur ${data.data.summary_metrics.total_processed} enregistrements.` }]);
      
      } else if (activeTask === "audio") {
        const res = await fetch(`${API_BASE_URL}/api/audio`, { method: "POST", credentials: "include", body: formData });
        if (!res.ok) throw new Error("Erreur serveur");
        const data = await res.json();
        
        setAudioResult(data.transcript);
        setAnalysesHistory(prev => [{ id: Date.now().toString(), type: "audio", filename: file.name, date: currentDate, data: data.transcript }, ...prev]);
        setChatMessages(prev => [...prev, { sender: "copilot", text: "Transcription et analyse des intentions terminées." }]);
      
      } else if (activeTask === "rag") {
        const res = await fetch(`${API_BASE_URL}/api/rag`, { method: "POST", credentials: "include", body: formData });
        if (!res.ok) throw new Error("Erreur serveur");
        const data = await res.json();
        
        setRagResult(data);
        setAnalysesHistory(prev => [{ id: Date.now().toString(), type: "rag", filename: file.name, date: currentDate, data: data }, ...prev]);
        setChatMessages(prev => [...prev, { sender: "copilot", text: `Base de données vectorielle mise à jour avec le document "${data.filename}". L'indexation (RAG) est active.` }]);
      }
    } catch (error: any) {
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
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: userText })
      });
      const data = await res.json();
      if (!res.ok) throw new Error("Erreur serveur");
      setChatMessages(prev => [...prev, { sender: "copilot", text: data.response }]);
    } catch (error) {
      setChatMessages(prev => [...prev, { sender: "copilot", text: "Erreur de connexion au modèle LLM. Veuillez vérifier l'état du backend." }]);
    }
    setIsChatSending(false);
  };

  const handleDownload = (record: AnalysisRecord) => {
    let content = "";
    if (record.type === "batch") {
      content = JSON.stringify(record.data, null, 2);
    } else {
      content = record.data;
    }
    const blob = new Blob([content], { type: "text/plain;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `NOVA_Rapport_${record.type}_${Date.now()}.${record.type === 'batch' ? 'json' : 'txt'}`;
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
    rag: { accept: ".pdf,.txt,.docx", icon: <Target size={14} />, label: "Documentation Technique" }
  };

  const activeRecord = getActiveRecord();

  if (authStatus === "checking") {
    return (
      <div className="min-h-screen bg-[#020617] text-white flex items-center justify-center">
        <Sparkles size={20} className="text-[#f37021] animate-pulse" />
      </div>
    );
  }

  if (authStatus === "anonymous") {
    return (
      <div className="min-h-screen bg-[#020617] relative overflow-hidden flex items-center justify-center p-6 font-sans">
        <div className="absolute inset-0 bg-cover bg-center opacity-70" style={{ backgroundImage: "url('/background_gradiant.jpg')" }} />
        <div className="absolute inset-0 bg-slate-950/55 backdrop-blur-[2px]" />
        <main className="relative z-10 w-full max-w-md bg-white/95 backdrop-blur-xl rounded-3xl shadow-2xl border border-white/30 overflow-hidden">
          <div className="bg-slate-900 px-8 py-7 text-white">
            <div className="flex items-center gap-3 mb-5">
              <div className="w-10 h-10 bg-white rounded-xl flex items-center justify-center shadow-md">
                <Sparkles size={21} className="text-[#f37021]" />
              </div>
              <div>
                <p className="font-black tracking-[0.22em] text-xl">NOVA</p>
                <p className="text-[10px] text-white/60 uppercase tracking-widest">Data Intelligence Platform</p>
              </div>
            </div>
            <h1 className="text-2xl font-bold">Bienvenue</h1>
            <p className="text-sm text-white/65 mt-2">Connectez-vous pour accéder à l'espace de travail.</p>
          </div>

          <form onSubmit={handleLogin} className="px-8 py-8 space-y-5">
            <div>
              <label htmlFor="username" className="block text-xs font-bold text-slate-700 mb-2">Nom d'utilisateur</label>
              <div className="relative">
                <UserRound size={17} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400" />
                <input
                  id="username"
                  name="username"
                  required
                  value={loginUsername}
                  onChange={(event) => setLoginUsername(event.target.value)}
                  className="w-full rounded-xl border border-slate-200 bg-slate-50 pl-11 pr-4 py-3 text-sm text-slate-900 outline-none focus:ring-2 focus:ring-[#2353a4]/30 focus:border-[#2353a4]"
                  placeholder="votre.nom"
                />
              </div>
            </div>
            <div>
              <label htmlFor="password" className="block text-xs font-bold text-slate-700 mb-2">Mot de passe</label>
              <div className="relative">
                <LockKeyhole size={17} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400" />
                <input
                  id="password"
                  name="password"
                  type="password"
                  required
                  value={loginPassword}
                  onChange={(event) => setLoginPassword(event.target.value)}
                  className="w-full rounded-xl border border-slate-200 bg-slate-50 pl-11 pr-4 py-3 text-sm text-slate-900 outline-none focus:ring-2 focus:ring-[#2353a4]/30 focus:border-[#2353a4]"
                  placeholder="••••••••••"
                />
              </div>
            </div>
            {loginError && (
              <div role="alert" className="flex gap-2 rounded-xl bg-rose-50 border border-rose-200 p-3 text-xs text-rose-700 leading-relaxed">
                <AlertCircle size={16} className="shrink-0 mt-0.5" />
                <span>{loginError}</span>
              </div>
            )}
            <button type="submit" disabled={loginLoading || !loginUsername.trim() || !loginPassword} className="w-full rounded-xl bg-[#2353a4] hover:bg-[#1a4082] disabled:bg-slate-300 text-white py-3 text-sm font-bold transition-colors shadow-lg shadow-blue-900/15">
              {loginLoading ? "Connexion…" : "Se connecter"}
            </button>
          </form>
        </main>
      </div>
    );
  }

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
                  <h3 className="font-bold text-slate-800 text-sm">Aperçu Détaillé du Fichier</h3>
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
                  <p className="font-bold text-[#2353a4] uppercase text-xs tracking-wide border-b pb-2">Métriques d'Ingestion</p>
                  <ul className="space-y-3">
                    <li className="flex justify-between bg-slate-50 p-3 rounded-lg border border-slate-100">
                      <span className="font-semibold text-slate-600">Volume de requêtes traitées</span>
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
                      <span className="font-extrabold text-rose-600 text-xs mb-1">REVENU À RISQUE (ARR)</span>
                      <span className="text-2xl font-black text-rose-600">{viewingRecord.data.financial_risk?.global_ca_menace_euros?.toLocaleString('fr-FR') || "0"} €</span>
                    </div>
                  </div>
                  
                  {viewingRecord.data.strategic_insights && (
                     <div className="mt-6">
                        <p className="font-bold text-[#2353a4] uppercase text-xs tracking-wide border-b pb-2 mb-3">Plans d'Action Prescriptifs</p>
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
                  <p className="font-bold text-[#2353a4] uppercase text-xs tracking-wide border-b pb-2">Analyse Sémantique du Script</p>
                  <p className="leading-relaxed whitespace-pre-wrap font-medium">{viewingRecord.data}</p>
                </div>
              )}
              {viewingRecord.type === 'rag' && (
                <div className="flex flex-col items-center justify-center py-8 text-emerald-600">
                  <Database size={48} className="mb-4 opacity-50" />
                  <p className="font-bold text-lg">Vecteurs générés avec succès</p>
                  <p className="text-slate-500 text-sm mt-2 text-center max-w-md">L'ensemble du document a été découpé et inséré dans la base d'indexation vectorielle de l'espace de travail.</p>
                </div>
              )}
            </div>

            <div className="px-6 py-4 bg-slate-50 border-t border-slate-100 flex justify-end gap-3">
              <button onClick={() => setViewingRecord(null)} className="px-4 py-2 text-sm font-bold text-slate-600 bg-white border border-slate-200 rounded-lg hover:bg-slate-100 transition-colors">
                Fermer
              </button>
              <button onClick={() => handleDownload(viewingRecord)} className="px-4 py-2 text-sm font-bold text-white bg-[#2353a4] rounded-lg hover:bg-blue-800 transition-colors flex items-center gap-2 shadow-md">
                <Download size={16} /> Exporter
              </button>
            </div>
          </div>
        </div>
      )}

      {/* HEADER INITIAL (SOMBRE) */}
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
          <div className="hidden md:flex items-center gap-2 text-right">
            <div>
              <p className="text-[11px] font-bold leading-tight">{currentUser?.display_name}</p>
              <p className="text-[9px] text-white/50 uppercase tracking-wider">{currentUser?.role}</p>
            </div>
            <div className="w-8 h-8 rounded-full bg-[#2353a4] flex items-center justify-center border border-white/20 shadow-sm text-xs font-black">
              {(currentUser?.display_name || currentUser?.username || "N").slice(0, 1).toUpperCase()}
            </div>
          </div>
          <button onClick={handleLogout} className="flex items-center gap-2 rounded-lg border border-white/10 bg-white/10 hover:bg-white/20 px-3 py-2 text-[10px] font-bold uppercase tracking-wider transition-colors" title="Se déconnecter">
            <LogOut size={14} />
          </button>
        </div>
      </header>

      <div className="flex-1 flex gap-4 p-4 overflow-hidden z-10">
        
        {/* ASIDE GAUCHE INITIAL (BLANC VERRE) */}
        <aside className="w-[320px] flex flex-col gap-4 overflow-y-auto shrink-0 pb-4">
          <div className="bg-white/95 backdrop-blur-md rounded-xl shadow-lg border border-white/20 p-4">
            <div className="flex items-center justify-between mb-6">
              <div className="flex items-center gap-2 text-slate-800">
                <ArrowLeft size={18} />
                <h1 className="text-xl font-semibold">Espace de Travail</h1>
              </div>
            </div>
            <div className="space-y-2 mb-6">
              <p className="text-[11px] text-slate-400 uppercase tracking-wider font-semibold">Moteurs de Traitement</p>
              <div className="grid grid-cols-1 gap-2">
                <button onClick={() => setActiveTask("batch")} className={`flex items-center gap-2 p-2 rounded-lg text-sm transition-all ${activeTask === "batch" ? "bg-[#2353a4] text-white shadow-md" : "bg-slate-100 text-slate-600 hover:bg-slate-200"}`}><MessageSquare size={16}/> Analyse Sémantique (CX)</button>
                <button onClick={() => setActiveTask("audio")} className={`flex items-center gap-2 p-2 rounded-lg text-sm transition-all ${activeTask === "audio" ? "bg-[#2353a4] text-white shadow-md" : "bg-slate-100 text-slate-600 hover:bg-slate-200"}`}><Mic size={16}/> Analyse des Interactions</button>
                <button onClick={() => setActiveTask("rag")} className={`flex items-center gap-2 p-2 rounded-lg text-sm transition-all ${activeTask === "rag" ? "bg-[#2353a4] text-white shadow-md" : "bg-slate-100 text-slate-600 hover:bg-slate-200"}`}><Database size={16}/> Indexation Documentaire (RAG)</button>
              </div>
            </div>
            <div className="border-t border-slate-100 pt-4">
              <p className="text-[11px] text-slate-400 uppercase tracking-wider mb-1 font-semibold">Source de Données</p>
              <p className="text-sm text-[#f37021] font-semibold flex items-center gap-2">{taskConfig[activeTask].icon} {taskConfig[activeTask].label}</p>
            </div>
          </div>
          <div className="bg-white/95 backdrop-blur-md rounded-xl shadow-lg border border-white/20 overflow-hidden">
             <div className="p-3 border-b border-slate-100 flex justify-between items-center bg-slate-50/50">
                <span className="text-xs font-bold text-slate-600 uppercase tracking-wider">Import de Données</span>
                <ChevronDown size={14} className="text-slate-400" />
             </div>
             <div className="p-4">
                <form onSubmit={handleUpload} className="flex flex-col gap-4">
                  <div className="border-2 border-dashed border-slate-200 rounded-xl p-4 text-center bg-slate-50/50 hover:bg-blue-50/30 transition-colors">
                    <input type="file" accept={taskConfig[activeTask].accept} onChange={(e) => setFile(e.target.files?.[0] || null)} className="block w-full text-xs text-slate-500 file:mr-3 file:py-1.5 file:px-3 file:rounded-md file:border-0 file:text-xs file:font-semibold file:bg-[#2353a4]/10 file:text-[#2353a4] cursor-pointer transition-colors" />
                  </div>
                  <button type="submit" disabled={!file || loading} className="w-full bg-[#f37021] hover:bg-[#d95d13] disabled:bg-slate-300 text-white text-sm font-bold py-2.5 rounded-lg transition-all shadow-md">
                    {loading ? "Traitement en cours..." : "Exécuter le Traitement"}
                  </button>
                </form>
             </div>
          </div>
        </aside>

        {/* CONTENU PRINCIPAL INITIAL */}
        <main className="flex-1 bg-white/95 backdrop-blur-md rounded-xl shadow-lg border border-white/20 flex flex-col min-w-[400px] overflow-hidden">
          <div className="flex items-center px-4 pt-2 border-b border-slate-200 overflow-x-auto bg-white/50 gap-2 shrink-0">
            <button onClick={() => setActiveTab("RAPPORTS")} className="outline-none">
              <Tab label="SYNTHÈSE EXÉCUTIVE" active={activeTab === "RAPPORTS"} />
            </button>
            <button onClick={() => setActiveTab("DASHBOARDS")} className="outline-none">
              <Tab label="EXPLORATION (BI)" active={activeTab === "DASHBOARDS"} />
            </button>
            <button onClick={() => setActiveTab("HISTORIQUE")} className="outline-none">
              <Tab label="REGISTRE D'AUDIT" active={activeTab === "HISTORIQUE"} />
            </button>
          </div>

          <div className="flex-1 overflow-y-auto p-6 relative bg-slate-50/30">
            
            {activeTab === "RAPPORTS" && (
              <div className="flex flex-col h-full animate-in fade-in duration-300">
                <h3 className="text-sm font-extrabold text-slate-800 mb-6 tracking-wide">APERÇU DES PERFORMANCES</h3>
                
                {loading && (
                  <div className="flex flex-col items-center justify-center flex-1 text-[#2353a4]">
                    <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-[#2353a4] mb-4"></div>
                    <p className="text-sm font-semibold">Traitement des données et extraction des entités en cours...</p>
                  </div>
                )}

                {!loading && activeTask === "batch" && batchResults && activeRecord && (
                  <div className="flex flex-col gap-4">
                    <div className="flex gap-4 items-start">
                      <div className="w-9 h-9 rounded-full bg-[#f37021] flex items-center justify-center shrink-0 mt-1 shadow-md"><TrendingUp size={18} className="text-white" /></div>
                      <div className="flex-1 bg-white border border-slate-200 rounded-xl p-5 shadow-sm">
                        <div className="flex justify-between items-start mb-4">
                          <div>
                            <p className="text-sm font-bold text-[#2353a4] mb-1">Analyse Sémantique (CX)</p>
                            <p className="text-xs text-slate-500 font-medium">Validation effectuée sur {batchResults.summary_metrics.total_processed} requêtes extraites.</p>
                          </div>
                          <span className="text-[10px] bg-emerald-100 text-emerald-700 font-bold px-2 py-1 rounded">Job Terminé</span>
                        </div>
                        
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-5 pb-5 border-b border-slate-100">
                          <div className="bg-slate-50 p-3 rounded-lg text-center border border-slate-100 shadow-sm">
                            <p className="text-[10px] text-slate-500 font-bold uppercase tracking-wider mb-1">Score NPS Global</p>
                            <p className="text-2xl font-extrabold text-[#2353a4]">{batchResults.summary_metrics.nps_score}</p>
                          </div>
                          <div className="bg-rose-50/30 p-3 rounded-lg text-center border border-rose-100 shadow-sm">
                            <p className="text-[10px] text-rose-600 font-bold uppercase tracking-wider mb-1">Revenu à Risque (ARR)</p>
                            <p className="text-xl font-extrabold text-rose-600 mt-1">
                              {batchResults.financial_risk?.global_ca_menace_euros?.toLocaleString('fr-FR') || "0"} €
                            </p>
                          </div>
                          <div className="bg-amber-50/30 p-3 rounded-lg text-center border border-amber-100 shadow-sm">
                            <p className="text-[10px] text-amber-600 font-bold uppercase tracking-wider mb-1">Segment à Risque</p>
                            <p className="text-sm font-extrabold text-slate-700 mt-2 truncate" title={batchResults.strategic_insights?.bi_metrics?.worst_segment}>
                              {batchResults.strategic_insights?.bi_metrics?.worst_segment || "En attente"}
                            </p>
                            <p className="text-[9px] text-rose-500 font-bold mt-1">NPS: {batchResults.strategic_insights?.bi_metrics?.worst_segment_nps || "0"}</p>
                          </div>
                          <div className="bg-slate-50 p-3 rounded-lg text-center border border-slate-100 shadow-sm">
                            <p className="text-[10px] text-slate-500 font-bold uppercase tracking-wider mb-1">Anomalie Majeure Détectée</p>
                            <p className="text-sm font-extrabold text-[#f37021] mt-2 truncate" title={batchResults.strategic_insights?.bi_metrics?.top_product_issue}>
                              {batchResults.strategic_insights?.bi_metrics?.top_product_issue || "En attente"}
                            </p>
                            <p className="text-[9px] text-slate-500 font-bold mt-1">SLA: {batchResults.strategic_insights?.bi_metrics?.avg_resolution_time_detractors_h || "0"}h</p>
                          </div>
                        </div>

                        <div className="bg-blue-50/50 p-4 rounded-lg border border-blue-100 text-sm text-slate-700 mb-4">
                           <p className="font-bold text-[#2353a4] mb-2 flex items-center gap-2"><Sparkles size={14}/> Plans d'Action Prescriptifs :</p>
                           <ul className="list-disc pl-5 space-y-2 text-xs leading-relaxed">
                              {batchResults.strategic_insights?.recommendations?.map((reco: string, i: number) => (
                                 <li key={i}><strong>Action {i+1} :</strong> {reco}</li>
                              )) || <li>Les recommandations ont été générées dans le fichier d'export JSON.</li>}
                           </ul>
                        </div>
                        
                        <div className="flex gap-3 justify-end border-t border-slate-100 pt-4">
                          <button onClick={() => setViewingRecord(activeRecord)} className="flex items-center gap-2 px-3 py-2 bg-white border border-slate-200 text-slate-700 rounded-lg text-xs font-bold hover:bg-slate-50 transition-colors shadow-sm">
                            <Eye size={14} /> Aperçu détaillé
                          </button>
                          <button onClick={() => handleDownload(activeRecord)} className="flex items-center gap-2 px-3 py-2 bg-[#2353a4] text-white rounded-lg text-xs font-bold hover:bg-blue-800 transition-colors shadow-sm">
                            <Download size={14} /> Exporter JSON
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
                      <p className="text-sm font-bold text-[#2353a4] mb-1">Analyse des Interactions</p>
                      <p className="text-xs text-slate-500 mb-4 font-medium">Extraction sémantique du fichier source.</p>
                      <div className="bg-slate-50 border border-slate-100 p-4 rounded-lg text-slate-700 text-sm leading-relaxed whitespace-pre-wrap mb-4 line-clamp-4">{audioResult}</div>
                      <div className="flex gap-3 justify-end border-t border-slate-100 pt-4">
                        <button onClick={() => setViewingRecord(activeRecord)} className="flex items-center gap-2 px-3 py-2 bg-white border border-slate-200 text-slate-700 rounded-lg text-xs font-bold hover:bg-slate-50 transition-colors shadow-sm"><Eye size={14} /> Aperçu détaillé</button>
                        <button onClick={() => handleDownload(activeRecord)} className="flex items-center gap-2 px-3 py-2 bg-[#2353a4] text-white rounded-lg text-xs font-bold hover:bg-blue-800 transition-colors shadow-sm"><Download size={14} /> Exporter (.txt)</button>
                      </div>
                    </div>
                  </div>
                )}

                {!loading && activeTask === "rag" && ragResult && activeRecord && (
                  <div className="flex gap-4">
                    <div className="w-9 h-9 rounded-full bg-emerald-500 flex items-center justify-center shrink-0 mt-1 shadow-md"><Database size={18} className="text-white" /></div>
                    <div className="flex-1 bg-white border border-slate-200 rounded-xl p-5 shadow-sm">
                      <p className="text-sm font-bold text-[#2353a4] mb-1">Indexation Documentaire (RAG)</p>
                      <p className="text-xs text-slate-500 mb-4 font-medium">Conversion du corpus en espace vectoriel.</p>
                      <div className="flex items-center gap-2 bg-emerald-50 text-emerald-700 border border-emerald-200 p-3 rounded-lg text-sm mb-4"><Sparkles size={18} /> Les données de <strong>{ragResult.filename}</strong> ont été indexées.</div>
                      <div className="flex gap-3 justify-end border-t border-slate-100 pt-4">
                        <button onClick={() => setViewingRecord(activeRecord)} className="flex items-center gap-2 px-3 py-2 bg-white border border-slate-200 text-slate-700 rounded-lg text-xs font-bold hover:bg-slate-50 transition-colors shadow-sm"><Eye size={14} /> Aperçu détaillé</button>
                        <button onClick={() => handleDownload(activeRecord)} className="flex items-center gap-2 px-3 py-2 bg-[#2353a4] text-white rounded-lg text-xs font-bold hover:bg-blue-800 transition-colors shadow-sm"><Download size={14} /> Exporter (.txt)</button>
                      </div>
                    </div>
                  </div>
                )}
                
                {!loading && !batchResults && !audioResult && !ragResult && (
                  <div className="flex flex-col items-center justify-center flex-1 text-slate-400">
                    <Database size={48} className="mb-3 opacity-30" />
                    <p className="text-sm font-medium">Importer un jeu de données pour démarrer l'analyse.</p>
                  </div>
                )}
              </div>
            )}

            {/* ONGLET DASHBOARD POWER BI (Intégré) */}
            {activeTab === "DASHBOARDS" && (
              <div className="flex flex-col h-full animate-in fade-in duration-300">
                <div className="flex items-center justify-between mb-4">
                   <h3 className="text-sm font-extrabold text-slate-800 tracking-wide flex items-center gap-2">
                     <BarChart3 size={16} className="text-[#2353a4]"/> TABLEAUX DE BORD DÉCISIONNELS (POWER BI)
                   </h3>
                   <span className="text-[10px] bg-amber-100 text-amber-700 font-bold px-2 py-1 rounded">Intégration Microsoft</span>
                </div>
                
                <div className="flex-1 w-full bg-slate-100 rounded-xl border border-slate-200 overflow-hidden relative shadow-inner">
                  <iframe 
                    title="Dashboard" 
                    width="100%" 
                    height="100%" 
                    src="https://app.powerbi.com/view?r=eyJrIjoiODA1N2VhYTQtNGNmYS00OGMwLWJhMzgtMDJiOTNkYmI1ZGYwIiwidCI6IjJkYjU1MmVlLTA0ZDMtNDBjNC1iNGE2LTg3NDc0ZjA2YTZkNSIsImMiOjl9" 
                    frameBorder="0" 
                    allowFullScreen={true}
                    className="absolute inset-0 rounded-xl"
                  ></iframe>
                </div>
              </div>
            )}

            {activeTab === "HISTORIQUE" && (
              <div className="flex flex-col h-full animate-in fade-in duration-300">
                <div className="flex items-center justify-between mb-6">
                  <h3 className="text-sm font-extrabold text-slate-800 tracking-wide flex items-center gap-2">
                    <Clock size={16} className="text-[#2353a4]"/> REGISTRE D'AUDIT
                  </h3>
                  <span className="text-[10px] text-slate-500 font-semibold">{analysesHistory.length} entrée(s) stockée(s)</span>
                </div>

                {analysesHistory.length === 0 ? (
                  <div className="flex flex-col items-center justify-center flex-1 text-slate-400">
                    <FileText size={48} className="mb-3 opacity-30" />
                    <p className="text-sm font-medium">Aucun registre d'analyse détecté pour cette session.</p>
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
                                {record.type === 'batch' && 'Analyse Sémantique (CX)'}
                                {record.type === 'audio' && 'Analyse des Interactions'}
                                {record.type === 'rag' && 'Indexation Documentaire (RAG)'}
                              </p>
                              <div className="flex items-center gap-2 mt-1">
                                <span className="text-[10px] bg-slate-100 text-slate-600 px-2 py-0.5 rounded font-semibold flex items-center gap-1">
                                  <Clock size={10} /> {record.date}
                                </span>
                                <span className="text-[10px] text-slate-400 font-medium">Fichier: {record.filename}</span>
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
                          {record.type === 'batch' && record.data.summary_metrics && (
                            <div className="flex gap-6">
                              <span><strong>Lignes extraites:</strong> {record.data.summary_metrics.total_processed}</span>
                              <span><strong>Score NPS:</strong> <span className="text-[#2353a4] font-bold">{record.data.summary_metrics.nps_score}</span></span>
                            </div>
                          )}
                          {record.type === 'audio' && (
                            <p className="line-clamp-1 italic">"{record.data}"</p>
                          )}
                          {record.type === 'rag' && (
                            <p className="text-emerald-700 font-medium">Indexation des vecteurs complétée avec succès.</p>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}
            
          </div>
        </main>

        {/* ASIDE DROIT INITIAL (AVEC LA BARRE NOIRE LATERALE) */}
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
               <h3 className="font-extrabold text-slate-800 text-sm">Copilote Analytique</h3>
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
              <input type="text" value={chatInput} onChange={(e) => setChatInput(e.target.value)} placeholder="Interroger le modèle..." className="flex-1 bg-slate-100 border border-slate-200 rounded-full px-4 py-2 text-xs outline-none focus:ring-1 focus:ring-[#2353a4]" />
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