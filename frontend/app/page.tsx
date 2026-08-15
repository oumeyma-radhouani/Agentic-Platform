"use client";

import { useState, useEffect, useRef } from "react";
import { 
  Search, Grid3X3, Bell, HelpCircle, Settings, Plus, Play, 
  ArrowLeft, Tag, Mail, Phone, MessageSquare, Paperclip, 
  Send, Bot, ChevronDown, AlertCircle, Mic, Database, Sparkles, BrainCircuit, BarChart3, TrendingUp, Users, Target, Clock, FileText,
  Eye, Download, X, AlertTriangle, Euro, LogOut, UserRound, LockKeyhole
} from "lucide-react";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";
const POWER_BI_EMBED_URL = process.env.NEXT_PUBLIC_POWER_BI_EMBED_URL || "";

type ModuleReadiness = Record<string, { ready: boolean; reason?: string | null; index_type?: string }>;

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
    { sender: "copilot", text: "Bonjour. Je suis NOVA. Je suis prêt à analyser vos données et formuler des recommandations stratégiques." }
  ]);
  const chatEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    fetch(`${API_BASE_URL}/api/health`)
      .then((res) => res.json())
      .then((data) => {
        setModuleReadiness(data.modules || {});
        const modelReady = data.modules?.batch_enrichment?.ready;
        setBackendStatus(data.status === "online" ? (modelReady ? "Opérationnel" : "API seule") : "Hors ligne");
      })
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
        setLoginError("Le service d'authentification est indisponible. Vérifiez MONGO_URI et le backend.");
        setAuthStatus("anonymous");
      });
  }, []);

  useEffect(() => {
    if (!currentUser) return;
    const cachePrefix = `nova_${currentUser.id}`;
    setBatchResults(null);
    setAudioResult(null);
    setRagResult(null);
    setAnalysesHistory([]);
    try {
      const savedHistory = localStorage.getItem(`${cachePrefix}_analysesHistory`);
      if (savedHistory) setAnalysesHistory(JSON.parse(savedHistory));

      const savedBatch = localStorage.getItem(`${cachePrefix}_batchResultsSummary`);
      if (savedBatch) setBatchResults(JSON.parse(savedBatch));

      const savedAudio = localStorage.getItem(`${cachePrefix}_audioResult`);
      if (savedAudio) {
        const parsedAudio = JSON.parse(savedAudio);
        setAudioResult(typeof parsedAudio === "string" ? { transcript: parsedAudio, provider: "legacy", deployment: "unknown" } : parsedAudio);
      }

      const savedRag = localStorage.getItem(`${cachePrefix}_ragResult`);
      if (savedRag) setRagResult(JSON.parse(savedRag));
    } catch (error) {
      console.error("Erreur lors de la lecture du cache:", error);
    }

    fetch(`${API_BASE_URL}/api/chat/history`, { credentials: "include" })
      .then((res) => res.json())
      .then((data) => {
        if (data.success && data.messages?.length > 0) setChatMessages(data.messages);
      })
      .catch((error) => console.error("Impossible de charger l'historique", error));
  }, [currentUser]);

  useEffect(() => {
    if (batchResults && currentUser) {
      const summaryOnly = {
        ...batchResults,
        normalized_records: [],
        enriched_records: [],
        processed_records: [],
        errors: (batchResults.errors || []).slice(0, 20),
        records_omitted_from_browser_cache: true,
      };
      localStorage.setItem(`nova_${currentUser.id}_batchResultsSummary`, JSON.stringify(summaryOnly));
    }
  }, [batchResults, currentUser]);

  useEffect(() => {
    if (audioResult && currentUser) localStorage.setItem(`nova_${currentUser.id}_audioResult`, JSON.stringify(audioResult));
  }, [audioResult, currentUser]);

  useEffect(() => {
    if (ragResult && currentUser) localStorage.setItem(`nova_${currentUser.id}_ragResult`, JSON.stringify(ragResult));
  }, [ragResult, currentUser]);

  useEffect(() => {
    if (analysesHistory.length > 0 && currentUser) {
      const compactHistory = analysesHistory.map((record) => record.type === "batch" ? {
        ...record,
        data: {
          ...record.data,
          normalized_records: [],
          enriched_records: [],
          processed_records: [],
          review_queue: (record.data.review_queue || []).slice(0, 20),
          errors: (record.data.errors || []).slice(0, 20),
          records_omitted_from_browser_cache: true,
        }
      } : record);
      localStorage.setItem(`nova_${currentUser.id}_analysesHistory`, JSON.stringify(compactHistory));
    }
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
    setChatMessages([
      { sender: "copilot", text: "Bonjour. Je suis NOVA. Je peux vous aider à comprendre la qualité, les métriques et les enrichissements de vos données." }
    ]);
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
      if (!response.ok) {
        const message = response.status === 401
          ? "Nom d'utilisateur ou mot de passe incorrect."
          : response.status === 429
            ? "Trop de tentatives. Réessayez dans 15 minutes."
            : response.status === 503
              ? "Le service d'authentification est indisponible. Vérifiez MONGO_URI et le backend."
              : data.detail || "Connexion impossible.";
        throw new Error(message);
      }
      setCurrentUser(data.user);
      setAuthStatus("authenticated");
      setLoginPassword("");
    } catch (error) {
      setLoginError(error instanceof Error ? error.message : "Connexion impossible.");
    } finally {
      setLoginLoading(false);
    }
  };

  const handleLogout = async () => {
    try {
      await fetch(`${API_BASE_URL}/api/auth/logout`, {
        method: "POST",
        credentials: "include",
      });
    } finally {
      resetAuthenticatedState();
      setLoginUsername("");
      setLoginPassword("");
      setLoginError("");
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
        if (!res.ok) {
          const error = await res.json().catch(() => ({}));
          throw new Error(error.detail || "Erreur serveur");
        }
        const data = await res.json();
        
        setBatchResults(data.data);
        setAnalysesHistory(prev => [{ id: Date.now().toString(), type: "batch", filename: file.name, date: currentDate, data: data.data }, ...prev]);
        const flaggedCount = data.data.security_alert?.flagged_record_count || 0;
        const securityNotice = flaggedCount > 0
          ? ` Avertissement : ${flaggedCount} retour(s) ont été signalés par le contrôle anti-injection et placés dans la file de revue.`
          : "";
        setChatMessages(prev => [...prev, { sender: "copilot", text: `Traitement ${data.data.run_info.status} : ${data.data.data_quality.total_valid} lignes valides, ${data.data.data_quality.enrichment_succeeded} enrichies et ${data.data.data_quality.total_review_required ?? data.data.data_quality.predictions_review_required} à revoir.${securityNotice}` }]);
      
      } else if (activeTask === "audio") {
        const res = await fetch(`${API_BASE_URL}/api/audio`, { method: "POST", credentials: "include", body: formData });
        if (!res.ok) {
          const error = await res.json().catch(() => ({}));
          throw new Error(error.detail || "Erreur serveur");
        }
        const data = await res.json();
        
        setAudioResult(data.transcript);
        setAnalysesHistory(prev => [{ id: Date.now().toString(), type: "audio", filename: file.name, date: currentDate, data: data.transcript }, ...prev]);
        setChatMessages(prev => [...prev, { sender: "copilot", text: "L'analyse de l'interaction vocale est terminée." }]);
      
      } else if (activeTask === "rag") {
        const res = await fetch(`${API_BASE_URL}/api/rag`, { method: "POST", credentials: "include", body: formData });
        if (!res.ok) {
          const error = await res.json().catch(() => ({}));
          throw new Error(error.detail || "Erreur serveur");
        }
        const data = await res.json();
        
        setRagResult(data);
        setAnalysesHistory(prev => [{ id: Date.now().toString(), type: "rag", filename: file.name, date: currentDate, data: data }, ...prev]);
        setChatMessages(prev => [...prev, { sender: "copilot", text: `Le document stratégique "${data.filename}" a été assimilé.` }]);
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
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: userText })
      });
      const data = await res.json();
      if (res.status === 401) {
        resetAuthenticatedState();
        throw new Error("Session expirée");
      }
      if (!res.ok) throw new Error(data.detail || "Erreur serveur");
      setChatMessages(prev => [...prev, { sender: "copilot", text: data.response }]);
    } catch (error) {
      setChatMessages(prev => [...prev, { sender: "copilot", text: "Je rencontre des difficultés pour me connecter au réseau neuronal." }]);
    }
    setIsChatSending(false);
  };

  const handleDownload = (record: AnalysisRecord) => {
    let content = "";
    if (record.type === "batch") {
      content = JSON.stringify({
        dataset_manifest: record.data.dataset_manifest,
        data_quality: record.data.data_quality,
        summary_metrics: record.data.summary_metrics,
        normalized_records: record.data.normalized_records,
        enriched_records: record.data.enriched_records,
        review_queue: record.data.review_queue,
        security_alert: record.data.security_alert,
        rejected_records: record.data.rejected_records,
        evidence_insights: record.data.evidence_insights,
        errors: record.data.errors,
        run_info: record.data.run_info,
      }, null, 2);
      mimeType = "application/json;charset=utf-8";
      extension = "json";
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

  if (authStatus === "checking") {
    return (
      <div className="min-h-screen bg-[#020617] text-white flex items-center justify-center">
        <div className="flex items-center gap-3 text-sm font-semibold text-white/80">
          <Sparkles size={20} className="text-[#f37021] animate-pulse" />
          Vérification de la session NOVA…
        </div>
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
            <p className="text-sm text-white/65 mt-2">Connectez-vous pour accéder à vos analyses et documents.</p>
          </div>

          <form onSubmit={handleLogin} className="px-8 py-8 space-y-5">
            <div>
              <label htmlFor="username" className="block text-xs font-bold text-slate-700 mb-2">Nom d'utilisateur</label>
              <div className="relative">
                <UserRound size={17} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400" />
                <input
                  id="username"
                  name="username"
                  autoComplete="username"
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
                  autoComplete="current-password"
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

            <button
              type="submit"
              disabled={loginLoading || !loginUsername.trim() || !loginPassword}
              className="w-full rounded-xl bg-[#2353a4] hover:bg-[#1a4082] disabled:bg-slate-300 text-white py-3 text-sm font-bold transition-colors shadow-lg shadow-blue-900/15"
            >
              {loginLoading ? "Connexion…" : "Se connecter"}
            </button>
            <p className="text-[11px] text-center text-slate-400">Les comptes sont créés par un administrateur NOVA.</p>
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

                  {viewingRecord.data.evidence_insights?.findings?.length > 0 && (
                    <div className="mt-6">
                      <p className="font-bold text-[#2353a4] uppercase text-xs tracking-wide border-b pb-2 mb-3">Constats traçables</p>
                      <div className="space-y-3">
                        {viewingRecord.data.evidence_insights.findings.map((finding: any) => (
                          <div key={finding.finding_id} className="bg-blue-50/50 p-4 rounded-lg border border-blue-100">
                            <p className="font-bold text-slate-800">{finding.title}</p>
                            <p className="mt-1 text-xs">{finding.statement}</p>
                            <p className="mt-2 text-[10px] text-slate-500">Base : {finding.denominator} lignes • {finding.caveats.join(" • ")}</p>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {viewingRecord.data.security_alert?.detected && (
                    <div role="alert" className="mt-6 rounded-xl border border-rose-300 bg-rose-50 p-4 text-rose-900">
                      <p className="font-extrabold text-xs uppercase tracking-wide flex items-center gap-2">
                        <AlertTriangle size={16} /> Contenu potentiellement malveillant signalé
                      </p>
                      <p className="mt-2 text-xs leading-relaxed">
                        {viewingRecord.data.security_alert.flagged_record_count} retour(s) ont été isolés du traitement ML et ajoutés à la file de revue. Ce signal nécessite une vérification humaine et ne prouve pas à lui seul une attaque.
                      </p>
                    </div>
                  )}

                  {viewingRecord.data.review_queue?.length > 0 && (
                    <div className="mt-6">
                      <p className="font-bold text-amber-800 uppercase text-xs tracking-wide border-b pb-2 mb-3">File de revue ({viewingRecord.data.review_queue.length})</p>
                      <div className="space-y-3">
                        {viewingRecord.data.review_queue.slice(0, 10).map((item: any) => (
                          <div key={item.feedback_id} className="bg-amber-50 p-3 rounded-lg border border-amber-200 text-xs">
                            <p className="font-bold text-slate-800">{item.feedback_id} • {item.predicted_theme_id || "NON ANALYSÉ"}</p>
                            <p className="mt-1 text-slate-600">{item.comment}</p>
                            <p className="mt-2 text-amber-800">Motif : {item.review_reason}</p>
                          </div>
                        ))}
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
            <span className="hidden sm:inline">Déconnexion</span>
          </button>
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
              <Tab label="RAPPORT CLASSIQUE" active={activeTab === "RAPPORTS"} />
            </button>
            <button onClick={() => setActiveTab("DASHBOARDS")} className="outline-none">
              <Tab label="TABLEAUX DE BORD" active={activeTab === "DASHBOARDS"} />
            </button>
            <button onClick={() => setActiveTab("HISTORIQUE")} className="outline-none">
              <Tab label="HISTORIQUE" active={activeTab === "HISTORIQUE"} />
            </button>
          </div>

          <div className="flex-1 overflow-y-auto p-6 relative bg-slate-50/30">
            
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
                        
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-5 pb-5 border-b border-slate-100">
                          <div className="bg-slate-50 p-3 rounded-lg text-center border border-slate-100 shadow-sm">
                            <p className="text-[10px] text-slate-500 font-bold uppercase tracking-wider mb-1">Score NPS Global</p>
                            <p className="text-2xl font-extrabold text-[#2353a4]">{batchResults.summary_metrics.nps_score}</p>
                          </div>
                          <div className="bg-rose-50/30 p-3 rounded-lg text-center border border-rose-100 shadow-sm">
                            <p className="text-[10px] text-rose-600 font-bold uppercase tracking-wider mb-1">CA Menacé (Churn)</p>
                            <p className="text-xl font-extrabold text-rose-600 mt-1">
                              {batchResults.strategic_insights?.bi_metrics?.revenue_at_risk_eur?.toLocaleString('fr-FR') || "0"} €
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
                            <p className="text-[10px] text-slate-500 font-bold uppercase tracking-wider mb-1">Enrichissements ML</p>
                            <p className="text-xl font-extrabold text-[#f37021] mt-1">{batchResults.data_quality?.predictions_ready || 0}</p>
                            <p className="text-[9px] text-slate-500 font-bold mt-1">À revoir : {batchResults.data_quality?.total_review_required ?? batchResults.data_quality?.predictions_review_required ?? 0} • Échecs : {batchResults.data_quality?.enrichment_failed || 0}</p>
                          </div>
                        </div>

                        <div className="bg-amber-50/50 p-4 rounded-lg border border-amber-100 text-sm text-slate-700 mb-4">
                           <p className="font-bold text-amber-800 mb-2 flex items-center gap-2"><AlertTriangle size={14}/> Contrôles de qualité :</p>
                           <ul className="space-y-2 text-xs leading-relaxed">
                              {(batchResults.data_quality?.warnings || []).map((warning: any, i: number) => (
                                 <li key={i}><strong>{warning.code} :</strong> {warning.message}</li>
                              ))}
                              {(batchResults.data_quality?.warnings || []).length === 0 && <li>Aucun problème détecté par les contrôles actuels.</li>}
                           </ul>
                        </div>

                        <div className="bg-blue-50/50 p-4 rounded-lg border border-blue-100 text-sm text-slate-700 mb-4">
                           <p className="font-bold text-[#2353a4] mb-2 flex items-center gap-2"><Sparkles size={14}/> Constats descriptifs et traçables :</p>
                           <ul className="space-y-3 text-xs leading-relaxed">
                              {(batchResults.evidence_insights?.findings || []).map((finding: any) => (
                                 <li key={finding.finding_id}>
                                   <strong>{finding.title} :</strong> {finding.statement}
                                   <span className="block text-[10px] text-slate-500 mt-1">Base : {finding.denominator} lignes • {finding.caveats.join(" • ")}</span>
                                 </li>
                              ))}
                              {(batchResults.evidence_insights?.findings || []).length === 0 && <li>Pas assez de prédictions valides pour produire un constat.</li>}
                           </ul>
                        </div>

                        {batchResults.security_alert?.detected && (
                          <div role="alert" className="bg-rose-50 p-4 rounded-lg border-2 border-rose-300 text-sm text-rose-900 mb-4 shadow-sm">
                            <p className="font-extrabold mb-2 flex items-center gap-2">
                              <AlertTriangle size={18} /> Avertissement de sécurité — contenu signalé
                            </p>
                            <p className="text-xs leading-relaxed">
                              {batchResults.security_alert.flagged_record_count} retour(s) présentent des indicateurs possibles d'injection de prompt. Ils ont été conservés dans les données source, exclus de l'enrichissement ML et ajoutés à la file de revue pour vérification humaine.
                            </p>
                            <p className="text-[10px] mt-2 text-rose-700 font-semibold">
                              Un signalement n'est pas une preuve d'attaque : vérifiez les éléments concernés dans l'aperçu détaillé.
                            </p>
                          </div>
                        )}
                        
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
                      <p className="text-sm font-bold text-[#2353a4] mb-1">Assimilation Stratégique</p>
                      <p className="text-xs text-slate-500 mb-4 font-medium">Le document a été converti en base de connaissances décisionnelle.</p>
                      <div className="flex items-center gap-2 bg-emerald-50 text-emerald-700 border border-emerald-200 p-3 rounded-lg text-sm mb-4"><Sparkles size={18} /> Les données de <strong>{ragResult.filename}</strong> sont prêtes.</div>
                      <div className="flex gap-3 justify-end border-t border-slate-100 pt-4">
                        <button onClick={() => setViewingRecord(activeRecord)} className="flex items-center gap-2 px-3 py-2 bg-white border border-slate-200 text-slate-700 rounded-lg text-xs font-bold hover:bg-slate-50 transition-colors shadow-sm"><Eye size={14} /> Aperçu détaillé</button>
                        <button onClick={() => handleDownload(activeRecord)} className="flex items-center gap-2 px-3 py-2 bg-[#2353a4] text-white rounded-lg text-xs font-bold hover:bg-blue-800 transition-colors shadow-sm"><Download size={14} /> Exporter (.txt)</button>
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

            {/* ====== RETOUR DU DASHBOARD POWER BI ====== */}
            {activeTab === "DASHBOARDS" && (
              <div className="flex flex-col h-full animate-in fade-in duration-300">
                <div className="flex items-center justify-between mb-4">
                   <h3 className="text-sm font-extrabold text-slate-800 tracking-wide flex items-center gap-2">
                     <BarChart3 size={16} className="text-[#2353a4]"/> VISION MACRO & KPIS STRATÉGIQUES (POWER BI)
                   </h3>
                   <span className="text-[10px] bg-amber-100 text-amber-700 font-bold px-2 py-1 rounded">Intégration Microsoft</span>
                </div>
                
                <div className="flex-1 w-full bg-slate-100 rounded-xl border border-slate-200 overflow-hidden relative shadow-inner">
                  <iframe 
                    title="Dashboard_Strategique_CloudShift" 
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