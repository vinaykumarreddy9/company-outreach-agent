import React, { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useParams, useNavigate } from 'react-router-dom';
import {
    Users,
    ChevronLeft,
    Loader2,
    ShieldCheck,
    Zap,
    Globe,
    ArrowRight,
    Mail,
    Target,
    CheckCircle,
    Telescope,
    Sparkles,
    Activity,
    X,
    Maximize2,
    Linkedin,
    Save,
    Edit3,
    UserCircle2,
    PhoneCall,
    History,
    MessageSquare,
    FileEdit,
    Trash2
} from 'lucide-react';
import { Button } from '../components/Button';
import axios from 'axios';
import { cn } from '../lib/utils';
import API_BASE_URL from '../apiConfig';

const CampaignWorkspace = () => {
    const { campaign_id } = useParams();
    const navigate = useNavigate();
    
    // Core State
    const [data, setData] = useState({
        campaign: null,
        companies: [],
        decision_makers: [],
        emails: []
    });
    const [isLoading, setIsLoading] = useState(true);
    const [isLaunching, setIsLaunching] = useState(false);
    const [isSaving, setIsSaving] = useState(false);
    const [query, setQuery] = useState('');
    const [modalContent, setModalContent] = useState(null);
    const [activeView, setActiveView] = useState('research');
    const [isDispatching, setIsDispatching] = useState(false);
    const [isPolling, setIsPolling] = useState(false);
    const [hasUserNavigated, setHasUserNavigated] = useState(false);
    
    const fetchCampaignData = useCallback(async () => {
        try {
            const response = await axios.get(`${API_BASE_URL}campaigns/${campaign_id}`);
            const apiData = response.data;
            if (apiData.error) return;
            setData(apiData);
            
            // Auto-switch to monitor view if already in monitoring status and user hasn't navigated elsewhere
            if (!hasUserNavigated && (apiData.campaign?.status === 'MONITORING_READY' || apiData.campaign?.status === 'MONITORING_ACTIVE')) {
                if (activeView !== 'monitor') {
                    setActiveView('monitor');
                }
            }
            
            setIsLoading(false);
        } catch (error) {
            console.error('Error fetching campaign:', error);
            setIsLoading(false);
        }
    }, [campaign_id, activeView, hasUserNavigated]);


    useEffect(() => {
        fetchCampaignData();
    }, [fetchCampaignData]);

    useEffect(() => {
        let interval;
        const needsPolling = isLaunching || 
                          isPolling ||
                          data.campaign?.status === 'MONITORING_ACTIVE' ||
                          (data.campaign?.value_proposition && data.emails.length === 0);

        if (needsPolling) {
            interval = setInterval(fetchCampaignData, 5000);
        }
        return () => clearInterval(interval);
    }, [isLaunching, isPolling, fetchCampaignData, data.campaign?.status, data.campaign?.value_proposition, data.emails.length]);

    const handleLaunch = async () => {
        if (!query.trim()) return;
        setIsLaunching(true);
        try {
            await axios.post(`${API_BASE_URL}campaigns/${campaign_id}/launch`, { 
                query: query.trim() 
            });
            setIsPolling(true);
        } catch (error) {
            console.error('Launch failed:', error);
        } finally {
            setIsLaunching(false);
        }
    };


    const handleApproveEmail = async (emailId) => {
        try {
            await axios.post(`${API_BASE_URL}emails/${emailId}/approve`);
            await fetchCampaignData();
        } catch (error) {
            console.error('Failed to approve email:', error);
        }
    };

    const handleDeclineEmail = async (emailId) => {
        try {
            await axios.post(`${API_BASE_URL}emails/${emailId}/decline`);
            await fetchCampaignData();
        } catch (error) {
            console.error('Failed to decline email:', error);
        }
    };

    const handleBatchDispatch = async () => {
        setIsDispatching(true);
        try {
            await axios.post(`${API_BASE_URL}campaigns/${campaign_id}/batch-send`);
            await fetchCampaignData();
        } catch (error) {
            console.error('Batch dispatch failed:', error);
        } finally {
            setIsDispatching(false);
        }
    };

    const handleSaveEmail = async () => {
        if (!modalContent || modalContent.type !== 'email') return;
        setIsSaving(true);
        try {
            // 1. Update Email Content
            await axios.patch(`${API_BASE_URL}emails/${modalContent.id}`, {
                subject: modalContent.subtitle,
                body: modalContent.body,
                recipient: modalContent.recipient_email
            });

            // 2. Update DM Email if changed
            if (modalContent.recipient_email) {
                await axios.patch(`${API_BASE_URL}decision-makers/${modalContent.dm_id}`, {
                    email: modalContent.recipient_email
                });
            }

            await fetchCampaignData();
            setModalContent(null);
        } catch (error) {
            console.error('Failed to save changes:', error);
            alert("Failed to save changes. Please try again.");
        } finally {
            setIsSaving(false);
        }
    };

    const handleSaveDM = async () => {
        if (!modalContent || modalContent.type !== 'person') return;
        setIsSaving(true);
        try {
            await axios.patch(`${API_BASE_URL}decision-makers/${modalContent.id}`, {
                email: modalContent.email
            });
            await fetchCampaignData();
            setModalContent(null);
        } catch (error) {
            console.error('Failed to update lead:', error);
            alert("Failed to update lead information.");
        } finally {
            setIsSaving(false);
        }
    };

    const handleSendDiscovery = async () => {
        if (!modalContent || modalContent.type !== 'discovery') return;
        setIsSaving(true);
        try {
            await axios.post(`${API_BASE_URL}decision-makers/${modalContent.dm_id}/send-discovery`, {
                subject: modalContent.subject,
                body: modalContent.body
            });
            await fetchCampaignData();
            setModalContent(null);
        } catch (error) {
            console.error('Failed to send discovery:', error);
            alert("Failed to dispatch discovery invitation. Please try again.");
        } finally {
            setIsSaving(false);
        }
    };

    if (isLoading) {
        return (
            <div className="min-h-screen flex items-center justify-center bg-slate-50">
                <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
            </div>
        );
    }

    const hasMission = data.campaign?.value_proposition;
    const isMonitoring = data.campaign?.status === 'MONITORING_READY' || data.campaign?.status === 'MONITORING_ACTIVE';

    return (
        <div className="min-h-screen bg-slate-50 text-slate-900 flex flex-col font-sans">
            {/* Modal Overlay */}
            <AnimatePresence>
                {modalContent && (
                    <div className="fixed inset-0 z-[100] flex items-center justify-center p-4 md:p-8">
                        <motion.div 
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            exit={{ opacity: 0 }}
                            onClick={() => setModalContent(null)}
                            className="absolute inset-0 bg-slate-900/60 backdrop-blur-sm"
                        />
                        <motion.div 
                            initial={{ opacity: 0, scale: 0.95, y: 20 }}
                            animate={{ opacity: 1, scale: 1, y: 0 }}
                            exit={{ opacity: 0, scale: 0.95, y: 20 }}
                            className="relative bg-white w-full max-w-3xl rounded-[2.5rem] shadow-2xl overflow-hidden flex flex-col max-h-[90vh]"
                        >
                            <div className="p-8 border-b border-slate-100 flex items-center justify-between bg-slate-50/50">
                                <div className="flex items-center gap-3">
                                    <div className={`p-2 rounded-xl bg-${modalContent.color}-100`}>
                                        <modalContent.icon className={`w-5 h-5 text-${modalContent.color}-600`} />
                                    </div>
                                    <h3 className="text-xl font-black text-slate-900 tracking-tight">{modalContent.title}</h3>
                                </div>
                                <button 
                                    onClick={() => setModalContent(null)}
                                    className="p-2 hover:bg-slate-200 rounded-full transition-colors"
                                >
                                    <X className="w-5 h-5 text-slate-500" />
                                </button>
                            </div>
                            <div className="p-8 overflow-y-auto custom-scrollbar">
                                {modalContent.type === 'email' ? (
                                    <div className="space-y-6">
                                        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                            <div className="bg-slate-50 p-6 rounded-2xl border border-slate-100">
                                                <p className="text-xs font-black text-slate-400 uppercase tracking-widest mb-3 flex items-center gap-2">
                                                    <UserCircle2 className="w-3 h-3" />
                                                    Recipient Email
                                                </p>
                                                <input 
                                                    type="email"
                                                    value={modalContent.recipient_email}
                                                    onChange={(e) => setModalContent({...modalContent, recipient_email: e.target.value})}
                                                    className="w-full bg-white border border-slate-200 rounded-xl px-4 py-3 text-sm font-bold text-slate-900 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition-all font-mono"
                                                />
                                            </div>
                                            <div className="bg-slate-50 p-6 rounded-2xl border border-slate-100">
                                                <p className="text-xs font-black text-slate-400 uppercase tracking-widest mb-3 flex items-center gap-2">
                                                    <Edit3 className="w-3 h-3" />
                                                    Subject Line
                                                </p>
                                                <input 
                                                    type="text"
                                                    value={modalContent.subtitle}
                                                    onChange={(e) => setModalContent({...modalContent, subtitle: e.target.value})}
                                                    className="w-full bg-white border border-slate-200 rounded-xl px-4 py-3 text-sm font-bold text-slate-900 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition-all"
                                                />
                                            </div>
                                        </div>
                                        <div>
                                            <p className="text-xs font-black text-slate-400 uppercase tracking-widest mb-3 flex items-center gap-2">
                                                <Mail className="w-3 h-3" />
                                                Email Body
                                            </p>
                                            <textarea 
                                                value={modalContent.body}
                                                onChange={(e) => setModalContent({...modalContent, body: e.target.value})}
                                                rows={10}
                                                className="w-full bg-white border border-slate-200 rounded-2xl p-6 text-slate-600 leading-relaxed text-base focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition-all resize-none font-medium"
                                            />
                                        </div>
                                    </div>
                                ) : modalContent.type === 'person' ? (
                                    <div className="space-y-8">
                                        <div className="flex items-center gap-6">
                                            <div className="w-20 h-20 rounded-3xl bg-indigo-50 border border-indigo-100 flex items-center justify-center text-indigo-600 font-bold text-4xl shadow-lg shadow-indigo-100">
                                                {modalContent.title.charAt(0)}
                                            </div>
                                            <div>
                                                <h4 className="text-3xl font-black text-slate-900 tracking-tight mb-2">{modalContent.title}</h4>
                                                <p className="text-sm font-black text-indigo-600 uppercase tracking-[0.2em]">{modalContent.subtitle}</p>
                                            </div>
                                        </div>
                                        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                            <div className="bg-slate-50 p-6 rounded-2xl border border-slate-100">
                                                <p className="text-xs font-black text-slate-400 uppercase tracking-widest mb-3">Direct Email</p>
                                                <input 
                                                    type="email"
                                                    value={modalContent.email}
                                                    onChange={(e) => setModalContent({...modalContent, email: e.target.value})}
                                                    className="w-full bg-white border border-slate-200 rounded-xl px-4 py-3 text-base font-bold text-slate-700 focus:outline-none focus:ring-2 focus:ring-cyan-500/20 focus:border-cyan-500 transition-all font-mono"
                                                />
                                            </div>
                                            <div className="bg-slate-50 p-6 rounded-2xl border border-slate-100">
                                                <p className="text-xs font-black text-slate-400 uppercase tracking-widest mb-2">Professional Profile</p>
                                                {modalContent.linkedin ? (
                                                    <a 
                                                        href={modalContent.linkedin} 
                                                        target="_blank" 
                                                        rel="noreferrer"
                                                        className="flex items-center gap-2 text-blue-600 hover:text-blue-700 font-bold group h-full pt-1"
                                                    >
                                                        <Linkedin className="w-4 h-4" />
                                                        View on LinkedIn
                                                    </a>
                                                ) : (
                                                    <p className="text-sm font-bold text-slate-400 italic pt-1">No Profile Linked</p>
                                                )}
                                            </div>
                                        </div>
                                        <div className="pt-8 border-t border-slate-100">
                                            <div className="flex items-center gap-3 mb-4">
                                                <ShieldCheck className="w-5 h-5 text-green-500" />
                                                <h5 className="font-black text-slate-900 uppercase tracking-widest text-xs">Verification Details</h5>
                                            </div>
                                            <p className="text-slate-600 leading-relaxed text-base italic">
                                                This lead has been cross-referenced through autonomous market scouting. Their contact vector is verified for campaign-ready outreach.
                                            </p>
                                        </div>
                                    </div>
                                ) : modalContent.type === 'company' ? (
                                    <div className="space-y-8">
                                        <div className="bg-slate-50 border border-slate-100 rounded-[2rem] p-8">
                                            <h5 className="text-[10px] font-black text-indigo-500 uppercase tracking-widest mb-4 flex items-center gap-2">
                                                <Globe className="w-3.5 h-3.5" /> Intelligence Snapshot
                                            </h5>
                                            <p className="text-slate-600 font-medium leading-relaxed text-lg">
                                                {modalContent.body}
                                            </p>
                                            <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mt-8">
                                                {modalContent.recent_news?.length > 0 && (
                                                    <div className="space-y-3">
                                                        <h5 className="text-[10px] font-black text-blue-500 uppercase tracking-widest flex items-center gap-2">
                                                            <Activity className="w-3 h-3" /> Recent Signals
                                                        </h5>
                                                        <ul className="space-y-2">
                                                            {modalContent.recent_news.map((news, idx) => (
                                                                <li key={idx} className="text-sm text-slate-600 font-medium leading-relaxed pl-4 border-l-2 border-blue-100 italic">
                                                                    "{news}"
                                                                </li>
                                                            ))}
                                                        </ul>
                                                    </div>
                                                )}
                                                {modalContent.key_challenges?.length > 0 && (
                                                    <div className="space-y-3">
                                                        <h5 className="text-[10px] font-black text-rose-500 uppercase tracking-widest flex items-center gap-2">
                                                            <Activity className="w-3 h-3" /> Pain Points
                                                        </h5>
                                                        <div className="flex flex-wrap gap-2">
                                                            {modalContent.key_challenges.map((challenge, idx) => (
                                                                <span key={idx} className="px-3 py-1 bg-rose-50 text-rose-600 border border-rose-100 rounded-lg text-[10px] font-bold">
                                                                    {challenge}
                                                                </span>
                                                            ))}
                                                        </div>
                                                    </div>
                                                )}
                                                {modalContent.strategic_priorities?.length > 0 && (
                                                    <div className="md:col-span-2 space-y-3">
                                                        <h5 className="text-[10px] font-black text-emerald-500 uppercase tracking-widest flex items-center gap-2">
                                                            <Target className="w-3 h-3" /> Strategic Objectives
                                                        </h5>
                                                        <div className="flex flex-wrap gap-2">
                                                            {modalContent.strategic_priorities.map((item, idx) => (
                                                                <span key={idx} className="px-3 py-1 bg-emerald-50 text-emerald-600 border border-emerald-100 rounded-lg text-[10px] font-bold">
                                                                    {item}
                                                                </span>
                                                            ))}
                                                        </div>
                                                    </div>
                                                )}
                                            </div>
                                        </div>
                                    </div>
                                ) : modalContent.type === 'reply' ? (
                                    <div className="space-y-6 bg-white">
                                        <div 
                                            className="text-slate-700 leading-relaxed font-medium whitespace-pre-wrap text-lg"
                                            dangerouslySetInnerHTML={{ __html: modalContent.body }}
                                        />
                                        <div className="flex justify-end pt-4 border-t border-slate-50">
                                            <span className="text-[9px] font-bold text-slate-400 uppercase tracking-widest italic">Conversion context signal generated by AI Intent Analysis</span>
                                        </div>
                                    </div>
                                ) : modalContent.type === 'timeline' ? (
                                    <div className="min-h-[200px] w-full bg-white rounded-3xl" />
                                ) : modalContent.type === 'discovery' ? (
                                    <div className="space-y-6">
                                        <div>
                                            <label className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-2 block">Subject Line</label>
                                            <input 
                                                value={modalContent.subject}
                                                onChange={(e) => setModalContent({...modalContent, subject: e.target.value})}
                                                className="w-full bg-slate-50 border border-slate-200 rounded-xl px-4 py-3 font-bold text-slate-900 focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 outline-none transition-all"
                                            />
                                        </div>
                                        <div>
                                            <label className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-2 block">Personalized Invitation Body</label>
                                            <textarea 
                                                value={modalContent.body}
                                                onChange={(e) => setModalContent({...modalContent, body: e.target.value})}
                                                rows={12}
                                                className="w-full bg-slate-50 border border-slate-200 rounded-xl px-4 py-3 font-medium text-slate-600 focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 outline-none transition-all resize-none leading-relaxed"
                                            />
                                        </div>
                                    </div>
                                ) : (
                                    <div className="space-y-6">
                                        <div>
                                            <label className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-2 block">Direct Email Vector</label>
                                            <input 
                                                value={modalContent.email || ''}
                                                onChange={(e) => setModalContent({...modalContent, email: e.target.value})}
                                                className="w-full bg-slate-50 border border-slate-200 rounded-xl px-4 py-3 font-bold text-slate-900 focus:ring-2 focus:ring-cyan-500/20 focus:border-cyan-500 outline-none transition-all"
                                                placeholder="stakeholder@company.com"
                                            />
                                        </div>
                                        <div>
                                            <label className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-2 block">Professional Identity (LinkedIn)</label>
                                            <input 
                                                value={modalContent.linkedin || ''}
                                                onChange={(e) => setModalContent({...modalContent, linkedin: e.target.value})}
                                                className="w-full bg-slate-50 border border-slate-200 rounded-xl px-4 py-3 font-bold text-slate-900 focus:ring-2 focus:ring-cyan-500/20 focus:border-cyan-500 outline-none transition-all"
                                                placeholder="linkedin.com/in/username"
                                            />
                                        </div>
                                    </div>
                                )}
                            </div>
                            <div className="p-6 bg-slate-50 border-t border-slate-100 flex justify-end gap-4">
                                <Button 
                                    onClick={() => setModalContent(null)} 
                                    className="rounded-xl px-8 font-bold bg-white text-slate-600 border border-slate-200 hover:bg-slate-100"
                                >
                                    {modalContent.type === 'discovery' ? 'Back' : 'Dismiss'}
                                </Button>
                                {modalContent.type === 'email' && (
                                    <Button 
                                        onClick={handleSaveEmail} 
                                        isLoading={isSaving}
                                        className="bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl px-8 font-black flex items-center gap-2 shadow-lg shadow-emerald-100"
                                    >
                                        <Save className="w-4 h-4" />
                                        Save Narrative
                                    </Button>
                                )}
                                {modalContent.type === 'person' && (
                                    <Button 
                                        onClick={handleSaveDM} 
                                        isLoading={isSaving}
                                        className="bg-cyan-600 hover:bg-cyan-700 text-white rounded-xl px-8 font-black flex items-center gap-2 shadow-lg shadow-cyan-100"
                                    >
                                        <Save className="w-4 h-4" />
                                        Save Changes
                                    </Button>
                                )}
                                {modalContent.type === 'discovery' && (
                                    <Button 
                                        onClick={handleSendDiscovery} 
                                        isLoading={isSaving}
                                        className="bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl px-8 font-black flex items-center gap-2 shadow-lg shadow-indigo-100"
                                    >
                                        <Mail className="w-4 h-4" />
                                        Send Discovery
                                    </Button>
                                )}
                            </div>
                        </motion.div>
                    </div>
                )}
            </AnimatePresence>

            {/* Header */}
            <header className="bg-white/80 backdrop-blur-md border-b border-slate-200 h-20 sticky top-0 z-50 flex items-center px-8">
                <div className="max-w-[1400px] mx-auto w-full flex items-center justify-between">
                    <div className="flex items-center gap-6">
                        <button 
                            onClick={() => navigate('/active-campaigns')} 
                            className="w-10 h-10 flex items-center justify-center bg-white border border-slate-200 hover:bg-slate-50 hover:border-slate-300 rounded-xl transition-all shadow-sm group"
                        >
                            <ChevronLeft className="w-5 h-5 text-slate-500 group-hover:-translate-x-0.5 transition-transform" />
                        </button>
                        <div className="flex flex-col">
                            <h1 className="text-xl font-black text-slate-900 leading-none mb-2 tracking-tight">
                                {data.campaign?.name || 'Campaign Workspace'}
                            </h1>
                            <div className="flex items-center gap-3">
                                <span className="text-[10px] font-black text-slate-400 uppercase tracking-widest flex items-center gap-1.5">
                                    <div className="w-1.5 h-1.5 rounded-full bg-blue-500" />
                                    Orchestration Phase 0{isMonitoring ? '2' : '1'}
                                </span>
                                {hasMission && (
                                    <div className="flex gap-1.5">
                                        <span className="px-1.5 py-0.5 bg-emerald-50 text-emerald-600 text-[9px] font-black rounded border border-emerald-100 uppercase tracking-tighter shadow-sm shadow-emerald-50">
                                            Dataset Live
                                        </span>
                                    </div>
                                )}
                            </div>
                        </div>
                    </div>

                    {/* CENTERED VIEW TOGGLE */}
                    {isMonitoring && (
                        <nav className="absolute left-1/2 -translate-x-1/2 flex items-center gap-4">
                            <ViewTab 
                                active={activeView === 'research'} 
                                onClick={() => { setHasUserNavigated(true); setActiveView('research'); }} 
                                label="Research" 
                                icon={Globe} 
                            />
                            <ViewTab 
                                active={activeView === 'monitor'} 
                                onClick={() => { setHasUserNavigated(true); setActiveView('monitor'); }} 
                                label="Monitor" 
                                icon={Activity} 
                            />
                            <ViewTab 
                                active={activeView === 'discovery'} 
                                onClick={() => { setHasUserNavigated(true); setActiveView('discovery'); }} 
                                label="Discovery Call" 
                                icon={PhoneCall} 
                            />
                        </nav>
                    )}

                    <div className="flex items-center gap-4">
                        {hasMission && data.emails.length > 0 && !isMonitoring && (
                            <motion.div 
                                initial={{ opacity: 0, x: 20 }}
                                animate={{ opacity: 1, x: 0 }}
                                className="flex items-center gap-4"
                            >
                                <div className="hidden lg:flex flex-col items-end mr-4">
                                     <span className="text-[9px] font-black text-slate-400 uppercase tracking-widest">Intelligence Pulse</span>
                                     <span className="text-[11px] font-bold text-slate-600 flex items-center gap-1.5">
                                        <div className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
                                        Monitoring Active
                                     </span>
                                </div>
                            </motion.div>
                        )}
                        {isMonitoring && (
                            <div className="hidden lg:flex flex-col items-end mr-2">
                                <span className="text-[9px] font-black text-slate-200 px-2 py-0.5 bg-slate-900 rounded-full uppercase tracking-widest">Command Center</span>
                            </div>
                        )}
                    </div>
                </div>
            </header>

            <main className="flex-1 overflow-y-auto">
                <div className="max-w-[1400px] mx-auto p-6 md:p-8 space-y-12">
                    {!hasMission && !isLaunching ? (
                        /* Launch State */
                        <div className="max-w-2xl mx-auto py-16 text-center">
                            <motion.div 
                                initial={{ scale: 0.9, opacity: 0 }}
                                animate={{ scale: 1, opacity: 1 }}
                                className="w-20 h-20 bg-blue-600 rounded-3xl flex items-center justify-center mx-auto mb-10 shadow-2xl shadow-blue-200"
                            >
                                <Zap className="w-10 h-10 text-white fill-current" />
                            </motion.div>
                            <h1 className="text-4xl font-black text-slate-900 mb-6 tracking-tight font-sans">Initiate Outreach</h1>
                            <p className="text-slate-500 mb-12 text-lg leading-relaxed">
                                Deploy your autonomous multi-agent pipeline to research markets, verify stakeholders, and architect personalized narratives.
                            </p>
                            <div className="bg-white p-2 rounded-[2rem] border border-slate-200 shadow-2xl shadow-slate-200/40 flex flex-col gap-2">
                                <textarea
                                    value={query}
                                    onChange={(e) => setQuery(e.target.value)}
                                    placeholder="e.g. Find UK-based manufacturing plants needing AI downtime reduction..."
                                    className="w-full bg-transparent p-8 text-slate-900 placeholder:text-slate-300 focus:outline-none min-h-[180px] resize-none text-xl leading-relaxed"
                                />
                                <div className="flex justify-end p-4 border-t border-slate-50">
                                    <Button 
                                        onClick={handleLaunch} 
                                        disabled={!query.trim() || isLaunching}
                                        isLoading={isLaunching}
                                        className="bg-blue-600 hover:bg-blue-700 text-white font-black py-4 px-10 rounded-2xl gap-3 shadow-xl shadow-blue-200 transition-all active:scale-95 text-lg"
                                    >
                                        Begin Orchestration
                                        <ArrowRight className="w-6 h-6" />
                                    </Button>
                                </div>
                            </div>
                        </div>
                    ) : activeView === 'research' ? (
                        /* Balanced Vertical Content Feed */
                        <div className="space-y-12 pb-32 animate-in fade-in slide-in-from-bottom-8 duration-1000">
                             {/* Content same as before... */}
                            
                            {/* 1. MISSION STRATEGY */}
                            <section className="space-y-6">
                                <SectionHeader icon={Target} color="blue" label="Strategic Objectives" count="01" />
                                <div className="bg-white rounded-2xl border border-slate-200 p-8 shadow-sm relative overflow-hidden group">
                                    <div className="absolute top-0 right-0 p-8 opacity-[0.02] group-hover:scale-110 transition-transform duration-1000">
                                        <Target className="w-24 h-24" />
                                    </div>
                                    <div className="relative z-10 space-y-8">
                                        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 items-start">
                                            <div className="md:col-span-2">
                                                <h3 className="text-[10px] font-black text-blue-600 uppercase tracking-widest mb-3 flex items-center gap-2">
                                                    <Zap className="w-3 h-3" /> Autonomous Value Proposition
                                                </h3>
                                                <p className="text-2xl font-black text-slate-900 leading-tight tracking-tight italic">
                                                    "{data.campaign?.value_proposition || "Generating strategic summary..."}"
                                                </p>
                                                {data.campaign?.strategic_positioning && (
                                                    <p className="mt-4 text-sm font-bold text-slate-400 uppercase tracking-widest flex items-center gap-2">
                                                        <ShieldCheck className="w-4 h-4 text-blue-400" />
                                                        {data.campaign.strategic_positioning}
                                                    </p>
                                                )}
                                            </div>
                                            <div className="md:border-l md:border-slate-100 md:pl-8">
                                                <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-2 flex items-center gap-2">
                                                    <Users className="w-3 h-3" /> Target Demographic
                                                </p>
                                                <p className="text-sm font-bold text-slate-700 leading-relaxed italic">
                                                    {data.campaign?.target_audience || "Analyzing market segments..."}
                                                </p>
                                            </div>
                                        </div>
                                        
                                        {data.campaign?.key_offerings?.length > 0 && (
                                            <div className="pt-8 border-t border-slate-50">
                                                <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-4">Core Solution Vectors</p>
                                                <div className="flex flex-wrap gap-3">
                                                    {data.campaign.key_offerings.map((offering, idx) => (
                                                        <span key={idx} className="px-4 py-1.5 bg-blue-50 text-blue-700 border border-blue-100 rounded-xl text-[11px] font-black uppercase tracking-wider">
                                                            {offering}
                                                        </span>
                                                    ))}
                                                </div>
                                            </div>
                                        )}
                                    </div>
                                </div>
                            </section>

                            {/* 2. DISCOVERY STREAM */}
                            <section className="space-y-6">
                                <SectionHeader icon={Telescope} color="indigo" label="Market Discovery" count="02" badge={`${data.companies.length} TARGETS FOUND`} />
                                
                                {data.companies.length === 0 ? (
                                    <LoadingState label="Agent is scanning global markets for matches..." />
                                ) : (
                                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                                        {data.companies.map((company, i) => (
                                            <div key={i} className="bg-white border border-slate-200 rounded-2xl p-6 hover:border-blue-300 transition-all shadow-sm hover:shadow-xl hover:shadow-slate-200/30 flex flex-col">
                                                <div className="flex justify-between items-start mb-3">
                                                    <h4 className="font-bold text-slate-900 text-lg leading-none">{company.name}</h4>
                                                    <div className="flex items-center gap-2 px-2 py-0.5 bg-slate-50 rounded text-slate-400 font-bold text-[10px]">
                                                        {company.relevance_score}/10
                                                    </div>
                                                </div>
                                                <p className="text-sm text-slate-500 mb-4 line-clamp-2 leading-relaxed font-medium flex-1">{company.description}</p>
                                                <div className="flex items-center justify-between pt-4 border-t border-slate-50">
                                                    <div className="flex items-center gap-2">
                                                        <Globe className="w-3.5 h-3.5 text-slate-300" />
                                                        <span className="text-[11px] text-slate-400 font-semibold truncate max-w-[100px]">{company.website}</span>
                                                    </div>
                                                    <button 
                                                        onClick={() => setModalContent({
                                                            type: 'company',
                                                            title: company.name,
                                                            body: company.description,
                                                            score: company.relevance_score,
                                                            website: company.website,
                                                            recent_news: company.recent_news,
                                                            key_challenges: company.key_challenges,
                                                            strategic_priorities: company.strategic_priorities,
                                                            icon: Telescope,
                                                            color: 'indigo'
                                                        })}
                                                        className="p-1.5 text-indigo-600 hover:bg-indigo-50 rounded-lg transition-colors group/btn flex items-center gap-1.5"
                                                    >
                                                        <Maximize2 className="w-4 h-4" />
                                                    </button>
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                )}
                            </section>

                            {/* 3. LEAD PIPELINE */}
                            <section className="space-y-6">
                                <SectionHeader icon={Users} color="cyan" label="Validated Decision Makers" count="03" badge={`${data.decision_makers.length} LEADS VERIFIED`} />
                                
                                {data.decision_makers.length === 0 ? (
                                    <div className="bg-white rounded-[2rem] border border-slate-200 shadow-sm overflow-hidden">
                                        <LoadingState label="Verifying key stakeholders and contact vectors..." className="border-none py-20" />
                                    </div>
                                ) : (
                                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                        {data.decision_makers.map((dm, i) => {
                                            const company = data.companies.find(c => c.id === dm.company_id);
                                            return (
                                                <div key={i} className="bg-white border border-slate-200 rounded-2xl p-5 flex flex-col justify-between hover:bg-slate-50/50 transition-all shadow-sm group relative overflow-hidden">
                                                    <div className="flex items-start justify-between mb-4">
                                                        <div className="flex items-center gap-4">
                                                            <div className="w-10 h-10 rounded-xl bg-indigo-50 border border-indigo-100 flex items-center justify-center text-indigo-600 font-bold text-lg">
                                                                {dm.name.charAt(0)}
                                                            </div>
                                                            <div>
                                                                {company && (
                                                                    <p className="text-[9px] font-black text-blue-400 uppercase tracking-[0.15em] leading-none mb-1.5 flex items-center gap-1">
                                                                        <Globe className="w-2.5 h-2.5" />
                                                                        {company.name}
                                                                    </p>
                                                                )}
                                                                <h4 className="font-bold text-slate-900 text-sm leading-none mb-1">{dm.name}</h4>
                                                                <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest leading-none">
                                                                    {dm.role?.split(' at ')[0] || dm.role}
                                                                </p>
                                                            </div>
                                                        </div>
                                                        <div className="flex items-center gap-2">
                                                            <div className={cn(
                                                                "px-2 py-0.5 rounded-[4px] text-[9px] font-black uppercase tracking-widest border",
                                                                (dm.status === 'DISCOVERY' || dm.status === 'discovery') ? "bg-emerald-50 text-emerald-600 border-emerald-100" :
                                                                dm.status === 'TERMINATED' ? "bg-rose-50 text-rose-600 border-rose-100" :
                                                                dm.status === 'ACTIVE' ? "bg-blue-50 text-blue-600 border-blue-100" :
                                                                "bg-slate-50 text-slate-400 border-slate-100"
                                                            )}>
                                                                {dm.status}
                                                            </div>
                                                            <button 
                                                                onClick={() => setModalContent({
                                                                    type: 'person',
                                                                    id: dm.id,
                                                                    title: dm.name,
                                                                    subtitle: dm.role,
                                                                    email: dm.email,
                                                                    linkedin: dm.linkedin,
                                                                    icon: Users,
                                                                    color: 'cyan'
                                                                })}
                                                                className="p-1.5 text-slate-300 hover:text-blue-600 hover:gap-1 transition-all flex items-center"
                                                            >
                                                                <Maximize2 className="w-3.5 h-3.5" />
                                                            </button>
                                                        </div>
                                                    </div>
                                                    <div className="pt-3 border-t border-slate-50 flex items-center justify-between gap-4">
                                                        <div className="flex flex-col min-w-0 flex-1">
                                                            <p className="text-[9px] font-black text-slate-300 uppercase tracking-widest mb-0.5">Email Vector</p>
                                                            <p className="text-xs font-bold text-slate-600 break-all">{dm.email}</p>
                                                        </div>
                                                        {dm.linkedin && (
                                                            <a 
                                                                href={dm.linkedin} 
                                                                target="_blank" 
                                                                rel="noreferrer" 
                                                                className="flex-shrink-0 flex items-center gap-1 text-blue-600 hover:text-blue-700 font-black text-[9px] bg-blue-50 px-2 py-1 rounded-md transition-all uppercase tracking-tighter"
                                                            >
                                                                <Linkedin className="w-3 h-3" />
                                                                LinkedIn
                                                            </a>
                                                        )}
                                                    </div>
                                                </div>
                                            );
                                        })}
                                    </div>
                                )}
                            </section>

                            {/* 4. OUTREACH ARCHITECT */}
                            <section className="space-y-6">
                                <SectionHeader icon={Sparkles} color="emerald" label="Personalized Narratives" count="04" badge={`${data.emails.length} SEQUENCES BUILT`} />
                                
                                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                                    {data.emails.length === 0 ? (
                                        <LoadingState label="Synthesizing personalized outreach sequences..." className="md:col-span-2 lg:col-span-3 py-24" />
                                    ) : (
                                        data.emails.map((email, i) => {
                                            const dm = data.decision_makers.find(d => d.id === email.decision_maker_id);
                                            const company = dm ? data.companies.find(c => c.id === dm.company_id) : null;
                                            
                                            return (
                                                <div key={i} className="bg-white border border-slate-200 rounded-2xl p-6 shadow-sm flex flex-col hover:border-emerald-400 transition-all group relative overflow-hidden">
                                                    <div className="flex items-center justify-between mb-4">
                                                        <div className="flex items-center gap-3">
                                                            <div className="w-10 h-10 rounded-xl bg-emerald-50 flex items-center justify-center">
                                                                <Mail className="w-5 h-5 text-emerald-600" />
                                                            </div>
                                                            <div className="flex flex-col">
                                                                <span className="text-[10px] font-black text-slate-400 uppercase tracking-widest leading-none mb-1">Targeting</span>
                                                                <span className="text-xs font-bold text-slate-900 leading-none">{dm?.name || 'Lead'}</span>
                                                            </div>
                                                        </div>
                                                        <button 
                                                            onClick={() => setModalContent({
                                                                type: 'email',
                                                                id: email.id,
                                                                dm_id: dm?.id,
                                                                title: 'Edit Personalized Draft',
                                                                subtitle: email.subject,
                                                                body: email.body,
                                                                recipient: dm?.name,
                                                                recipient_email: dm?.email,
                                                                icon: Sparkles,
                                                                color: 'emerald'
                                                            })}
                                                            className="p-1.5 text-slate-300 hover:text-emerald-600 hover:bg-emerald-50 rounded-lg transition-all"
                                                        >
                                                            <Maximize2 className="w-4 h-4" />
                                                        </button>
                                                    </div>

                                                    <div className="bg-slate-50/50 p-4 rounded-xl border border-slate-100 mb-4 group-hover:bg-white transition-colors">
                                                        <h4 className="font-bold text-slate-900 mb-2 text-sm leading-tight line-clamp-1">{email.subject}</h4>
                                                        <p className="text-xs text-slate-500 line-clamp-3 leading-relaxed font-medium italic">
                                                            "{email.body.replace(/<[^>]*>?/gm, '')}"
                                                        </p>
                                                    </div>

                                                    <div className="mt-auto flex justify-between items-center pt-4 border-t border-slate-50">
                                                        <div className="flex flex-col gap-1">
                                                            <div className="flex items-center gap-1.5">
                                                                <CheckCircle className="w-3.5 h-3.5 text-emerald-500" />
                                                                <span className="text-[10px] font-black text-emerald-600 uppercase tracking-widest">{email.status === 'draft' ? 'Architected' : email.status}</span>
                                                            </div>
                                                            <div className="flex items-center gap-2">
                                                                <span className="text-[9px] font-bold text-slate-300 uppercase">{email.type || 'initial'}</span>
                                                                {email.sent_at && (
                                                                    <span className="text-[9px] text-slate-300 flex items-center gap-1">
                                                                        • {new Date(email.sent_at).toLocaleDateString()}
                                                                    </span>
                                                                )}
                                                            </div>
                                                        </div>
                                                        <div className="text-[10px] font-bold text-slate-400 uppercase tracking-tight text-right">
                                                            {company?.name || 'Private Sector'}
                                                        </div>
                                                    </div>
                                                </div>
                                            );
                                        })
                                    )}
                                </div>
                            </section>
                        </div>
                    ) : activeView === 'monitor' ? (
                        /* OUTREACH MONITORING & DISPATCH QUEUE */
                        <div className="space-y-12 pb-32">
                            {/* 1. DISPATCH QUEUE (DRAFTS) */}
                            <section className="space-y-6">
                                <div className="flex items-center justify-between">
                                    <SectionHeader icon={Mail} color="blue" label="Pending Dispatch" count={data.emails.filter(e => e.status === 'PENDING_APPROVAL').length.toString().padStart(2, '0')} badge="REQUIRES APPROVAL" />
                                    {data.emails.filter(e => e.status === 'PENDING_APPROVAL').length > 0 && (
                                        <Button 
                                            onClick={handleBatchDispatch}
                                            isLoading={isDispatching}
                                            className="bg-slate-900 hover:bg-black text-white px-6 py-2.5 rounded-xl font-black text-[10px] uppercase tracking-widest flex items-center gap-2 shadow-xl shadow-slate-200"
                                        >
                                            <Zap className="w-3.5 h-3.5 fill-current text-yellow-400" />
                                            Batch Dispatch All
                                        </Button>
                                    )}
                                </div>
                                
                                    {data.emails.filter(e => e.status === 'PENDING_APPROVAL').length === 0 ? (
                                        <div className="bg-slate-50 border-2 border-dashed border-slate-200 rounded-[2rem] py-16 text-center">
                                            <p className="text-slate-400 font-bold text-sm tracking-tight uppercase">Approval queue clear. All generated narratives are dispatched or declined.</p>
                                        </div>
                                    ) : (
                                        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                                            {data.emails.filter(e => e.status === 'PENDING_APPROVAL').map((email, i) => {
                                                const dm = data.decision_makers.find(d => d.id === email.decision_maker_id);
                                                const company = dm ? data.companies.find(c => c.id === dm.company_id) : null;
                                                return (
                                                    <motion.div 
                                                        layout
                                                        initial={{ opacity: 0, y: 20 }}
                                                        animate={{ opacity: 1, y: 0 }}
                                                        exit={{ opacity: 0, scale: 0.95 }}
                                                        transition={{ duration: 0.5, delay: i * 0.1 }}
                                                        key={email.id}
                                                        onClick={() => setModalContent({
                                                            type: 'email',
                                                            id: email.id,
                                                            dm_id: dm?.id,
                                                            title: 'Edit Full Sequence',
                                                            subtitle: email.subject,
                                                            body: email.body,
                                                            recipient: dm?.name,
                                                            recipient_email: dm?.email,
                                                            icon: Sparkles,
                                                            color: 'emerald'
                                                        })}
                                                        className="bg-white border border-slate-200/60 rounded-[2.5rem] p-8 flex flex-col shadow-sm hover:shadow-2xl hover:shadow-blue-500/10 transition-all group border-b-4 border-b-slate-100 hover:border-b-blue-500 cursor-pointer relative"
                                                    >
                                                        <div className="flex items-start justify-between mb-8">
                                                            <div className="flex items-center gap-4">
                                                                <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center text-white shadow-lg shadow-blue-100 flex-shrink-0">
                                                                    <Mail className="w-7 h-7" />
                                                                </div>
                                                                <div className="min-w-0">
                                                                    <div className="flex items-center gap-2 mb-1">
                                                                        <span className="text-[10px] font-black text-blue-600 uppercase tracking-widest bg-blue-50 px-2 py-0.5 rounded-md">{company?.name || 'Prospect'}</span>
                                                                        <div className="flex items-center gap-0.5 ml-2">
                                                                            {[1, 2, 3, 4, 5].map((v) => (
                                                                                <div key={v} className={`h-1 w-2 rounded-full ${v <= 4 ? 'bg-emerald-400' : 'bg-slate-100'}`} />
                                                                            ))}
                                                                        </div>
                                                                    </div>
                                                                    <div className="flex items-baseline gap-2 truncate">
                                                                        <h4 className="text-lg font-black text-slate-900 truncate leading-none">{dm?.name}</h4>
                                                                        <span className="text-[11px] font-bold text-slate-400 truncate font-mono">({dm?.email})</span>
                                                                    </div>
                                                                    <p className="text-[11px] font-bold text-slate-400 uppercase tracking-tight mt-1">{dm?.role?.split(' at ')[0] || dm?.role}</p>
                                                                </div>
                                                            </div>
                                                            <div className="px-3 py-1 bg-slate-100 rounded-full text-[9px] font-black text-slate-400 uppercase tracking-widest flex items-center gap-1.5 opacity-0 group-hover:opacity-100 transition-opacity">
                                                                <FileEdit className="w-3 h-3" />
                                                                Click to Edit
                                                            </div>
                                                        </div>

                                                        <div className="bg-slate-50/50 rounded-3xl p-6 mb-8 border border-slate-100 group-hover:bg-slate-50 transition-colors flex-1">
                                                            <div className="flex items-center gap-2 mb-3">
                                                                <div className="w-2 h-2 rounded-full bg-blue-500 animate-pulse" />
                                                                <span className="text-[10px] font-black text-slate-400 uppercase tracking-[0.2em]">Subject Line</span>
                                                            </div>
                                                            <h4 className="text-sm font-bold text-slate-900 mb-4 leading-tight">{email.subject}</h4>
                                                            <p className="text-xs text-slate-500 leading-relaxed font-medium italic border-l-2 border-slate-200 pl-4 py-1">
                                                                "{email.body.replace(/<[^>]*>?/gm, '').substring(0, 160)}..."
                                                            </p>
                                                        </div>

                                                        <div className="flex items-center gap-3 mt-auto">
                                                            <button 
                                                                onClick={(e) => {
                                                                    e.stopPropagation();
                                                                    handleDeclineEmail(email.id);
                                                                }}
                                                                className="flex-1 h-14 bg-white border-2 border-slate-100 text-slate-400 hover:border-rose-100 hover:bg-rose-50 hover:text-rose-600 rounded-2xl font-black text-[11px] uppercase tracking-[0.2em] transition-all flex items-center justify-center gap-3 active:scale-95"
                                                            >
                                                                <Trash2 className="w-5 h-5" />
                                                                Reject
                                                            </button>
                                                            <button 
                                                                onClick={(e) => {
                                                                    e.stopPropagation();
                                                                    handleApproveEmail(email.id);
                                                                }}
                                                                className="flex-[1.5] h-14 bg-slate-900 text-white hover:bg-emerald-600 rounded-2xl font-black text-[11px] uppercase tracking-[0.2em] transition-all flex items-center justify-center gap-3 shadow-xl shadow-slate-200 active:scale-95"
                                                            >
                                                                <ShieldCheck className="w-5 h-5 text-emerald-400" />
                                                                Approve & Send
                                                            </button>
                                                        </div>
                                                    </motion.div>
                                                );
                                            })}
                                        </div>
                                    )}
                            </section>

                            {/* 2. ACTIVE OUTREACH MONITORING (SENT) */}
                            <section className="space-y-6">
                                <SectionHeader icon={Activity} color="emerald" label="Active Outreach Monitoring" count={data.emails.filter(e => e.status === 'SENT').length.toString().padStart(2, '0')} badge="LIVE TRACKING" />
                                
                                <div className="bg-white border border-slate-200 rounded-[2.5rem] overflow-hidden shadow-sm">
                                    <div className="overflow-x-auto">
                                        <table className="w-full text-left border-collapse">
                                            <thead>
                                                <tr className="border-b border-slate-100">
                                                    <th className="px-8 py-5 text-[10px] font-black text-slate-400 uppercase tracking-[0.2em]">Prospect / Company</th>
                                                    <th className="px-8 py-5 text-[10px] font-black text-slate-400 uppercase tracking-[0.2em]">Outreach Stage</th>
                                                    <th className="px-8 py-5 text-[10px] font-black text-slate-400 uppercase tracking-[0.2em]">Sent At</th>
                                                    <th className="px-8 py-5 text-[10px] font-black text-slate-400 uppercase tracking-[0.2em]">Reply Status</th>
                                                </tr>
                                            </thead>
                                            <tbody className="divide-y divide-slate-50">
                                                {data.emails.filter(e => e.status === 'SENT').length === 0 ? (
                                                    <tr>
                                                        <td colSpan="4" className="px-8 py-12 text-center text-slate-400 font-bold text-xs uppercase tracking-tight italic">
                                                            No active outreach threads detected yet. Approve items in the queue to begin tracking.
                                                        </td>
                                                    </tr>
                                                ) : (
                                                    data.emails.filter(e => e.status === 'SENT').map((email, i) => {
                                                        const dm = data.decision_makers.find(d => d.id === email.decision_maker_id);
                                                        const company = dm ? data.companies.find(c => c.id === dm.company_id) : null;
                                                        return (
                                                            <tr key={email.id} className="group hover:bg-slate-50/50 transition-colors">
                                                                <td className="px-8 py-5">
                                                                    <div className="flex flex-col">
                                                                        <span className="text-sm font-bold text-slate-900 leading-tight">{dm?.name}</span>
                                                                        <span className="text-[10px] font-bold text-slate-400 uppercase tracking-tight">{company?.name}</span>
                                                                    </div>
                                                                </td>
                                                                <td className="px-8 py-5">
                                                                    <div className="flex items-center gap-2">
                                                                        <div className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
                                                                        <span className="text-[10px] font-black text-slate-600 uppercase tracking-widest">{email.type || 'INITIAL'}</span>
                                                                    </div>
                                                                </td>
                                                                <td className="px-8 py-5">
                                                                    <span className="text-[10px] font-bold text-slate-500 uppercase">{email.sent_at ? new Date(email.sent_at).toLocaleString() : 'Just now'}</span>
                                                                </td>
                                                                <td className="px-8 py-5">
                                                                    <div className="flex items-center justify-between gap-4">
                                                                        {data.emails.some(e => e.decision_maker_id === dm?.id && e.direction === 'inbound') ? (
                                                                            <div className="flex items-center gap-2">
                                                                                {(() => {
                                                                                    const reply = data.emails.find(e => e.decision_maker_id === dm?.id && e.direction === 'inbound');
                                                                                    const intent = reply?.intent || 'PENDING';
                                                                                    return (
                                                                                        <div className={`px-3 py-1 rounded-full text-[9px] font-black uppercase tracking-widest flex items-center gap-1.5 ${
                                                                                            intent === 'POSITIVE' ? 'bg-emerald-50 text-emerald-600' :
                                                                                            intent === 'NEGATIVE' ? 'bg-rose-50 text-rose-600' :
                                                                                            'bg-indigo-50 text-indigo-600'
                                                                                        }`}>
                                                                                            <MessageSquare className="w-3 h-3" />
                                                                                            {intent}
                                                                                        </div>
                                                                                    );
                                                                                })()}
                                                                            </div>
                                                                        ) : (
                                                                            <div className="px-3 py-1 bg-slate-100 text-slate-500 rounded-full text-[9px] font-black uppercase tracking-widest flex items-center gap-1.5 font-sans">
                                                                                <Loader2 className="w-3 h-3 animate-spin" />
                                                                                Awaiting Signal
                                                                            </div>
                                                                        )}
                                                                        
                                                                        <button 
                                                                            onClick={() => {
                                                                                setModalContent({
                                                                                    type: 'timeline',
                                                                                    title: `Audit: ${dm?.name}`,
                                                                                    icon: History,
                                                                                    color: 'blue'
                                                                                });
                                                                                
                                                                            }}
                                                                            className="p-2 text-slate-300 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-all"
                                                                            title="View History"
                                                                        >
                                                                            <History className="w-4 h-4" />
                                                                        </button>
                                                                    </div>
                                                                </td>
                                                            </tr>
                                                        );
                                                    })
                                                )}
                                            </tbody>
                                        </table>
                                    </div>
                                </div>
                            </section>
                        </div>
                    ) : (
                        /* DISCOVERY CALL VIEW */
                        <div className="space-y-12 pb-32">
                            <SectionHeader icon={PhoneCall} color="indigo" label="High-Intent Conversion Pipeline" count={data.decision_makers.filter(dm => dm.status === 'DISCOVERY' || dm.status === 'discovery').length.toString().padStart(2, '0')} badge="READY FOR ENGAGEMENT" />
                            
                            <div className="flex flex-col gap-4">
                                {data.decision_makers.filter(dm => dm.status === 'DISCOVERY' || dm.status === 'discovery').length === 0 ? (
                                    <div className="h-[50vh] flex flex-col items-center justify-center bg-white border border-dashed border-slate-200 rounded-[2.5rem] p-12 text-center">
                                        <div className="w-20 h-20 bg-indigo-50 rounded-3xl flex items-center justify-center mb-8 text-indigo-400">
                                            <PhoneCall className="w-8 h-8 opacity-20" />
                                        </div>
                                        <h3 className="text-xl font-black text-slate-900 mb-2">Bridge Awaiting Signals</h3>
                                        <p className="text-slate-500 max-w-sm font-medium">
                                            When a prospect exhibits a <span className="text-emerald-600 font-bold">POSITIVE</span> intent during monitoring, they will be automatically escalated here for final discovery coordination.
                                        </p>
                                    </div>
                                ) : (
                                    data.decision_makers.filter(dm => dm.status === 'DISCOVERY' || dm.status === 'discovery').map((dm, i) => {
                                        const company = data.companies.find(c => c.id === dm.company_id);
                                        // Get the absolute LATEST inbound reply
                                        const lastReply = [...data.emails]
                                            .filter(e => e.decision_maker_id === dm.id && e.direction === 'inbound')
                                            .sort((a, b) => new Date(b.created_at) - new Date(a.created_at))[0];

                                        const cleanReplyContent = (text) => {
                                            if (!text) return "No message content available.";
                                            // 1. Strip HTML tags
                                            let clean = text.replace(/<[^>]*>?/gm, '');
                                            
                                            // 2. Remove lines starting with '>' (standard email quoting)
                                            clean = clean.split('\n')
                                                .filter(line => !line.trim().startsWith('>'))
                                                .join('\n');

                                            // 3. Clear out common reply delimiters (quotes)
                                            const delimiters = [
                                                /On\s.*\n?.*wrote:/i,
                                                /-----Original Message-----/i,
                                                /From:\s/i,
                                                /Sent from my/i,
                                                /________________________________/
                                            ];
                                            for (let delim of delimiters) {
                                                const parts = clean.split(delim);
                                                if (parts.length > 1) {
                                                    clean = parts[0];
                                                }
                                            }

                                            // 4. SMART TEXT HEALING (Fix hard wrapping)
                                            // Split into paragraphs (delimited by double newlines)
                                            const paragraphs = clean.split(/\n\s*\n/);
                                            const healed = paragraphs.map(para => {
                                                // Within each paragraph, replace single newlines with spaces
                                                // but keep list items or short lines that look like sign-offs
                                                if (para.trim().startsWith('-') || para.trim().startsWith('*')) return para;
                                                return para.replace(/\n(?!\n)/g, ' ').replace(/\s\s+/g, ' ').trim();
                                            }).join('\n\n');

                                            return healed;
                                        };

                                        return (
                                            <motion.div 
                                                layout
                                                initial={{ opacity: 0, y: 10 }}
                                                animate={{ opacity: 1, y: 0 }}
                                                key={dm.id}
                                                onClick={() => setModalContent({
                                                    type: 'reply',
                                                    title: 'Conversion Intelligence',
                                                    subtitle: `From ${dm.name} (${dm.email})`,
                                                    body: cleanReplyContent(lastReply?.body),
                                                    icon: MessageSquare,
                                                    color: 'indigo'
                                                })}
                                                className="bg-white border border-slate-200 rounded-[2rem] p-6 hover:shadow-2xl hover:shadow-indigo-500/10 transition-all group flex items-center justify-between cursor-pointer border-b-4 border-b-slate-100 hover:border-b-indigo-500 relative overflow-hidden"
                                            >
                                                <div className="flex items-center gap-6 flex-1 min-w-0">
                                                    <div className="w-14 h-14 rounded-2xl bg-indigo-600 flex items-center justify-center text-white text-2xl font-black shrink-0 shadow-lg shadow-indigo-100 group-hover:scale-105 transition-transform">
                                                        {dm.name.charAt(0)}
                                                    </div>
                                                    <div className="grid grid-cols-1 md:grid-cols-3 xl:grid-cols-4 gap-8 flex-1 min-w-0 items-center">
                                                        <div className="min-w-0">
                                                            <p className="text-[10px] font-black text-indigo-500 uppercase tracking-[0.2em] mb-1 truncate">{company?.name || 'Venture'}</p>
                                                            <h4 className="text-lg font-black text-slate-900 truncate tracking-tight">{dm.name}</h4>
                                                        </div>
                                                        <div className="hidden md:block min-w-0">
                                                            <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-1.5 flex items-center gap-1.5">
                                                                <Telescope className="w-3 h-3" /> Professional Status
                                                            </p>
                                                            <p className="text-xs font-bold text-slate-600 truncate">{dm.role}</p>
                                                        </div>
                                                        <div className="hidden xl:block min-w-0">
                                                            <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-1.5 flex items-center gap-1.5">
                                                                <Mail className="w-3 h-3" /> Communication Vector
                                                            </p>
                                                            <p className="text-xs font-bold text-slate-500 truncate font-mono">{dm.email}</p>
                                                        </div>
                                                        <div className="hidden md:flex justify-end pr-8">
                                                            <div className="px-3 py-1 bg-emerald-50 text-emerald-600 border border-emerald-100 rounded-full text-[9px] font-black uppercase tracking-widest flex items-center gap-1.5">
                                                                <div className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
                                                                Positive Intent
                                                            </div>
                                                        </div>
                                                    </div>
                                                </div>
                                                
                                                <div className="flex items-center gap-3">
                                                    <div className="absolute top-0 right-0 p-2 opacity-0 group-hover:opacity-100 transition-opacity">
                                                        <Sparkles className="w-4 h-4 text-indigo-400/30" />
                                                    </div>
                                                    <Button 
                                                        className="bg-slate-900 hover:bg-indigo-600 text-white rounded-xl px-6 py-3 font-black text-[10px] uppercase tracking-widest shadow-xl shadow-slate-200 flex items-center gap-2 whitespace-nowrap active:scale-95 transition-all"
                                                        onClick={(e) => {
                                                            e.stopPropagation();
                                                            setModalContent({
                                                                type: 'discovery',
                                                                title: `Bridge Coordination: ${dm.name}`,
                                                                subtitle: `Inviting to Discovery Call`,
                                                                dm_id: dm.id,
                                                                subject: `Discovery Call: Digiotai Solutions x ${company?.name || 'Venture'}`,
                                                                body: `Hi ${dm.name},\n\nIt’s great to connect. Based on our recent exchange, I’d love to explore how we can support your goals at ${company?.name || 'your organization'}.\n\nPlease use the link below to book a suitable time for our introductory discovery discussion:\n\nhttps://calendly.com/vinaykumarreddy8374/discovery-call\n\nLooking forward to it!\n\nBest regards,\nDigiotai Solutions Team`,
                                                                icon: PhoneCall,
                                                                color: 'indigo'
                                                            });
                                                        }}
                                                    >
                                                        Send Discovery
                                                        <ArrowRight className="w-4 h-4" />
                                                    </Button>
                                                </div>
                                            </motion.div>
                                        );
                                    })
                                )}
                            </div>
                        </div>
                    )}
                </div>
            </main>
        </div>
    );
};

const ViewTab = ({ active, onClick, label, icon: Icon }) => (
    <button 
        onClick={onClick}
        className={cn(
            "relative px-2 py-6 flex items-center gap-2.5 transition-all duration-300 group",
            active ? "text-slate-900" : "text-slate-400 hover:text-slate-600"
        )}
    >
        <Icon className={cn("w-4 h-4 transition-colors", active ? "text-blue-600" : "group-hover:text-slate-500")} />
        <span className="text-[10px] font-black uppercase tracking-[0.2em]">{label}</span>
        {active && (
            <motion.div 
                layoutId="activeIndicator"
                className="absolute bottom-0 left-0 right-0 h-1 bg-blue-600 rounded-full"
                transition={{ type: "spring", bounce: 0.2, duration: 0.6 }}
            />
        )}
    </button>
);

const SectionHeader = ({ icon: Icon, color, label, count, badge }) => (
    <div className="flex items-center justify-between">
        <div className="flex items-center gap-6">
            <div className={cn(
                "w-14 h-14 rounded-2xl flex items-center justify-center shadow-2xl transition-transform hover:scale-105",
                color === 'blue' ? "bg-blue-600 shadow-blue-100/50 text-white" :
                color === 'indigo' ? "bg-indigo-600 shadow-indigo-100/50 text-white" :
                color === 'cyan' ? "bg-cyan-600 shadow-cyan-100/50 text-white" :
                "bg-emerald-600 shadow-emerald-100/50 text-white"
            )}>
                <Icon className="w-7 h-7" />
            </div>
            <div>
                <div className="flex items-center gap-3">
                    <span className="text-xs font-black text-slate-200 uppercase tracking-widest">{count}</span>
                    <h2 className="text-2xl font-black text-slate-900 tracking-tight">{label}</h2>
                </div>
                {badge && <p className="text-xs font-bold text-slate-400 uppercase tracking-widest mt-1">{badge}</p>}
            </div>
        </div>
    </div>
);

const LoadingState = ({ label, className }) => (
    <div className={cn("py-20 flex flex-col items-center justify-center text-center bg-white border border-dashed border-slate-200 rounded-[2.5rem]", className)}>
        <Loader2 className="w-8 h-8 animate-spin text-blue-200 mb-6" />
        <p className="text-sm font-bold text-slate-400 italic tracking-tight uppercase">{label}</p>
    </div>
);

export default CampaignWorkspace;
