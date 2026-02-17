import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import { Globe, ArrowRight } from 'lucide-react';
import { Button } from '../components/Button';
import axios from 'axios';
import API_BASE_URL from '../apiConfig';

const CreateCampaign = () => {
    const [campaignName, setCampaignName] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState('');
    const navigate = useNavigate();

    const handleCreate = async (e) => {
        e.preventDefault();
        if (!campaignName.trim()) {
            setError('Please enter a company name or website.');
            return;
        }

        setIsLoading(true);
        setError('');

        try {
            const response = await axios.post(`${API_BASE_URL}campaigns/initialize`, {
                name: campaignName
            });

            if (response.data.campaign_id) {
                // Navigate to the workspace for this campaign
                navigate(`/workspace/${response.data.campaign_id}`);
            } else {
                setError('Failed to create campaign. Please try again.');
            }
        } catch (err) {
            console.error('Error creating campaign:', err);
            setError('Could not connect to the server.');
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="min-h-screen bg-slate-50 flex items-center justify-center p-4 pt-20">
            <motion.div 
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="max-w-md w-full bg-white rounded-3xl shadow-2xl shadow-slate-200/60 p-10 flex flex-col items-center text-center"
            >
                {/* Icon Circle */}
                <div className="w-16 h-16 bg-indigo-50 rounded-2xl flex items-center justify-center mb-8 border border-indigo-100/50">
                    <Globe className="w-8 h-8 text-indigo-600" />
                </div>

                {/* Header */}
                <h1 className="text-3xl font-bold text-slate-900 mb-3 font-display">
                    Create New Campaign
                </h1>
                <p className="text-slate-500 text-sm mb-10 max-w-[280px]">
                    Enter your company name or website URL to begin the intelligence process.
                </p>

                {/* Form */}
                <form onSubmit={handleCreate} className="w-full text-left">
                    <div className="mb-6">
                        <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-3 ml-1">
                            Company Website or Name
                        </label>
                        <input
                            type="text"
                            placeholder="e.g. acme.com or Acme Corp"
                            value={campaignName}
                            onChange={(e) => setCampaignName(e.target.value)}
                            className="w-full px-5 py-4 bg-white border border-slate-200 rounded-xl text-slate-900 placeholder:text-slate-300 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 transition-all text-sm"
                        />
                    </div>

                    {error && (
                        <p className="text-red-500 text-xs mb-4 ml-1 italic">{error}</p>
                    )}

                    <Button
                        type="submit"
                        isLoading={isLoading}
                        className="w-full h-auto py-4 rounded-xl text-md gap-2 font-bold shadow-indigo-200/50 shadow-lg"
                    >
                        {isLoading ? 'Processing...' : 'Create Campaign'}
                        {!isLoading && <ArrowRight className="w-5 h-5" />}
                    </Button>
                </form>
            </motion.div>
        </div>
    );
};

export default CreateCampaign;
