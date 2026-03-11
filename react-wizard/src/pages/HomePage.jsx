import React from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Sparkles, Zap, ArrowRight, BarChart3, Brain, Video, Target, Users, Palette, FileText, TrendingUp, Shield } from 'lucide-react';

const HomePage = () => {
  const navigate = useNavigate();

  const features = [
    {
      icon: Brain,
      title: "AI Strategy",
      description: "Get data-driven insights from competitor analysis and market research to craft winning campaigns"
    },
    {
      icon: Target,
      title: "Smart Targeting",
      description: "Identify your ideal audience with psychographic profiling and behavioral analysis"
    },
    {
      icon: Users,
      title: "Competitor Research",
      description: "Discover what works in your industry by analyzing thousands of successful ads"
    },
    {
      icon: Palette,
      title: "Creative Studio",
      description: "Generate on-brand scripts, storyboards, and visuals tailored to your product"
    },
    {
      icon: Video,
      title: "Video Production",
      description: "Create professional video ads with AI avatars, voices, and dynamic animations"
    },
    {
      icon: BarChart3,
      title: "Analytics Dashboard",
      description: "Track performance metrics and optimize campaigns with real-time insights"
    }
  ];

  const howItWorks = [
    {
      step: "01",
      title: "Upload Your Product",
      description: "Share product details, images, and brand assets. Our AI analyzes everything to understand your offering."
    },
    {
      step: "02",
      title: "AI Research",
      description: "We scan thousands of ads in your niche, identifying winning patterns, hooks, and psychological triggers."
    },
    {
      step: "03",
      title: "Generate Campaign",
      description: "Get multiple ad variations with scripts, visuals, and targeting strategies customized for your brand."
    },
    {
      step: "04",
      title: "Launch & Optimize",
      description: "Publish to your platforms and track performance with our analytics to continuously improve results."
    }
  ];

  return (
    <div className="home-page">
      {/* Navbar */}
      <motion.nav 
        className="home-navbar"
        initial={{ y: -20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ duration: 0.6 }}
      >
        <div className="nav-content">
          <div className="logo-section" onClick={() => navigate('/')}>
            <Zap className="logo-icon" size={32} />
            <h1 className="logo-text">SPECTRA</h1>
          </div>
          <div className="nav-actions">
            <button className="nav-btn" onClick={() => navigate('/auth')}>
              Login
            </button>
            <button className="nav-btn-primary" onClick={() => navigate('/auth')}>
              Get Started <ArrowRight size={18} />
            </button>
          </div>
        </div>
      </motion.nav>

      {/* Floating gradient blobs */}
      <div className="floating-blobs">
        <motion.div 
          className="blob blob-1"
          animate={{
            x: [0, 50, 0],
            y: [0, -50, 0],
            scale: [1, 1.2, 1],
          }}
          transition={{
            duration: 15,
            repeat: Infinity,
            ease: "easeInOut"
          }}
        />
        <motion.div 
          className="blob blob-2"
          animate={{
            x: [0, -50, 0],
            y: [0, 50, 0],
            scale: [1, 1.3, 1],
          }}
          transition={{
            duration: 20,
            repeat: Infinity,
            ease: "easeInOut"
          }}
        />
      </div>

      {/* Hero Section */}
      <section className="hero-section">
        <motion.div
          className="hero-content"
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.2 }}
        >
          <motion.div 
            className="hero-badge"
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            transition={{ duration: 0.5, delay: 0.4 }}
          >
            <Sparkles size={16} />
            <span>AI-Powered Ad Generation</span>
          </motion.div>
          
          <h1 className="hero-title">
            Create Viral Ads in
            <span className="gradient-text"> Minutes</span>
          </h1>
          
          <p className="hero-description">
            Transform your product into scroll-stopping video ads with AI. 
            Research competitors, generate scripts, and produce videos—all automated.
          </p>
          
          <div className="hero-actions">
            <button className="cta-btn-primary" onClick={() => navigate('/auth')}>
              <Sparkles size={20} />
              Start Creating Free
            </button>
            <button className="cta-btn-secondary" onClick={() => navigate('/auth')}>
              Watch Demo
            </button>
          </div>
        </motion.div>
      </section>

      {/* Features Section */}
      <section className="features-section">
        <motion.h2 
          className="section-title"
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
        >
          Everything You Need to Scale
        </motion.h2>
        <motion.p 
          className="section-subtitle"
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ delay: 0.1 }}
        >
          From research to production, all the tools in one platform
        </motion.p>
        
        <div className="features-grid">
          {features.map((feature, index) => {
            const Icon = feature.icon;
            return (
              <motion.div
                key={index}
                className="feature-card"
                initial={{ opacity: 0, y: 30 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: index * 0.1 }}
                whileHover={{ y: -8, scale: 1.02 }}
              >
                <div className="feature-icon">
                  <Icon size={28} />
                </div>
                <h3 className="feature-title">{feature.title}</h3>
                <p className="feature-description">{feature.description}</p>
              </motion.div>
            );
          })}
        </div>
      </section>

      {/* How It Works Section */}
      <section className="how-it-works-section">
        <motion.h2 
          className="section-title"
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
        >
          How It Works
        </motion.h2>
        <motion.p 
          className="section-subtitle"
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ delay: 0.1 }}
        >
          Launch high-performing ads in 4 simple steps
        </motion.p>

        <div className="steps-grid">
          {howItWorks.map((step, index) => (
            <motion.div
              key={index}
              className="step-card"
              initial={{ opacity: 0, x: index % 2 === 0 ? -30 : 30 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true }}
              transition={{ delay: index * 0.15 }}
            >
              <div className="step-number">{step.step}</div>
              <div className="step-content">
                <h3 className="step-title">{step.title}</h3>
                <p className="step-description">{step.description}</p>
              </div>
              {index < howItWorks.length - 1 && (
                <div className="step-connector"></div>
              )}
            </motion.div>
          ))}
        </div>
      </section>

      {/* Stats Section */}
      <section className="stats-section">
        <div className="stats-grid">
          <motion.div 
            className="stat-card"
            initial={{ opacity: 0, scale: 0.9 }}
            whileInView={{ opacity: 1, scale: 1 }}
            viewport={{ once: true }}
          >
            <div className="stat-number">10K+</div>
            <div className="stat-label">Ads Generated</div>
          </motion.div>
          <motion.div 
            className="stat-card"
            initial={{ opacity: 0, scale: 0.9 }}
            whileInView={{ opacity: 1, scale: 1 }}
            viewport={{ once: true }}
            transition={{ delay: 0.1 }}
          >
            <div className="stat-number">3.5x</div>
            <div className="stat-label">Avg. Conversion Boost</div>
          </motion.div>
          <motion.div 
            className="stat-card"
            initial={{ opacity: 0, scale: 0.9 }}
            whileInView={{ opacity: 1, scale: 1 }}
            viewport={{ once: true }}
            transition={{ delay: 0.2 }}
          >
            <div className="stat-number">85%</div>
            <div className="stat-label">Time Saved</div>
          </motion.div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="cta-section">
        <motion.div
          className="cta-content"
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
        >
          <h2 className="cta-title">Ready to Transform Your Ad Game?</h2>
          <p className="cta-description">
            Join thousands of marketers creating scroll-stopping ads with AI
          </p>
          <button className="cta-btn-large" onClick={() => navigate('/auth')}>
            <Sparkles size={24} />
            Start Creating for Free
          </button>
        </motion.div>
      </section>

      <style>{`
        .home-page {
          min-height: 100vh;
          width: 100%;
          overflow-x: hidden;
          position: relative;
          background: linear-gradient(135deg, #0a0a1f 0%, #1a0a2e 50%, #0f0f23 100%);
        }

        /* Floating Blobs */
        .floating-blobs {
          position: fixed;
          top: 0;
          left: 0;
          width: 100%;
          height: 100%;
          pointer-events: none;
          z-index: 0;
        }

        .blob {
          position: absolute;
          border-radius: 50%;
          filter: blur(120px);
          opacity: 0.3;
        }

        .blob-1 {
          width: 600px;
          height: 600px;
          background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
          top: -200px;
          right: -150px;
        }

        .blob-2 {
          width: 500px;
          height: 500px;
          background: linear-gradient(135deg, #ec4899 0%, #8b5cf6 100%);
          bottom: -150px;
          left: -150px;
        }

        /* Navbar */
        .home-navbar {
          position: fixed;
          top: 0;
          left: 0;
          right: 0;
          z-index: 100;
          padding: 20px 0;
          backdrop-filter: blur(20px);
          background: rgba(10, 10, 31, 0.8);
          border-bottom: 1px solid rgba(255, 255, 255, 0.08);
        }

        .nav-content {
          max-width: 1200px;
          margin: 0 auto;
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 0 40px;
        }

        .logo-section {
          display: flex;
          align-items: center;
          gap: 12px;
          cursor: pointer;
          transition: transform 0.3s ease;
        }

        .logo-section:hover {
          transform: scale(1.05);
        }

        .logo-icon {
          color: #818cf8;
          filter: drop-shadow(0 0 12px rgba(129, 140, 248, 0.5));
        }

        .logo-text {
          font-size: 1.8rem;
          font-weight: 900;
          letter-spacing: -1px;
          background: linear-gradient(135deg, #ffffff 0%, #818cf8 100%);
          -webkit-background-clip: text;
          -webkit-text-fill-color: transparent;
          margin: 0;
        }

        .nav-actions {
          display: flex;
          gap: 16px;
          align-items: center;
        }

        .nav-btn {
          background: transparent;
          border: 1px solid rgba(255, 255, 255, 0.15);
          color: white;
          padding: 10px 24px;
          border-radius: 10px;
          font-weight: 600;
          cursor: pointer;
          transition: all 0.3s ease;
          font-size: 0.95rem;
        }

        .nav-btn:hover {
          background: rgba(255, 255, 255, 0.05);
          border-color: rgba(255, 255, 255, 0.3);
          transform: translateY(-2px);
        }

        .nav-btn-primary {
          background: linear-gradient(135deg, #6366f1, #a855f7);
          border: none;
          color: white;
          padding: 10px 24px;
          border-radius: 10px;
          font-weight: 600;
          cursor: pointer;
          display: flex;
          align-items: center;
          gap: 8px;
          transition: all 0.3s ease;
          font-size: 0.95rem;
          box-shadow: 0 4px 20px rgba(99, 102, 241, 0.3);
        }

        .nav-btn-primary:hover {
          transform: translateY(-2px);
          box-shadow: 0 8px 30px rgba(99, 102, 241, 0.5);
        }

        /* Hero Section */
        .hero-section {
          position: relative;
          z-index: 1;
          min-height: 100vh;
          display: flex;
          align-items: center;
          justify-content: center;
          padding: 120px 40px 80px;
        }

        .hero-content {
          max-width: 900px;
          text-align: center;
        }

        .hero-badge {
          display: inline-flex;
          align-items: center;
          gap: 8px;
          background: rgba(99, 102, 241, 0.1);
          border: 1px solid rgba(99, 102, 241, 0.3);
          padding: 8px 20px;
          border-radius: 50px;
          color: #c7d2fe;
          font-size: 0.9rem;
          font-weight: 600;
          margin-bottom: 32px;
          backdrop-filter: blur(10px);
        }

        .hero-title {
          font-size: 5rem;
          font-weight: 900;
          line-height: 1.1;
          margin: 0 0 28px 0;
          color: white;
          letter-spacing: -2px;
        }

        .gradient-text {
          background: linear-gradient(135deg, #818cf8 0%, #c084fc 50%, #ec4899 100%);
          -webkit-background-clip: text;
          -webkit-text-fill-color: transparent;
        }

        .hero-description {
          font-size: 1.3rem;
          color: rgba(255, 255, 255, 0.7);
          margin: 0 0 48px 0;
          line-height: 1.7;
          max-width: 700px;
          margin-left: auto;
          margin-right: auto;
        }

        .hero-actions {
          display: flex;
          gap: 20px;
          justify-content: center;
          align-items: center;
        }

        .cta-btn-primary {
          background: linear-gradient(135deg, #6366f1, #a855f7);
          border: none;
          color: white;
          padding: 16px 32px;
          border-radius: 12px;
          font-size: 1.1rem;
          font-weight: 700;
          cursor: pointer;
          display: flex;
          align-items: center;
          gap: 10px;
          transition: all 0.4s cubic-bezier(0.16, 1, 0.3, 1);
          box-shadow: 0 8px 32px rgba(99, 102, 241, 0.4);
        }

        .cta-btn-primary:hover {
          transform: translateY(-4px);
          box-shadow: 0 16px 48px rgba(99, 102, 241, 0.6);
        }

        .cta-btn-secondary {
          background: transparent;
          border: 2px solid rgba(255, 255, 255, 0.2);
          color: white;
          padding: 16px 32px;
          border-radius: 12px;
          font-size: 1.1rem;
          font-weight: 700;
          cursor: pointer;
          transition: all 0.3s ease;
        }

        .cta-btn-secondary:hover {
          background: rgba(255, 255, 255, 0.05);
          border-color: rgba(255, 255, 255, 0.4);
          transform: translateY(-2px);
        }

        /* Features Section */
        .features-section {
          position: relative;
          z-index: 1;
          padding: 80px 40px;
          max-width: 1200px;
          margin: 0 auto;
        }

        .section-title {
          font-size: 3rem;
          font-weight: 800;
          text-align: center;
          margin: 0 0 16px 0;
          color: white;
          letter-spacing: -1px;
        }

        .section-subtitle {
          font-size: 1.2rem;
          color: rgba(255, 255, 255, 0.6);
          text-align: center;
          margin: 0 0 60px 0;
        }

        .features-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
          gap: 28px;
        }

        .feature-card {
          background: rgba(255, 255, 255, 0.03);
          backdrop-filter: blur(20px);
          border: 1px solid rgba(255, 255, 255, 0.08);
          border-radius: 20px;
          padding: 36px 28px;
          transition: all 0.4s cubic-bezier(0.16, 1, 0.3, 1);
          cursor: pointer;
        }

        .feature-card:hover {
          background: rgba(255, 255, 255, 0.05);
          border-color: rgba(99, 102, 241, 0.3);
          box-shadow: 0 20px 60px rgba(0, 0, 0, 0.4);
        }

        .feature-icon {
          width: 64px;
          height: 64px;
          background: linear-gradient(135deg, #6366f1, #a855f7);
          border-radius: 16px;
          display: flex;
          align-items: center;
          justify-content: center;
          color: white;
          margin-bottom: 20px;
          box-shadow: 0 8px 24px rgba(99, 102, 241, 0.3);
        }

        .feature-title {
          font-size: 1.4rem;
          font-weight: 700;
          margin: 0 0 12px 0;
          color: white;
        }

        .feature-description {
          font-size: 0.95rem;
          color: rgba(255, 255, 255, 0.6);
          line-height: 1.6;
          margin: 0;
        }

        /* How It Works Section */
        .how-it-works-section {
          position: relative;
          z-index: 1;
          padding: 80px 40px;
          max-width: 1000px;
          margin: 0 auto;
        }

        .steps-grid {
          display: flex;
          flex-direction: column;
          gap: 40px;
        }

        .step-card {
          display: flex;
          gap: 24px;
          align-items: flex-start;
          position: relative;
          padding: 32px;
          background: rgba(255, 255, 255, 0.02);
          border: 1px solid rgba(255, 255, 255, 0.08);
          border-radius: 20px;
          transition: all 0.3s ease;
        }

        .step-card:hover {
          background: rgba(255, 255, 255, 0.04);
          border-color: rgba(99, 102, 241, 0.2);
          transform: translateX(8px);
        }

        .step-number {
          font-size: 3rem;
          font-weight: 900;
          background: linear-gradient(135deg, #818cf8 0%, #c084fc 100%);
          -webkit-background-clip: text;
          -webkit-text-fill-color: transparent;
          line-height: 1;
          flex-shrink: 0;
        }

        .step-content {
          flex: 1;
        }

        .step-title {
          font-size: 1.6rem;
          font-weight: 700;
          margin: 0 0 12px 0;
          color: white;
        }

        .step-description {
          font-size: 1rem;
          color: rgba(255, 255, 255, 0.6);
          line-height: 1.7;
          margin: 0;
        }

        .step-connector {
          position: absolute;
          left: 85px;
          bottom: -40px;
          width: 2px;
          height: 40px;
          background: linear-gradient(180deg, rgba(99, 102, 241, 0.5), transparent);
        }

        /* Stats Section */
        .stats-section {
          position: relative;
          z-index: 1;
          padding: 80px 40px;
          max-width: 1200px;
          margin: 0 auto;
        }

        .stats-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
          gap: 32px;
        }

        .stat-card {
          text-align: center;
          padding: 40px 32px;
          background: rgba(99, 102, 241, 0.05);
          border: 1px solid rgba(99, 102, 241, 0.15);
          border-radius: 20px;
          backdrop-filter: blur(20px);
        }

        .stat-number {
          font-size: 3.5rem;
          font-weight: 900;
          background: linear-gradient(135deg, #818cf8 0%, #c084fc 100%);
          -webkit-background-clip: text;
          -webkit-text-fill-color: transparent;
          margin-bottom: 12px;
        }

        .stat-label {
          font-size: 1.1rem;
          color: rgba(255, 255, 255, 0.7);
          font-weight: 600;
        }

        /* CTA Section */
        .cta-section {
          position: relative;
          z-index: 1;
          padding: 100px 40px;
          max-width: 900px;
          margin: 0 auto;
        }

        .cta-content {
          text-align: center;
          padding: 60px 40px;
          background: linear-gradient(135deg, rgba(99, 102, 241, 0.1), rgba(168, 85, 247, 0.1));
          border: 1px solid rgba(99, 102, 241, 0.2);
          border-radius: 24px;
          backdrop-filter: blur(20px);
        }

        .cta-title {
          font-size: 3rem;
          font-weight: 900;
          margin: 0 0 20px 0;
          color: white;
          letter-spacing: -1px;
        }

        .cta-description {
          font-size: 1.3rem;
          color: rgba(255, 255, 255, 0.7);
          margin: 0 0 40px 0;
        }

        .cta-btn-large {
          background: linear-gradient(135deg, #6366f1, #a855f7);
          border: none;
          color: white;
          padding: 20px 48px;
          border-radius: 14px;
          font-size: 1.2rem;
          font-weight: 700;
          cursor: pointer;
          display: inline-flex;
          align-items: center;
          gap: 12px;
          transition: all 0.4s cubic-bezier(0.16, 1, 0.3, 1);
          box-shadow: 0 12px 40px rgba(99, 102, 241, 0.4);
        }

        .cta-btn-large:hover {
          transform: translateY(-4px);
          box-shadow: 0 20px 60px rgba(99, 102, 241, 0.6);
        }

        /* Responsive */
        @media (max-width: 768px) {
          .hero-title {
            font-size: 3rem;
          }

          .hero-description {
            font-size: 1.1rem;
          }

          .hero-actions {
            flex-direction: column;
            width: 100%;
          }

          .cta-btn-primary,
          .cta-btn-secondary {
            width: 100%;
            justify-content: center;
          }

          .section-title {
            font-size: 2rem;
          }

          .nav-content {
            padding: 0 20px;
          }

          .logo-text {
            font-size: 1.4rem;
          }

          .nav-actions {
            gap: 12px;
          }

          .nav-btn, .nav-btn-primary {
            padding: 8px 16px;
            font-size: 0.85rem;
          }
        }
      `}</style>
    </div>
  );
};

export default HomePage;
