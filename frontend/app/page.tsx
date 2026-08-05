"use client";

import { useState, useEffect } from "react";
import { 
  Search, Grid3X3, Bell, HelpCircle, Settings, Plus, Play, 
  ArrowLeft, Tag, Mail, Phone, MessageSquare, Paperclip, 
  Send, Bot, ChevronDown, CheckCircle2, AlertCircle 
} from "lucide-react";

export default function Dashboard() {
  const [activeTab, setActiveTab] = useState("CHRONOLOGIE");
  const [backendStatus, setBackendStatus] = useState("Connexion...");
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState<any>(null);

  useEffect(() => {
    fetch("http://localhost:8000/api/health")
      .then((res) => res.json())
      .then((data) => setBackendStatus(data.status === "online" ? "Connecté" : "Hors ligne"))
      .catch(() => setBackendStatus("Déconnecté"));
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
    } catch (error) {
      console.error(error);
    }
    setLoading(false);
  };

  return (
    <div 
      className="flex flex-col h-screen w-full font-sans overflow-hidden bg-cover bg-center bg-no-repeat"
      style={{ backgroundImage: "url('/background_gradiant.jpg')" }}
    >
      {/* Couche d'assombrissement optionnelle pour garantir la lisibilité */}
      <div className="absolute inset-0 bg-black/20 z-0 pointer-events-none"></div>
      
      {/* 1. TOP BAR */}
      <header className="h-14 bg-slate-900/90 backdrop-blur-md flex items-center justify-between px-4 shrink-0 text-white shadow-md z-20 border-b border-white/10">
        <div className="flex items-center gap-4">
          <Grid3X3 size={20} className="text-white/80 hover:text-white cursor-pointer" />
          <div className="flex items-center gap-2">
             <div className="w-7 h-7 bg-white rounded flex items-center justify-center font-bold text-[#2353a4] shadow-sm">
               C<span className="text-[#f37021]">S</span>
             </div>
             <span className="font-bold tracking-wide text-lg hidden sm:block drop-shadow-sm">CloudShift</span>
          </div>
          
          <div className="flex items-center gap-3 ml-4">
            <button className="w-8 h-8 rounded-full bg-white/10 hover:bg-white/20 flex items-center justify-center transition-colors">
              <Play size={14} className="text-white fill-current" />
            </button>
            <button className="w-8 h-8 rounded-full bg-white/10 hover:bg-white/20 flex items-center justify-center transition-colors">
              <Plus size={16} />
            </button>
            <div className="flex items-center bg-white/10 rounded-md px-3 py-1.5 ml-2 border border-white/10 w-64 shadow-inner">
              <Search size={14} className="text-white/60 mr-2" />
              <input 
                type="text" 
                placeholder="Rechercher..." 
                className="bg-transparent border-none outline-none text-sm text-white placeholder-white/60 w-full"
              />
            </div>
          </div>
        </div>

        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2 text-[10px] uppercase tracking-wider font-semibold bg-white/10 px-2 py-1 rounded shadow-inner border border-white/5">
            <span className={`w-1.5 h-1.5 rounded-full shadow-sm ${backendStatus === "Connecté" ? "bg-emerald-400" : "bg-rose-400"}`}></span>
            API: {backendStatus}
          </div>
          <Grid3X3 size={18} className="text-white/80 cursor-pointer" />
          <div className="relative cursor-pointer">
            <Bell size={18} className="text-white/80" />
            <span className="absolute -top-1 -right-1 w-2 h-2 bg-[#f37021] rounded-full shadow-sm"></span>
          </div>
          <HelpCircle size={18} className="text-white/80 cursor-pointer" />
          <Settings size={18} className="text-white/80 cursor-pointer" />
          <div className="w-7 h-7 rounded-full bg-slate-300 overflow-hidden cursor-pointer border border-white/20 shadow-sm">
            <img src="https://api.dicebear.com/7.x/avataaars/svg?seed=Admin" alt="Profil" />
          </div>
        </div>
      </header>

      {/* 2. ESPACE DE TRAVAIL (3 Colonnes translucides) */}
      <div className="flex-1 flex gap-4 p-4 overflow-hidden z-10">
        
        {/* COLONNE GAUCHE */}
        <aside className="w-[320px] flex flex-col gap-4 overflow-y-auto shrink-0 pb-4">
          
          <div className="bg-white/95 backdrop-blur-md rounded-xl shadow-lg border border-white/20 p-4">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2 cursor-pointer text-slate-800 hover:text-[#2353a4] transition-colors">
                <ArrowLeft size={18} />
                <h1 className="text-xl font-semibold">Analyse de Lot</h1>
              </div>
              <span className="text-xs font-medium text-slate-500 cursor-pointer hover:text-slate-700">Fermer</span>
            </div>
            
            <div className="flex items-center gap-2 text-xs text-[#2353a4] font-medium mb-6 cursor-pointer bg-blue-50/80 w-fit px-2 py-1 rounded border border-blue-100">
              <Tag size={12} /> Ajouter un tag
            </div>

            <div className="flex gap-4 mb-6">
              <div className="w-16 h-16 bg-gradient-to-br from-[#2353a4]/10 to-[#2353a4]/20 rounded-xl flex items-center justify-center border border-[#2353a4]/10">
                <Bot size={32} className="text-[#2353a4]" />
              </div>
              <div>
                <h2 className="font-bold text-slate-800">Agent CloudShift</h2>
                <p className="text-xs text-slate-500">Aujourd'hui à {new Date().toLocaleTimeString('fr-FR', {hour: '2-digit', minute:'2-digit'})}</p>
                <p className="text-xs text-slate-500 mt-1 font-medium">Plateforme Agentique</p>
              </div>
            </div>

            <div className="space-y-4 border-t border-slate-100 pt-4">
              <div>
                <p className="text-[11px] text-slate-400 uppercase tracking-wider mb-1 font-semibold">Type de tâche</p>
                <p className="text-sm text-slate-800 font-medium">Traitement de feedback client</p>
              </div>
              <div>
                <p className="text-[11px] text-slate-400 uppercase tracking-wider mb-1 font-semibold">Source de données</p>
                <p className="text-sm text-[#f37021] font-semibold flex items-center gap-2">
                  <Mail size={14} /> Fichier JSONL / JSON
                </p>
              </div>
            </div>
          </div>

          <div className="bg-white/95 backdrop-blur-md rounded-xl shadow-lg border border-white/20 overflow-hidden">
             <div className="p-3 border-b border-slate-100 flex justify-between items-center bg-slate-50/50">
                <span className="text-xs font-bold text-slate-600 uppercase tracking-wider">Configuration du lot</span>
                <ChevronDown size={14} className="text-slate-400" />
             </div>
             <div className="p-4">
                <form onSubmit={handleUpload} className="flex flex-col gap-4">
                  <div className="border-2 border-dashed border-slate-200 rounded-xl p-4 text-center bg-slate-50/50 hover:bg-blue-50/30 transition-colors">
                    <input
                      type="file"
                      accept=".json,.jsonl"
                      onChange={(e) => setFile(e.target.files?.[0] || null)}
                      className="block w-full text-xs text-slate-500 file:mr-3 file:py-1.5 file:px-3 file:rounded-md file:border-0 file:text-xs file:font-semibold file:bg-[#2353a4]/10 file:text-[#2353a4] hover:file:bg-[#2353a4]/20 cursor-pointer transition-colors"
                    />
                  </div>
                  <button
                    type="submit"
                    disabled={!file || loading}
                    className="w-full bg-[#f37021] hover:bg-[#d95d13] disabled:bg-slate-300 text-white text-sm font-bold py-2.5 rounded-lg transition-all shadow-md hover:shadow-lg"
                  >
                    {loading ? "Analyse en cours..." : "Lancer l'analyse"}
                  </button>
                </form>
             </div>
          </div>
        </aside>

        {/* COLONNE CENTRALE */}
        <main className="flex-1 bg-white/95 backdrop-blur-md rounded-xl shadow-lg border border-white/20 flex flex-col min-w-[400px] overflow-hidden">
          
          <div className="flex items-center px-4 pt-2 border-b border-slate-200 overflow-x-auto bg-white/50">
            <Tab label="INFOS GÉNÉRALES" active={activeTab === "INFOS"} onClick={() => setActiveTab("INFOS")} />
            <Tab label="CHRONOLOGIE" active={activeTab === "CHRONOLOGIE"} onClick={() => setActiveTab("CHRONOLOGIE")} />
            <Tab label="STATISTIQUES" active={activeTab === "STATS"} onClick={() => setActiveTab("STATS")} />
            <Tab label="RECOMMANDATIONS" active={activeTab === "REC"} onClick={() => setActiveTab("REC")} />
          </div>

          <div className="flex items-center justify-between p-3 border-b border-slate-100 bg-slate-50/50">
            <div className="flex items-center gap-4 text-xs font-semibold text-slate-600">
              <span className="flex items-center gap-1 cursor-pointer hover:text-[#2353a4] transition-colors"><Settings size={14}/> Filtrer la période</span>
              <span className="flex items-center gap-1 cursor-pointer hover:text-[#2353a4] transition-colors"><Bot size={14}/> Propriétaire</span>
            </div>
            <div className="flex items-center gap-2 text-xs text-slate-400">
              <Search size={14} className="hover:text-slate-600 cursor-pointer" />
              <ArrowLeft size={14} className="rotate-270 cursor-pointer hover:text-slate-600" />
            </div>
          </div>

          <div className="flex-1 overflow-y-auto p-6">
            
            <h3 className="text-sm font-extrabold text-slate-800 mb-6 tracking-wide">{new Date().toLocaleDateString('fr-FR', {month: 'long', year: 'numeric'}).toUpperCase()}</h3>

            {!results && !loading && (
              <div className="flex flex-col items-center justify-center h-64 text-slate-400">
                <Bot size={48} className="mb-3 opacity-30" />
                <p className="text-sm font-medium">En attente des données clients...</p>
              </div>
            )}

            {loading && (
              <div className="flex flex-col items-center justify-center h-64 text-[#2353a4]">
                <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-[#2353a4] mb-4"></div>
                <p className="text-sm font-semibold">L'Agent CloudShift analyse les requêtes...</p>
              </div>
            )}

            {results && !loading && (
              <div className="space-y-8 animate-in fade-in duration-500">
                
                {/* Carte de Chronologie 1 */}
                <div className="flex gap-4">
                  <div className="w-9 h-9 rounded-full bg-blue-50 flex items-center justify-center shrink-0 mt-1 border border-blue-100 shadow-sm">
                    <Bot size={18} className="text-[#2353a4]" />
                  </div>
                  <div className="flex-1">
                    <p className="text-sm text-slate-800">
                      <span className="font-bold text-[#2353a4]">Agent CloudShift</span> a terminé l'analyse du lot <span className="text-slate-400 font-medium ml-1">Superviseur</span>
                    </p>
                    <p className="text-xs text-slate-400 mb-2 font-medium">Aujourd'hui à {new Date().toLocaleTimeString('fr-FR', {hour: '2-digit', minute:'2-digit'})}</p>
                    <p className="text-sm text-slate-700 leading-relaxed mb-2 bg-slate-50/50 p-3 rounded-lg border border-slate-100">
                      Le lot contenant <strong className="text-slate-900">{results.summary_metrics.total_processed} retours clients</strong> a été traité avec succès. Les scores NPS ont été recalculés et les thèmes principaux ont été extraits de manière autonome.
                    </p>
                    <span className="text-xs text-[#2353a4] font-semibold cursor-pointer hover:underline flex items-center gap-1">
                      <ChevronDown size={14}/> Voir les détails techniques
                    </span>
                  </div>
                </div>

                {/* Carte de Chronologie 2 */}
                <div className="flex gap-4">
                  <div className="w-9 h-9 rounded-full bg-[#f37021] flex items-center justify-center shrink-0 mt-1 shadow-md">
                    <AlertCircle size={18} className="text-white" />
                  </div>
                  <div className="flex-1 bg-white border border-slate-200 rounded-xl p-5 shadow-sm hover:shadow-md transition-shadow">
                    <p className="text-sm font-bold text-[#2353a4] hover:underline cursor-pointer mb-1">
                      Rapport d'Analyse : {results.summary_metrics.total_detractors} Détracteurs identifiés
                    </p>
                    <p className="text-xs text-slate-500 mb-5 font-medium">Système IA | Statut: <span className="text-[#f37021] font-bold">Action requise</span></p>
                    
                    <div className="grid grid-cols-3 gap-4 mb-5 pb-5 border-b border-slate-100">
                      <div className="bg-slate-50 p-3 rounded-lg text-center border border-slate-100">
                        <p className="text-[10px] text-slate-500 font-bold uppercase tracking-wider mb-1">Promoteurs</p>
                        <p className="text-2xl font-extrabold text-emerald-600">{results.summary_metrics.total_promoters}</p>
                      </div>
                      <div className="bg-slate-50 p-3 rounded-lg text-center border border-slate-100">
                        <p className="text-[10px] text-slate-500 font-bold uppercase tracking-wider mb-1">Passifs</p>
                        <p className="text-2xl font-extrabold text-amber-500">{results.summary_metrics.total_passives}</p>
                      </div>
                      <div className="bg-slate-50 p-3 rounded-lg text-center border border-slate-100 ring-1 ring-[#2353a4]/20">
                        <p className="text-[10px] text-slate-500 font-bold uppercase tracking-wider mb-1">NPS Global</p>
                        <p className="text-2xl font-extrabold text-[#2353a4]">{results.summary_metrics.nps_score}</p>
                      </div>
                    </div>
                    
                    <p className="text-sm text-slate-700 mb-3 leading-relaxed">
                      <strong>Description :</strong> Une proportion importante des commentaires négatifs pointe vers des temps de chargement lents. L'agent recommande d'assigner ces tickets au niveau 2 du support technique immédiatement.
                    </p>
                    <span className="text-xs text-[#2353a4] font-semibold cursor-pointer hover:underline">
                      Lire la suite du rapport
                    </span>
                  </div>
                </div>

              </div>
            )}
          </div>
        </main>

        {/* COLONNE DROITE (Chat Copilot) */}
        <aside className="w-[340px] bg-white/95 backdrop-blur-md rounded-xl shadow-lg border border-white/20 flex shrink-0 overflow-hidden">
          
          <div className="w-12 bg-slate-900/95 flex flex-col items-center py-4 gap-6 shrink-0 border-r border-slate-800">
            <div className="w-8 h-8 rounded-lg bg-white/10 flex items-center justify-center cursor-pointer hover:bg-[#f37021] transition-all">
              <Phone size={16} className="text-white" />
            </div>
            <div className="w-8 h-8 rounded-lg flex items-center justify-center cursor-pointer hover:bg-[#f37021] transition-all">
              <Mail size={16} className="text-white/60 hover:text-white" />
            </div>
            <div className="w-8 h-8 rounded-lg bg-[#f37021] flex items-center justify-center cursor-pointer relative shadow-md">
              <MessageSquare size={16} className="text-white" />
              <span className="absolute -top-1 -right-1 w-2.5 h-2.5 bg-rose-500 border-2 border-slate-900 rounded-full"></span>
            </div>
          </div>

          <div className="flex-1 flex flex-col bg-white/50">
            <div className="p-3 border-b border-slate-100 flex items-center justify-between bg-white/80">
              <span className="text-[#2353a4] text-xs font-bold flex items-center gap-1 cursor-pointer hover:text-[#1a4082]">
                <ArrowLeft size={14} /> Retour
              </span>
              <div className="flex items-center gap-2 text-slate-400">
                <Bot size={16} className="text-[#2353a4] bg-blue-50 p-1.5 rounded-full box-content border border-blue-100" />
                <span className="text-lg pb-2 font-bold tracking-widest">...</span>
              </div>
            </div>

            <div className="flex flex-col items-center py-6 border-b border-slate-100 bg-white/40">
               <div className="w-14 h-14 bg-gradient-to-br from-[#2353a4] to-[#1a4082] rounded-full flex items-center justify-center mb-3 shadow-md border-2 border-white">
                 <Bot size={28} className="text-white" />
               </div>
               <h3 className="font-extrabold text-slate-800 text-lg">NOVA Copilot</h3>
               <p className="text-[11px] text-[#2353a4] font-semibold cursor-pointer mt-0.5">Assistant IA CloudShift &gt;</p>
            </div>

            <div className="flex-1 p-4 overflow-y-auto space-y-5 bg-slate-50/50">
               
               <div className="flex justify-center">
                 <span className="text-[9px] text-slate-400 font-bold uppercase tracking-widest bg-white px-3 py-1 rounded-full border border-slate-200 shadow-sm">Résumé pré-chat</span>
               </div>

               <div className="flex justify-end">
                 <div className="bg-slate-800 text-white text-sm p-3.5 rounded-2xl rounded-tr-sm shadow-md max-w-[85%] leading-relaxed">
                   Pouvez-vous analyser le dernier lot de données clients et en extraire les recommandations ?
                 </div>
               </div>
               <p className="text-[10px] text-right font-medium text-slate-400 -mt-3.5 pr-2">Admin à {new Date().toLocaleTimeString('fr-FR', {hour: '2-digit', minute:'2-digit'})}</p>

               {results && (
                 <div className="animate-in fade-in slide-in-from-bottom-2 duration-500 delay-300">
                   <div className="flex items-end gap-2">
                     <div className="w-7 h-7 rounded-full bg-gradient-to-br from-[#2353a4] to-[#1a4082] flex items-center justify-center shrink-0 mb-1 shadow-sm">
                        <Bot size={14} className="text-white" />
                     </div>
                     <div className="bg-white border border-slate-200 text-slate-700 text-sm p-4 rounded-2xl rounded-tl-sm shadow-md max-w-[85%] leading-relaxed">
                       Bien sûr. Les informations ont été fournies ! Le lot actuel de <strong>{results.summary_metrics.total_processed} retours</strong> a été analysé. Le score NPS calculé est de <strong className="text-[#2353a4]">{results.summary_metrics.nps_score}</strong>.
                       <br/><br/>
                       Voulez-vous que je génère des brouillons d'e-mails pour les <strong className="text-rose-500">{results.summary_metrics.total_detractors} détracteurs</strong> ?
                     </div>
                   </div>
                   <p className="text-[10px] text-left font-medium text-slate-400 mt-1.5 pl-9">Copilot à {new Date().toLocaleTimeString('fr-FR', {hour: '2-digit', minute:'2-digit'})}</p>
                 </div>
               )}
            </div>

            <div className="p-3 bg-white border-t border-slate-200 flex items-center gap-2">
              <Paperclip size={20} className="text-slate-400 cursor-pointer hover:text-slate-600 transition-colors" />
              <input 
                type="text" 
                placeholder="Écrivez un message..." 
                className="flex-1 bg-slate-100 border border-slate-200 rounded-full px-4 py-2.5 text-sm outline-none focus:ring-2 focus:ring-[#2353a4] focus:bg-white transition-all shadow-inner"
              />
              <div className="w-9 h-9 rounded-full bg-[#2353a4] flex items-center justify-center cursor-pointer shadow-md hover:bg-[#1a4082] transition-colors">
                <Send size={16} className="text-white -ml-0.5" />
              </div>
            </div>
          </div>

        </aside>

      </div>
    </div>
  );
}

function Tab({ label, active, onClick }: any) {
  return (
    <div 
      onClick={onClick}
      className={`px-5 py-3.5 text-[11px] font-extrabold tracking-widest cursor-pointer border-b-[3px] transition-colors whitespace-nowrap ${
        active ? 'border-[#f37021] text-slate-900 bg-white/50' : 'border-transparent text-slate-500 hover:text-slate-800 hover:bg-white/30'
      }`}
    >
      {label}
    </div>
  );
}