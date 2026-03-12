import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion, AnimatePresence, useMotionValue, useSpring, useTransform } from 'framer-motion';
import { Mail, Lock, User, ArrowRight, Sparkles, Building2, Eye, EyeOff, CheckCircle2, XCircle, AlertCircle, Zap, Home } from 'lucide-react';
import { authService } from '../services/api';

function AuthPage({ onLogin }) {
  const navigate = useNavigate();
  const [isLogin, setIsLogin] = useState(true);
  const [formData, setFormData] = useState({ username: '', password: '', email: '', fullName: '', companyId: '' });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [fieldErrors, setFieldErrors] = useState({});
  const [touched, setTouched] = useState({});

  // Mouse Tracking for Parallax
  const mouseX = useMotionValue(0);
  const mouseY = useMotionValue(0);

  // Smooth springs for buttery motion
  const springX = useSpring(mouseX, { stiffness: 100, damping: 30 });
  const springY = useSpring(mouseY, { stiffness: 100, damping: 30 });

  // Transforms for parallax layers
  const textX = useTransform(springX, [0, 2000], [-30, 30]);
  const textY = useTransform(springY, [0, 1000], [-30, 30]);

  const blob1X = useTransform(springX, [0, 2000], [-60, 60]);
  const blob1Y = useTransform(springY, [0, 1000], [-60, 60]);

  const blob2X = useTransform(springX, [0, 2000], [60, -60]);
  const blob2Y = useTransform(springY, [0, 1000], [60, -60]);

  useEffect(() => {
    const handleMouseMove = (e) => {
      mouseX.set(e.clientX);
      mouseY.set(e.clientY);
    };
    window.addEventListener('mousemove', handleMouseMove);
    return () => window.removeEventListener('mousemove', handleMouseMove);
  }, [mouseX, mouseY]);

  // Real-time validation
  const validateField = (name, value) => {
    const errors = {};
    
    if (name === 'username' && !isLogin) {
      if (value.length < 3) errors.username = 'Username must be at least 3 characters';
      else if (value.length > 30) errors.username = 'Username cannot exceed 30 characters';
      else if (!/^[a-zA-Z0-9_]+$/.test(value)) errors.username = 'Only letters, numbers, and underscores allowed';
    }
    
    if (name === 'password') {
      if (value.length === 0) errors.password = '';
      else if (value.length < 6) errors.password = 'Password must be at least 6 characters';
      else if (!isLogin && !/(?=.*[a-z])(?=.*[A-Z])(?=.*\d)/.test(value)) {
        errors.password = 'Include uppercase, lowercase, and number';
      }
    }
    
    if (name === 'email' && !isLogin && value) {
      if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value)) errors.email = 'Invalid email format';
    }
    
    if (name === 'fullName' && !isLogin && value.length > 0 && value.length < 2) {
      errors.fullName = 'Name is too short';
    }
    
    return errors;
  };

  const handleFieldChange = (name, value) => {
    setFormData({ ...formData, [name]: value });
    if (touched[name]) {
      const errors = validateField(name, value);
      setFieldErrors(prev => ({ ...prev, ...errors, [name]: errors[name] || null }));
    }
    setError('');
    setSuccess('');
  };

  const handleBlur = (name) => {
    setTouched(prev => ({ ...prev, [name]: true }));
    const errors = validateField(name, formData[name]);
    setFieldErrors(prev => ({ ...prev, ...errors }));
  };

  const getPasswordStrength = (password) => {
    if (!password) return { level: 0, label: '', color: '' };
    let strength = 0;
    if (password.length >= 8) strength++;
    if (password.length >= 12) strength++;
    if (/[a-z]/.test(password)) strength++;
    if (/[A-Z]/.test(password)) strength++;
    if (/\d/.test(password)) strength++;
    if (/[^a-zA-Z\d]/.test(password)) strength++;
    
    if (strength <= 2) return { level: 1, label: 'Weak', color: '#ef4444' };
    if (strength <= 4) return { level: 2, label: 'Fair', color: '#f59e0b' };
    if (strength <= 5) return { level: 3, label: 'Good', color: '#10b981' };
    return { level: 4, label: 'Strong', color: '#059669' };
  };

  const passwordStrength = !isLogin ? getPasswordStrength(formData.password) : null;

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSuccess('');
    
    // Mark all fields as touched
    const allFields = isLogin 
      ? ['username', 'password'] 
      : ['username', 'password', 'email', 'fullName'];
    const newTouched = {};
    allFields.forEach(field => newTouched[field] = true);
    setTouched(newTouched);

    // Validate all fields
    let allErrors = {};
    allFields.forEach(field => {
      const errors = validateField(field, formData[field]);
      allErrors = { ...allErrors, ...errors };
    });
    
    if (Object.keys(allErrors).filter(key => allErrors[key]).length > 0) {
      setFieldErrors(allErrors);
      setError('Please fix the errors above');
      return;
    }

    setLoading(true);
    try {
      if (isLogin) {
        const res = await authService.login(formData.username, formData.password);
        const { access_token } = res.data;
        localStorage.setItem('spectra_token', access_token);
        localStorage.setItem('spectra_user', formData.username);
        
        setSuccess('✨ Login successful! Redirecting...');
        setTimeout(() => {
          onLogin(formData.username);
          navigate('/create');
        }, 1200);
      } else {
        await authService.signup(
          formData.username, 
          formData.password, 
          formData.email, 
          formData.fullName, 
          formData.companyId
        );
        setSuccess('✅ Account created successfully! Please login.');
        setIsLogin(true);
        setFormData({ username: formData.username, password: '', email: '', fullName: '', companyId: '' });
        setFieldErrors({});
        setTouched({});
      }
    } catch (err) {
      console.error('Auth error:', err);
      
      if (!err.response) {
        // Network error
        setError('🌐 Network error. Please check your connection and try again.');
      } else if (err.response.status === 500) {
        setError('⚠️ Server error. Please try again in a moment.');
      } else if (err.response.status === 503) {
        setError('🔧 Service temporarily unavailable. Please try again later.');
      } else if (err.response.status === 429) {
        setError('⏱️ Too many attempts. Please wait a moment before trying again.');
      } else {
        // Show backend validation message
        const backendError = err.response?.data?.detail || err.response?.data?.message;
        setError(backendError || '❌ Authentication failed. Please try again.');
      }
    } finally {
      setLoading(false);
    }
  };

  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: { staggerChildren: 0.1, delayChildren: 0.3 }
    }
  };

  const itemVariants = {
    hidden: { opacity: 0, y: 20 },
    visible: { opacity: 1, y: 0, transition: { duration: 0.5, ease: "easeOut" } }
  };

  return (
    <div className="auth-page-container">
      {/* Navbar */}
      <motion.nav 
        className="auth-navbar"
        initial={{ y: -20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ duration: 0.6 }}
      >
        <div className="auth-nav-content">
          <div className="nav-logo-section" onClick={() => navigate('/')}>
            <Zap className="nav-logo-icon" size={28} />
            <h1 className="nav-logo-text">SPECTRA</h1>
          </div>
          <button className="nav-home-btn" onClick={() => navigate('/')}>
            <Home size={18} />
            <span>Home</span>
          </button>
        </div>
      </motion.nav>

      <motion.div
        className="cursor-glow"
        style={{
          x: springX,
          y: springY,
          transform: 'translate(-50%, -50%)'
        }}
      />

      <motion.div
        className="auth-form-section"
        initial={{ opacity: 0, x: -50 }}
        animate={{ opacity: 1, x: 0 }}
        transition={{ duration: 1, ease: "easeOut" }}
      >
        {/* Floating gradient blobs for form section */}
        <div className="form-blobs">
          <motion.div 
            className="form-blob form-blob-1"
            animate={{
              x: [0, 30, 0],
              y: [0, -40, 0],
              scale: [1, 1.1, 1],
            }}
            transition={{
              duration: 8,
              repeat: Infinity,
              ease: "easeInOut"
            }}
          />
          <motion.div 
            className="form-blob form-blob-2"
            animate={{
              x: [0, -30, 0],
              y: [0, 40, 0],
              scale: [1, 1.15, 1],
            }}
            transition={{
              duration: 10,
              repeat: Infinity,
              ease: "easeInOut"
            }}
          />
        </div>
        
        <motion.div
          className="auth-card glass"
          variants={containerVariants}
          initial="hidden"
          animate="visible"
        >
          <motion.div className="auth-header" variants={itemVariants}>
            <motion.div
              className="logo-icon-container"
              whileHover={{ scale: 1.1, rotate: 10 }}
              whileTap={{ scale: 0.9 }}
            >
              <Sparkles className="logo-sparkle" size={32} />
            </motion.div>
            <h2>{isLogin ? 'Welcome Back' : 'Create Account'}</h2>
            <p className="subtitle">{isLogin ? 'Login to continue your ad journey' : 'Join thousands of creators'}</p>
          </motion.div>

          <form onSubmit={handleSubmit} className="auth-form">
            <AnimatePresence mode="wait">
              {!isLogin && (
                <motion.div
                  key="signup-fields"
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: 'auto' }}
                  exit={{ opacity: 0, height: 0 }}
                  transition={{ duration: 0.3 }}
                >
                  <div className={`input-group-glass ${fieldErrors.fullName ? 'error' : ''} ${touched.fullName && !fieldErrors.fullName && formData.fullName ? 'valid' : ''}`}>
                    <User size={18} className="input-icon" />
                    <input
                      type="text"
                      placeholder="Full Name"
                      value={formData.fullName}
                      onChange={e => handleFieldChange('fullName', e.target.value)}
                      onBlur={() => handleBlur('fullName')}
                      required
                    />
                    {touched.fullName && !fieldErrors.fullName && formData.fullName && (
                      <CheckCircle2 size={18} className="validation-icon success" />
                    )}
                  </div>
                  {fieldErrors.fullName && touched.fullName && (
                    <div className="field-error"><AlertCircle size={14} /> {fieldErrors.fullName}</div>
                  )}

                  <div className={`input-group-glass ${fieldErrors.email ? 'error' : ''} ${touched.email && !fieldErrors.email && formData.email ? 'valid' : ''}`}>
                    <Mail size={18} className="input-icon" />
                    <input
                      type="email"
                      placeholder="Email Address"
                      value={formData.email}
                      onChange={e => handleFieldChange('email', e.target.value)}
                      onBlur={() => handleBlur('email')}
                      required
                    />
                    {touched.email && !fieldErrors.email && formData.email && (
                      <CheckCircle2 size={18} className="validation-icon success" />
                    )}
                  </div>
                  {fieldErrors.email && touched.email && (
                    <div className="field-error"><AlertCircle size={14} /> {fieldErrors.email}</div>
                  )}

                  <div className="input-group-glass">
                    <Building2 size={18} className="input-icon" />
                    <input
                      type="text"
                      placeholder="Company / Brand Name (Optional)"
                      value={formData.companyId}
                      onChange={e => handleFieldChange('companyId', e.target.value)}
                    />
                  </div>
                </motion.div>
              )}
            </AnimatePresence>

            <motion.div className={`input-group-glass ${fieldErrors.username ? 'error' : ''} ${touched.username && !fieldErrors.username && formData.username ? 'valid' : ''}`} variants={itemVariants}>
              <User size={18} className="input-icon" />
              <input
                type="text"
                placeholder="Username"
                value={formData.username}
                onChange={e => handleFieldChange('username', e.target.value)}
                onBlur={() => handleBlur('username')}
                required
              />
              {touched.username && !fieldErrors.username && formData.username && (
                <CheckCircle2 size={18} className="validation-icon success" />
              )}
            </motion.div>
            {fieldErrors.username && touched.username && (
              <div className="field-error"><AlertCircle size={14} /> {fieldErrors.username}</div>
            )}

            <motion.div className={`input-group-glass ${fieldErrors.password ? 'error' : ''} ${touched.password && !fieldErrors.password && formData.password ? 'valid' : ''}`} variants={itemVariants}>
              <Lock size={18} className="input-icon" />
              <input
                type={showPassword ? 'text' : 'password'}
                placeholder="Password"
                value={formData.password}
                onChange={e => handleFieldChange('password', e.target.value)}
                onBlur={() => handleBlur('password')}
                required
              />
              <button
                type="button"
                className="password-toggle"
                onClick={() => setShowPassword(!showPassword)}
                aria-label={showPassword ? 'Hide password' : 'Show password'}
              >
                {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
              </button>
            </motion.div>
            {fieldErrors.password && touched.password && (
              <div className="field-error"><AlertCircle size={14} /> {fieldErrors.password}</div>
            )}
            
            {!isLogin && formData.password && passwordStrength && (
              <motion.div 
                className="password-strength"
                initial={{ opacity: 0, y: -10 }}
                animate={{ opacity: 1, y: 0 }}
              >
                <div className="strength-bar-container">
                  <motion.div 
                    className="strength-bar"
                    style={{ background: passwordStrength.color }}
                    initial={{ width: 0 }}
                    animate={{ width: `${(passwordStrength.level / 4) * 100}%` }}
                    transition={{ duration: 0.3 }}
                  />
                </div>
                <span className="strength-label" style={{ color: passwordStrength.color }}>
                  {passwordStrength.label}
                </span>
              </motion.div>
            )}

            <AnimatePresence mode="wait">
              {error && (
                <motion.div 
                  className="error-msg"
                  initial={{ opacity: 0, y: -10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -10 }}
                >
                  <XCircle size={18} />
                  <span>{error}</span>
                </motion.div>
              )}
              
              {success && (
                <motion.div 
                  className="success-msg"
                  initial={{ opacity: 0, y: -10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -10 }}
                >
                  <CheckCircle2 size={18} />
                  <span>{success}</span>
                </motion.div>
              )}
            </AnimatePresence>

            <motion.button
              type="submit"
              className="btn btn-primary w-full"
              disabled={loading}
              variants={itemVariants}
              whileHover={!loading ? { scale: 1.02, boxShadow: '0 15px 40px rgba(99, 102, 241, 0.35)' } : {}}
              whileTap={!loading ? { scale: 0.98 } : {}}
            >
              {loading ? (
                <>
                  <motion.div 
                    className="spinner"
                    animate={{ rotate: 360 }}
                    transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
                  />
                  Processing...
                </>
              ) : (
                <>
                  {isLogin ? 'Login' : 'Create Account'} <ArrowRight size={18} />
                </>
              )}
            </motion.button>
          </form>

          <motion.div className="auth-footer" variants={itemVariants}>
            <button className="toggle-btn" onClick={() => setIsLogin(!isLogin)}>
              {isLogin ? "Don't have an account? Sign Up" : "Already have an account? Login"}
            </button>
          </motion.div>
        </motion.div>
      </motion.div>

      <div className="brand-section">
        <div className="brand-content">
          <motion.h1
            className="brand-title"
            style={{ x: textX, y: textY }}
          >
            {["S", "P", "E", "C", "T", "R", "A"].map((letter, index) => (
              <motion.span
                key={index}
                initial={{ opacity: 0, scale: 0, rotateY: -90 }}
                animate={{
                  opacity: 1,
                  scale: 1,
                  rotateY: 0,
                  transition: { delay: index * 0.12, duration: 1, type: "spring" }
                }}
                whileHover={{
                  scale: 1.2,
                  color: "#818cf8",
                  filter: "drop-shadow(0 0 20px rgba(99, 102, 241, 0.6))",
                  rotateZ: [-5, 5, -5, 0],
                  transition: { duration: 0.3 }
                }}
              >
                {letter}
              </motion.span>
            ))}
          </motion.h1>
          <motion.div
            className="brand-pill"
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 1, duration: 1 }}
            whileHover={{ letterSpacing: "5px", background: "rgba(255,255,255,0.08)" }}
          >
            Next-Gen AI Advertising
          </motion.div>

          <div className="animated-blobs">
            <motion.div className="blob blob-1" style={{ x: blob1X, y: blob1Y }}></motion.div>
            <motion.div className="blob blob-2" style={{ x: blob2X, y: blob2Y }}></motion.div>
            <div className="blob blob-3"></div>
          </div>

          {/* Particle System */}
          {[...Array(6)].map((_, i) => (
            <motion.div
              key={i}
              className="particle"
              animate={{
                y: [0, -100, 0],
                opacity: [0, 0.5, 0],
                x: [0, (i % 2 === 0 ? 50 : -50), 0]
              }}
              transition={{
                duration: 4 + i,
                repeat: Infinity,
                delay: i * 0.5,
              }}
              style={{
                left: `${15 + (i * 15)}%`,
                top: `${20 + (i * 10)}%`,
              }}
            />
          ))}
        </div>
      </div>

      <style>{`
        .auth-page-container {
          display: flex;
          width: 100vw;
          height: 100vh;
          overflow: hidden;
          background: linear-gradient(135deg, #0a0a0a 0%, #1a0f2e 20%, #0f0a1a 50%, #1a0a1e 80%, #0a0a0a 100%);
          position: relative;
        }

        /* Navbar Styles */
        .auth-navbar {
          position: fixed;
          top: 0;
          left: 0;
          right: 0;
          z-index: 200;
          padding: 16px 0;
          backdrop-filter: blur(24px);
          background: linear-gradient(180deg, rgba(10, 10, 31, 0.95) 0%, rgba(10, 10, 31, 0.85) 100%);
          border-bottom: 1px solid rgba(99,102,241,0.2);
          box-shadow: 0 4px 32px rgba(0, 0, 0, 0.4), 0 0 40px rgba(99,102,241,0.05);
        }

        .auth-nav-content {
          max-width: 1400px;
          margin: 0 auto;
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 0 40px;
        }

        .nav-logo-section {
          display: flex;
          align-items: center;
          gap: 10px;
          cursor: pointer;
          transition: transform 0.3s ease;
        }

        .nav-logo-section:hover {
          transform: scale(1.05);
        }

        .nav-logo-icon {
          color: #818cf8;
          filter: drop-shadow(0 0 12px rgba(129, 140, 248, 0.5));
        }

        .nav-logo-text {
          font-size: 1.5rem;
          font-weight: 900;
          letter-spacing: -1px;
          background: linear-gradient(135deg, #ffffff 0%, #c7d2fe 50%, #8b5cf6 100%);
          -webkit-background-clip: text;
          -webkit-text-fill-color: transparent;
          margin: 0;
          filter: drop-shadow(0 0 8px rgba(129, 140, 248, 0.3));
        }

        .nav-home-btn {
          display: flex;
          align-items: center;
          gap: 8px;
          background: rgba(255, 255, 255, 0.03);
          backdrop-filter: blur(12px);
          border: 1px solid rgba(255, 255, 255, 0.15);
          color: white;
          padding: 10px 20px;
          border-radius: 10px;
          font-weight: 600;
          cursor: pointer;
          transition: all 0.3s cubic-bezier(0.16,1,0.3,1);
          font-size: 0.95rem;
        }

        .nav-home-btn:hover {
          background: rgba(255, 255, 255, 0.08);
          border-color: rgba(99, 102, 241, 0.5);
          transform: translateY(-2px);
          box-shadow: 0 6px 20px rgba(99, 102, 241, 0.3);
        }

        .cursor-glow {
          position: fixed;
          width: 900px;
          height: 900px;
          background: radial-gradient(circle, rgba(99, 102, 241, 0.09) 0%, rgba(139, 92, 246, 0.05) 40%, transparent 70%);
          pointer-events: none;
          z-index: 0;
        }

        .auth-form-section {
          flex: 1;
          display: flex;
          align-items: center;
          justify-content: center;
          padding: 40px;
          z-index: 10;
        }

        .auth-card {
          width: 440px;
          padding: 40px 36px;
          border-radius: 32px;
          backdrop-filter: blur(40px);
          background: linear-gradient(145deg, rgba(30,27,75,0.8) 0%, rgba(15,15,35,0.9) 100%);
          border: 1px solid rgba(99,102,241,0.3);
          box-shadow: 0 24px 80px rgba(0, 0, 0, 0.7), 0 0 80px rgba(99, 102, 241, 0.15), 0 0 120px rgba(139, 92, 246, 0.08);
          max-height: 90vh;
          overflow-y: auto;
          position: relative;
        }
        .auth-card::before {
          content: '';
          position: absolute;
          inset: 0;
          border-radius: 32px;
          padding: 1.5px;
          background: linear-gradient(135deg, #6366f1, rgba(139,92,246,0.5), #ec4899, rgba(99,102,241,0.3));
          -webkit-mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0);
          -webkit-mask-composite: xor;
          mask-composite: exclude;
          pointer-events: none;
          opacity: 0.6;
          transition: opacity 0.3s;
        }
        .auth-card:hover::before {
          opacity: 1;
        }

        .auth-card::-webkit-scrollbar {
          width: 4px;
        }
        .auth-card::-webkit-scrollbar-thumb {
          background: rgba(99, 102, 241, 0.3);
          border-radius: 4px;
        }

        .brand-section {
          flex: 1.2;
          position: relative;
          display: flex;
          align-items: center;
          justify-content: center;
          background: linear-gradient(135deg, #0a0a1f 0%, #1e1b4b 30%, #312e81 60%, #1a0a2e 100%);
          overflow: hidden;
          perspective: 1200px;
        }

        .brand-content {
          text-align: center;
          position: relative;
          z-index: 5;
        }

        .brand-title {
          font-size: 8.5rem;
          font-weight: 900;
          letter-spacing: -3px;
          margin: 0 40px;
          display: flex;
          flex-wrap: nowrap;
          justify-content: center;
          gap: 10px;
          color: white;
          max-width: 80%;
        }

        .brand-title span {
          display: inline-block;
          background: linear-gradient(to bottom, #ffffff 40%, #6366f1 100%);
          -webkit-background-clip: text;
          -webkit-text-fill-color: transparent;
          filter: drop-shadow(0 0 20px rgba(99, 102, 241, 0.1));
          cursor: default;
        }

        .brand-pill {
          display: inline-block;
          margin-top: 24px;
          background: linear-gradient(135deg, rgba(99,102,241,0.15) 0%, rgba(168,85,247,0.1) 100%);
          border: 1px solid rgba(99,102,241,0.3);
          padding: 12px 36px;
          border-radius: 40px;
          color: #a5b4fc;
          font-weight: 600;
          letter-spacing: 3px;
          text-transform: uppercase;
          font-size: 0.85rem;
          backdrop-filter: blur(10px);
          transition: all 0.5s cubic-bezier(0.16, 1, 0.3, 1);
          box-shadow: 0 4px 20px rgba(99,102,241,0.15);
        }

        .animated-blobs {
          position: absolute;
          top: 0;
          left: 0;
          width: 100%;
          height: 100%;
          z-index: -1;
        }

        .blob {
          position: absolute;
          width: 500px;
          height: 500px;
          border-radius: 50%;
          filter: blur(120px);
          opacity: 0.25;
        }

        .blob-1 { background: linear-gradient(135deg, #6366f1, #8b5cf6); top: -100px; right: -100px; }
        .blob-2 { background: linear-gradient(135deg, #4f46e5, #ec4899); bottom: -150px; left: -100px; }
        .blob-3 { background: linear-gradient(135deg, #818cf8, #c084fc); top: 30%; left: 20%; width: 300px; height: 300px; opacity: 0.2; }

        .form-blobs {
          position: absolute;
          width: 100%;
          height: 100%;
          pointer-events: none;
          z-index: 1;
          overflow: hidden;
        }

        .form-blob {
          position: absolute;
          border-radius: 50%;
          filter: blur(100px);
        }

        .form-blob-1 {
          width: 400px;
          height: 400px;
          background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
          top: 10%;
          left: -10%;
          opacity: 0.2;
        }

        .form-blob-2 {
          width: 350px;
          height: 350px;
          background: linear-gradient(135deg, #ec4899 0%, #8b5cf6 100%);
          bottom: 10%;
          right: -10%;
          opacity: 0.18;
        }

        .particle {
            position: absolute;
            width: 4px;
            height: 4px;
            background: rgba(99, 102, 241, 0.4);
            border-radius: 50%;
            filter: blur(1px);
        }

        .auth-header h2 {
          font-size: 2.8rem;
          margin: 24px 0 8px;
          font-weight: 800;
          letter-spacing: -1.5px;
          background: linear-gradient(135deg, #ffffff 0%, #e0e7ff 40%, #c4b5fd 100%);
          -webkit-background-clip: text;
          -webkit-text-fill-color: transparent;
          background-clip: text;
        }

        .subtitle {
          color: rgba(255, 255, 255, 0.4);
          margin-bottom: 40px;
          font-size: 1.1rem;
        }

        .auth-form {
          display: flex;
          flex-direction: column;
          gap: 14px;
        }

        .input-group-glass {
          background: rgba(255, 255, 255, 0.04);
          backdrop-filter: blur(12px);
          border: 1px solid rgba(255, 255, 255, 0.08);
          border-radius: 16px;
          display: flex;
          align-items: center;
          padding: 15px 18px;
          gap: 14px;
          transition: all 0.4s cubic-bezier(0.16, 1, 0.3, 1);
          position: relative;
          margin-bottom: 8px;
        }

        .input-group-glass.error {
          border-color: rgba(239, 68, 68, 0.5);
          background: rgba(239, 68, 68, 0.03);
        }

        .input-group-glass.valid {
          border-color: rgba(16, 185, 129, 0.3);
          background: rgba(16, 185, 129, 0.02);
        }

        .input-group-glass:focus-within {
          border-color: rgba(99, 102, 241, 0.7);
          background: rgba(99, 102, 241, 0.08);
          box-shadow: 0 0 0 4px rgba(99, 102, 241, 0.2), 0 8px 32px rgba(99, 102, 241, 0.15);
          transform: translateY(-2px);
        }

        .input-group-glass.error:focus-within {
          border-color: rgba(239, 68, 68, 0.5);
          background: rgba(239, 68, 68, 0.03);
          box-shadow: 0 0 0 3px rgba(239, 68, 68, 0.08);
        }

        .input-icon {
          color: rgba(255, 255, 255, 0.3);
          flex-shrink: 0;
          transition: color 0.3s;
        }

        .input-group-glass:focus-within .input-icon {
          color: #818cf8;
        }

        .input-group-glass.error .input-icon {
          color: #ef4444;
        }

        .input-group-glass.valid .input-icon {
          color: #10b981;
        }

        .validation-icon {
          flex-shrink: 0;
          transition: all 0.3s;
        }

        .validation-icon.success {
          color: #10b981;
        }

        .input-group-glass input {
          background: transparent;
          border: none;
          color: white;
          outline: none;
          width: 100%;
          font-size: 1.02rem;
          transition: all 0.3s;
          box-shadow: none;
          -webkit-appearance: none;
          -moz-appearance: none;
          appearance: none;
        }

        .input-group-glass input:focus {
          outline: none;
          box-shadow: none;
          border: none;
        }

        .input-group-glass input:-webkit-autofill,
        .input-group-glass input:-webkit-autofill:hover,
        .input-group-glass input:-webkit-autofill:focus {
          -webkit-text-fill-color: white;
          -webkit-box-shadow: 0 0 0 1000px transparent inset;
          box-shadow: 0 0 0 1000px transparent inset;
          transition: background-color 5000s ease-in-out 0s;
        }

        .input-group-glass input::placeholder {
          color: rgba(255, 255, 255, 0.25);
        }

        .password-toggle {
          background: transparent;
          border: none;
          color: rgba(255, 255, 255, 0.3);
          cursor: pointer;
          padding: 4px;
          display: flex;
          align-items: center;
          transition: all 0.3s;
          flex-shrink: 0;
        }

        .password-toggle:hover {
          color: #6366f1;
          transform: scale(1.1);
        }

        .field-error {
          color: #fca5a5;
          font-size: 0.875rem;
          display: flex;
          align-items: center;
          gap: 6px;
          margin: -4px 0 10px 4px;
          animation: shake 0.3s;
        }

        @keyframes shake {
          0%, 100% { transform: translateX(0); }
          25% { transform: translateX(-4px); }
          75% { transform: translateX(4px); }
        }

        .password-strength {
          display: flex;
          align-items: center;
          gap: 12px;
          margin-bottom: 6px;
        }

        .strength-bar-container {
          flex: 1;
          height: 4px;
          background: rgba(255, 255, 255, 0.08);
          border-radius: 2px;
          overflow: hidden;
        }

        .strength-bar {
          height: 100%;
          border-radius: 2px;
          transition: all 0.4s cubic-bezier(0.16, 1, 0.3, 1);
        }

        .strength-label {
          font-size: 0.85rem;
          font-weight: 600;
          min-width: 60px;
          text-align: right;
        }

        .btn-primary {
          background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 50%, #ec4899 100%);
          color: white;
          padding: 16px;
          border-radius: 16px;
          font-weight: 700;
          font-size: 1.1rem;
          border: none;
          cursor: pointer;
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 10px;
          transition: all 0.4s cubic-bezier(0.16, 1, 0.3, 1);
          margin-top: 10px;
          box-shadow: 0 8px 24px rgba(99, 102, 241, 0.35), 0 0 40px rgba(139, 92, 246, 0.2);
          position: relative;
          overflow: hidden;
        }

        .btn-primary::before {
          content: '';
          position: absolute;
          top: 0;
          left: -100%;
          width: 100%;
          height: 100%;
          background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.1), transparent);
          transition: left 0.6s;
        }

        .btn-primary:hover::before {
          left: 100%;
        }

        .btn-primary:disabled {
          opacity: 0.6;
          cursor: not-allowed;
          transform: none;
        }

        .btn-primary:active:not(:disabled) { 
          transform: scale(0.98); 
        }

        .spinner {
          width: 18px;
          height: 18px;
          border: 2px solid rgba(255, 255, 255, 0.3);
          border-top-color: white;
          border-radius: 50%;
          animation: spin 0.6s linear infinite;
        }

        @keyframes spin {
          to { transform: rotate(360deg); }
        }

        .error-msg {
          color: #fca5a5;
          font-size: 0.98rem;
          background: rgba(239, 68, 68, 0.08);
          padding: 14px 16px;
          border-radius: 12px;
          border: 1px solid rgba(239, 68, 68, 0.15);
          display: flex;
          align-items: center;
          gap: 10px;
          font-weight: 500;
        }

        .success-msg {
          color: #86efac;
          font-size: 0.98rem;
          background: rgba(16, 185, 129, 0.08);
          padding: 14px 16px;
          border-radius: 12px;
          border: 1px solid rgba(16, 185, 129, 0.15);
          display: flex;
          align-items: center;
          gap: 10px;
          font-weight: 500;
        }

        .toggle-btn {
          background: transparent;
          border: none;
          color: rgba(255, 255, 255, 0.4);
          font-size: 1rem;
          cursor: pointer;
          font-weight: 500;
          transition: all 0.3s;
        }

        .toggle-btn:hover {
          color: #818cf8;
        }

        .logo-icon-container {
          width: 80px;
          height: 80px;
          background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 50%, #a855f7 100%);
          border-radius: 24px;
          display: flex;
          align-items: center;
          justify-content: center;
          margin: 0 auto;
          box-shadow: 0 15px 50px rgba(99, 102, 241, 0.5), 0 0 80px rgba(139, 92, 246, 0.3);
          border: 2px solid rgba(255, 255, 255, 0.15);
          animation: logo-pulse 3s ease-in-out infinite;
        }

        @keyframes logo-pulse {
          0%, 100% { box-shadow: 0 15px 50px rgba(99, 102, 241, 0.5), 0 0 80px rgba(139, 92, 246, 0.3); }
          50% { box-shadow: 0 15px 60px rgba(99, 102, 241, 0.7), 0 0 100px rgba(139, 92, 246, 0.5); }
        }

        @media (max-width: 1024px) {
          .brand-section { display: none; }
          .auth-form-section { flex: 1; overflow-y: auto; }
          .auth-card { width: 100%; max-width: 440px; }
        }
      `}</style>
    </div>
  );
}

export default AuthPage;
