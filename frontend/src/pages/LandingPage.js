import React from 'react';
import { motion } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import { Button } from '../components/Button';
import { Sparkles, Zap, BarChart3 } from 'lucide-react';
import { cn } from '../lib/utils';

const features = [
  { 
    title: "AI-Powered Discovery", 
    desc: "Uses GPT-4o & Tavily to find verified decision makers.",
    icon: Sparkles,
    color: "bg-indigo-500"
  },
  { 
    title: "Ultra-Personalized Drafts", 
    desc: "Generates placeholder-free, value-driven email copy.",
    icon: Zap,
    color: "bg-violet-500"
  },
  { 
    title: "Smart Campaign Management", 
    desc: "Track active leads and automate follow-ups securely.",
    icon: BarChart3,
    color: "bg-cyan-500"
  }
];

const LandingPage = () => {
    const navigate = useNavigate();

    return (
        <div className="min-h-screen bg-gradient-to-br from-indigo-50 via-white to-violet-50 font-sans text-slate-900 pt-20">
            {/* Background Pattern */}
            <div className="absolute inset-x-0 top-0 -z-10 h-full overflow-hidden opacity-30">
                <div className="absolute left-[calc(50%-11rem)] aspect-[1155/678] w-[36.125rem] -translate-x-1/2 rotate-[30deg] bg-gradient-to-tr from-[#ff80b5] to-[#9089fc] opacity-30 sm:left-[calc(50%-30rem)] sm:w-[72.1875rem]" style={{clipPath: "polygon(74.1% 44.1%, 100% 61.6%, 97.5% 26.9%, 85.5% 0.1%, 80.7% 2%, 72.5% 32.5%, 60.2% 62.4%, 52.4% 68.1%, 47.5% 58.3%, 45.2% 34.5%, 27.5% 76.7%, 0.1% 64.9%, 17.9% 100%, 27.6% 76.8%, 76.1% 97.7%, 74.1% 44.1%)"}} />
            </div>

            <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20 lg:py-32 flex flex-col items-center text-center">
                
                {/* Badge */}
                <motion.div 
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.1 }}
                    className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-indigo-50 border border-indigo-100 text-indigo-700 text-sm font-medium mb-8"
                >
                    <span className="relative flex h-2 w-2">
                      <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-indigo-400 opacity-75"></span>
                      <span className="relative inline-flex rounded-full h-2 w-2 bg-indigo-500"></span>
                    </span>
                    Now with Phase 1 Intelligence Engine
                </motion.div>

                {/* Hero Title */}
                <motion.h1 
                    className="text-5xl md:text-7xl font-bold tracking-tight text-slate-900 mb-6 font-display"
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.2 }}
                >
                    Outreach that feels <br/>
                    <span className="bg-clip-text text-transparent bg-gradient-to-r from-indigo-600 via-violet-600 to-cyan-500">
                        Human, yet Scalable
                    </span>
                </motion.h1>

                {/* Subtitle */}
                <motion.p 
                    className="text-lg md:text-xl text-slate-600 max-w-2xl mb-10 leading-relaxed"
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.3 }}
                >
                    Stop sending generic spam. Our AI agent researches your prospects, deeply understands their business, and crafts hyper-personalized emails that actually get replies.
                </motion.p>

                {/* CTA Buttons */}
                <motion.div 
                    className="flex flex-col sm:flex-row gap-4 w-full sm:w-auto"
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.4 }}
                >
                    <Button 
                        size="lg" 
                        variant="primary" 
                        onClick={() => navigate('/create-campaign')}
                        className="gap-2 shadow-indigo-200/50 shadow-lg text-lg px-8 py-6 h-auto"
                    >
                        <Zap className="w-5 h-5 fill-current" />
                        Start New Campaign
                    </Button>
                    <Button 
                        size="lg" 
                        variant="secondary" 
                        onClick={() => navigate('/active-campaigns')}
                        className="gap-2 text-lg px-8 py-6 h-auto"
                    >
                        <BarChart3 className="w-5 h-5" />
                        View Dashboard
                    </Button>
                </motion.div>

                {/* Feature Grid */}
                <motion.div 
                    className="grid grid-cols-1 md:grid-cols-3 gap-8 mt-24 w-full text-left"
                    initial={{ opacity: 0, y: 40 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.6, duration: 0.8 }}
                >
                    {features.map((feature, idx) => (
                        <div key={idx} className="group p-8 rounded-2xl bg-white border border-slate-100 shadow-xl shadow-slate-200/40 hover:shadow-2xl hover:shadow-indigo-100/40 transition-all duration-300 hover:-translate-y-1">
                            <div className={cn("w-12 h-12 rounded-lg flex items-center justify-center mb-6 text-white shadow-lg", feature.color)}>
                                <feature.icon className="w-6 h-6" />
                            </div>
                            <h3 className="text-xl font-bold text-slate-900 mb-3">{feature.title}</h3>
                            <p className="text-slate-600 leading-relaxed">{feature.desc}</p>
                        </div>
                    ))}
                </motion.div>

                {/* Trust/Stats Section */}
                <motion.div 
                    className="mt-24 pt-10 border-t border-slate-200 w-full flex flex-wrap justify-center gap-12 md:gap-24 opacity-70 grayscale hover:grayscale-0 transition-all duration-500"
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{ delay: 0.8 }}
                >
                    {/* Placeholder for trusted logos or stats */}
                    <div className="text-center">
                        <div className="text-3xl font-bold text-slate-900">98%</div>
                        <div className="text-sm font-medium text-slate-500 uppercase tracking-wider">Delivery Rate</div>
                    </div>
                    <div className="text-center">
                        <div className="text-3xl font-bold text-slate-900">5x</div>
                        <div className="text-sm font-medium text-slate-500 uppercase tracking-wider">More Replies</div>
                    </div>
                    <div className="text-center">
                        <div className="text-3xl font-bold text-slate-900">24/7</div>
                        <div className="text-sm font-medium text-slate-500 uppercase tracking-wider">Automated</div>
                    </div>
                </motion.div>

            </main>
        </div>
    );
};

export default LandingPage;
