import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import { Button } from './Button';
import { Menu, X, Rocket, Zap, BarChart3, Database } from 'lucide-react';
import { cn } from '../lib/utils';
import { Link } from 'react-router-dom';

const navItems = [
  { name: 'Home', path: '/', icon: Rocket },
  { name: 'Create Campaign', path: '/create-campaign', icon: Zap },
  { name: 'Active Campaigns', path: '/active-campaigns', icon: BarChart3 },
  { name: 'Inactive Campaigns', path: '/inactive-campaigns', icon: Database },
];

const Header = () => {
    const navigate = useNavigate();
    const [scrolled, setScrolled] = useState(false);
    const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

    useEffect(() => {
        const handleScroll = () => {
            setScrolled(window.scrollY > 20);
        };
        window.addEventListener('scroll', handleScroll);
        return () => window.removeEventListener('scroll', handleScroll);
    }, []);

    return (
        <motion.header 
            className={cn(
                "fixed top-0 left-0 right-0 z-50 transition-all duration-300 border-b border-transparent",
                scrolled ? "bg-white/80 backdrop-blur-md border-indigo-100 shadow-sm py-3" : "bg-transparent py-5"
            )}
            initial={{ y: -100 }}
            animate={{ y: 0 }}
            transition={{ type: "spring", stiffness: 300, damping: 30 }}
        >
            <div className="w-full px-10 flex items-center justify-between">
                
                {/* Logo Section */}
                <motion.div 
                    className="flex items-center gap-4 cursor-pointer group"
                    onClick={() => navigate('/')}
                    whileHover={{ scale: 1.05 }}
                >
                    <div className="relative w-11 h-11 overflow-hidden rounded-xl bg-white p-1 shadow-sm ring-1 ring-slate-200 group-hover:ring-indigo-300 group-hover:shadow-md transition-all">
                        <img src="/logo.jpg" alt="DIGIOTAI" className="w-full h-full object-cover rounded-lg" />
                    </div>
                    
                    <div className="flex flex-col justify-center">
                        <span className="text-xl font-extrabold tracking-tight text-slate-800 leading-none group-hover:text-indigo-700 transition-colors">
                            DIGIOTAI
                        </span>
                        <span className="text-[0.7rem] font-bold text-slate-500 uppercase tracking-[0.25em] leading-none mt-1">
                            Solutions
                        </span>
                    </div>
                </motion.div>

                {/* Desktop Navigation */}
                <nav className="absolute left-1/2 transform -translate-x-1/2 hidden md:flex items-center gap-2">
                    {navItems.map((item) => (
                        <Link to={item.path} key={item.name}>
                            <motion.div 
                                className="px-5 py-2.5 rounded-full text-sm font-medium text-slate-600 hover:text-indigo-600 hover:bg-indigo-50 transition-colors flex items-center gap-2"
                                whileHover={{ y: -1 }}
                                whileTap={{ scale: 0.95 }}
                            >
                                {item.name}
                            </motion.div>
                        </Link>
                    ))}
                </nav>

                {/* Mobile Menu Toggle */}
                <div className="md:hidden">
                    <Button variant="ghost" size="icon" onClick={() => setMobileMenuOpen(!mobileMenuOpen)}>
                        {mobileMenuOpen ? <X className="w-6 h-6 text-slate-700" /> : <Menu className="w-6 h-6 text-slate-700" />}
                    </Button>
                </div>
            </div>

            {/* Mobile Menu Dropdown */}
            <AnimatePresence>
                {mobileMenuOpen && (
                    <motion.div 
                        className="md:hidden absolute top-full left-0 w-full bg-white border-b border-indigo-50 shadow-lg px-4 py-4 flex flex-col gap-2"
                        initial={{ opacity: 0, height: 0 }}
                        animate={{ opacity: 1, height: 'auto' }}
                        exit={{ opacity: 0, height: 0 }}
                    >
                        {navItems.map((item) => (
                            <Link to={item.path} key={item.name} onClick={() => setMobileMenuOpen(false)}>
                                <div className="p-3 rounded-lg hover:bg-indigo-50 flex items-center gap-3 text-slate-700">
                                    <div className="p-2 bg-indigo-100/50 rounded-md text-indigo-600">
                                        <item.icon className="w-5 h-5" />
                                    </div>
                                    <span className="font-medium">{item.name}</span>
                                </div>
                            </Link>
                        ))}
                    </motion.div>
                )}
            </AnimatePresence>
        </motion.header>
    );
};

export default Header;
