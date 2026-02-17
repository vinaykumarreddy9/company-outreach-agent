import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import { 
    BarChart3, 
    Calendar, 
    ChevronRight, 
    PauseCircle, 
    AlertCircle, 
    Loader2,
    Search,
    Play,
    Trash2
} from 'lucide-react';
import { Button } from '../components/Button';
import axios from 'axios';
import { cn } from '../lib/utils';
import API_BASE_URL from '../apiConfig';

const CampaignList = ({ type = 'active' }) => {
    const [campaigns, setCampaigns] = useState([]);
    const [isLoading, setIsLoading] = useState(true);
    const [searchTerm, setSearchTerm] = useState('');
    const navigate = useNavigate();

    useEffect(() => {
        const fetchCampaigns = async () => {
            setIsLoading(true);
            try {
                const response = await axios.get(`${API_BASE_URL}campaigns`);
                const allCampaigns = response.data.campaigns || [];
                
                // Filter based on type
                const filtered = allCampaigns.filter(c => 
                    type === 'inactive' ? c.status === 'terminated' : c.status !== 'terminated'
                );
                setCampaigns(filtered);
            } catch (error) {
                console.error('Error fetching campaigns:', error);
            } finally {
                setIsLoading(false);
            }
        };

        fetchCampaigns();
    }, [type]);

    const handleDeactivate = async (e, id) => {
        e.stopPropagation();
        if (!window.confirm('Are you sure you want to deactivate this campaign?')) return;

        try {
            await axios.patch(`${API_BASE_URL}campaigns/${id}/status`, { status: 'terminated' });
            window.location.reload();
        } catch (error) {
            console.error('Error deactivating campaign:', error);
        }
    };

    const handleActivate = async (e, id) => {
        e.stopPropagation();
        try {
            await axios.patch(`${API_BASE_URL}campaigns/${id}/status`, { status: 'active' });
            window.location.reload();
        } catch (error) {
            console.error('Error activating campaign:', error);
        }
    };

    const handleDelete = async (e, id) => {
        e.stopPropagation();
        if (!window.confirm('CRITICAL ACTION: This will permanently delete ALL data, emails, and research associated with this campaign. This cannot be undone. Proceed?')) return;

        try {
            await axios.delete(`${API_BASE_URL}campaigns/${id}`);
            setCampaigns(prev => prev.filter(c => c.id !== id));
        } catch (error) {
            console.error('Error deleting campaign:', error);
            alert('Failed to delete campaign. Please try again.');
        }
    };

    const formatDate = (dateString) => {
        return new Date(dateString).toLocaleDateString('en-US', {
            month: 'short',
            day: 'numeric',
            year: 'numeric'
        });
    };

    const filteredCampaigns = campaigns.filter(c => 
        c.name.toLowerCase().includes(searchTerm.toLowerCase())
    );

    return (
        <div className="min-h-screen bg-slate-50 pt-28 pb-20 px-4 md:px-8">
            <div className="max-w-7xl mx-auto">
                <header className="flex flex-col md:flex-row md:items-end justify-between mb-10 gap-6">
                    <div>
                        <h1 className="text-4xl font-extrabold text-slate-900 tracking-tight font-display mb-2">
                            {type === 'active' ? 'Active Campaigns' : 'Archived Campaigns'}
                        </h1>
                        <p className="text-slate-500 max-w-xl">
                            {type === 'active' 
                                ? 'Manage and monitor your ongoing outreach programs and intelligence pipelines.' 
                                : 'Review terminated outreach programs and historical research data.'}
                        </p>
                    </div>

                    <div className="flex items-center gap-3">
                        <div className="relative">
                            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                            <input 
                                type="text"
                                placeholder="Search campaigns..."
                                value={searchTerm}
                                onChange={(e) => setSearchTerm(e.target.value)}
                                className="pl-10 pr-4 py-2 bg-white border border-slate-200 rounded-full text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 transition-all w-64"
                            />
                        </div>
                    </div>
                </header>

                {isLoading ? (
                    <div className="flex flex-col items-center justify-center py-32 text-slate-400">
                        <Loader2 className="w-10 h-10 animate-spin mb-4 text-indigo-500" />
                        <p className="font-medium">Gathering campaign data...</p>
                    </div>
                ) : filteredCampaigns.length > 0 ? (
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                        <AnimatePresence mode='popLayout'>
                            {filteredCampaigns.map((campaign, idx) => (
                                <motion.div
                                    key={campaign.id}
                                    layout
                                    initial={{ opacity: 0, y: 20 }}
                                    animate={{ opacity: 1, y: 0 }}
                                    exit={{ opacity: 0, scale: 0.95 }}
                                    transition={{ delay: idx * 0.05 }}
                                    onClick={() => navigate(`/workspace/${campaign.id}`)}
                                    className="group bg-white rounded-2xl border border-slate-200 p-6 shadow-sm hover:shadow-xl hover:shadow-indigo-100/40 transition-all cursor-pointer flex flex-col justify-between"
                                >
                                    <div>
                                        <div className="flex items-start justify-between mb-4">
                                            <div className={cn(
                                                "p-3 rounded-xl",
                                                campaign.status === 'terminated' ? "bg-slate-100 text-slate-500" : "bg-indigo-50 text-indigo-600"
                                            )}>
                                                <BarChart3 className="w-6 h-6" />
                                            </div>
                                            <span className={cn(
                                                "text-[10px] font-bold uppercase tracking-widest px-2.5 py-1 rounded-full",
                                                campaign.status === 'active' ? "bg-green-50 text-green-600 border border-green-100" :
                                                campaign.status === 'terminated' ? "bg-slate-100 text-slate-500 border border-slate-200" :
                                                "bg-amber-50 text-amber-600 border border-amber-100"
                                            )}>
                                                {campaign.status}
                                            </span>
                                        </div>
                                        
                                        <h3 className="text-xl font-bold text-slate-900 mb-2 truncate group-hover:text-indigo-600 transition-colors">
                                            {campaign.name}
                                        </h3>
                                        
                                        <div className="flex items-center gap-2 text-slate-400 text-xs mb-6">
                                            <Calendar className="w-3.5 h-3.5" />
                                            <span>Created on {formatDate(campaign.created_at)}</span>
                                        </div>
                                    </div>

                                    <div className="flex items-center justify-between pt-4 border-t border-slate-50">
                                        <div className="flex items-center gap-1 text-indigo-600 font-bold text-xs">
                                            VIEW DETAILS <ChevronRight className="w-3.5 h-3.5" />
                                        </div>
                                        
                                        {type === 'active' ? (
                                            <div className="flex items-center gap-2">
                                                <Button 
                                                    variant="ghost" 
                                                    size="sm" 
                                                    onClick={(e) => handleDeactivate(e, campaign.id)}
                                                    className="text-slate-400 hover:text-red-500 hover:bg-red-50 py-1 h-auto"
                                                >
                                                    <PauseCircle className="w-4 h-4 mr-2" />
                                                    Deactivate
                                                </Button>
                                                <button 
                                                    onClick={(e) => handleDelete(e, campaign.id)}
                                                    className="p-2 text-slate-300 hover:text-red-600 hover:bg-red-50 rounded-lg transition-all"
                                                    title="Delete Campaign"
                                                >
                                                    <Trash2 className="w-4 h-4" />
                                                </button>
                                            </div>
                                        ) : (
                                            <div className="flex items-center gap-2">
                                                <Button 
                                                    variant="ghost" 
                                                    size="sm" 
                                                    onClick={(e) => handleActivate(e, campaign.id)}
                                                    className="text-indigo-600 hover:text-indigo-700 hover:bg-indigo-50 py-1 h-auto font-bold"
                                                >
                                                    <Play className="w-3.5 h-3.5 mr-2 fill-current" />
                                                    Activate
                                                </Button>
                                                <button 
                                                    onClick={(e) => handleDelete(e, campaign.id)}
                                                    className="p-2 text-slate-300 hover:text-red-600 hover:bg-red-50 rounded-lg transition-all"
                                                    title="Delete Campaign"
                                                >
                                                    <Trash2 className="w-4 h-4" />
                                                </button>
                                            </div>
                                        )}
                                    </div>
                                </motion.div>
                            ))}
                        </AnimatePresence>
                    </div>
                ) : (
                    <motion.div 
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        className="bg-white border border-dashed border-slate-300 rounded-2xl py-24 flex flex-col items-center justify-center text-center"
                    >
                        <div className="w-16 h-16 bg-slate-50 rounded-full flex items-center justify-center mb-6">
                            <AlertCircle className="w-8 h-8 text-slate-300" />
                        </div>
                        <h2 className="text-2xl font-bold text-slate-800 mb-2">No campaigns found</h2>
                        <p className="text-slate-500 mb-8 max-w-sm">
                            {searchTerm 
                                ? `We couldn't find any campaigns matching "${searchTerm}".`
                                : type === 'active' 
                                    ? "You don't have any active outreach programs yet. Launch one to get started." 
                                    : "You don't have any archived campaigns."}
                        </p>
                        {!searchTerm && type === 'active' && (
                            <Button onClick={() => navigate('/create-campaign')}>
                                Start Your First Campaign
                            </Button>
                        )}
                    </motion.div>
                )}
            </div>
        </div>
    );
};

export default CampaignList;
