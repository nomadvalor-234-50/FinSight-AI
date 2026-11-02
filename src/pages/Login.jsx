
import React, { useState } from "react";
import { Link } from "react-router-dom";
import { Eye, EyeOff, Wallet, ArrowRight } from "lucide-react";

export default function Login() {
  const [showPassword, setShowPassword] = useState(false);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [remember, setRemember] = useState(false);

  function handleSubmit(e) {
    e.preventDefault();
    alert("Login API will be connected when the backend is ready.");
  }

  return (
    <div className="auth-page">
      <div className="auth-brand-panel">
        <div className="auth-brand">
          <span className="auth-logo"><Wallet size={23}/></span>
          <span>FinSight <b>AI</b></span>
        </div>
        <div className="auth-brand-content">
          <span className="auth-kicker">SMARTER FINANCIAL DECISIONS</span>
          <h1>See your financial future with clarity.</h1>
          <p>Understand your cash flow, prepare for upcoming commitments and make confident financial decisions.</p>
          <div className="auth-feature">
            <span>✓</span> Intelligent cash flow forecasting
          </div>
          <div className="auth-feature">
            <span>✓</span> Early financial risk alerts
          </div>
          <div className="auth-feature">
            <span>✓</span> Explainable AI insights
          </div>
        </div>
        <small className="auth-copyright">© 2026 FinSight AI. All rights reserved.</small>
      </div>

      <div className="auth-form-panel">
        <div className="auth-form-container">
          <div className="auth-mobile-brand">
            <Wallet size={22}/> FinSight <b>AI</b>
          </div>
          <span className="auth-kicker">WELCOME BACK</span>
          <h2>Sign in to your account</h2>
          <p className="auth-subtitle">Enter your details to access your financial dashboard.</p>

          <form onSubmit={handleSubmit} className="auth-form">
            <label htmlFor="login-email">Email address</label>
            <input
              id="login-email"
              type="email"
              placeholder="you@example.com"
              value={email}
              onChange={e => setEmail(e.target.value)}
              required
            />

            <div className="auth-password-heading">
              <label htmlFor="login-password">Password</label>
              <a href="#" onClick={e => {e.preventDefault(); alert("Password reset will be available after backend integration.");}}>Forgot password?</a>
            </div>
            <div className="auth-password-input">
              <input
                id="login-password"
                type={showPassword ? "text" : "password"}
                placeholder="Enter your password"
                value={password}
                onChange={e => setPassword(e.target.value)}
                required
              />
              <button type="button" onClick={() => setShowPassword(!showPassword)} aria-label="Toggle password visibility">
                {showPassword ? <EyeOff size={18}/> : <Eye size={18}/>}
              </button>
            </div>

            <label className="auth-remember">
              <input type="checkbox" checked={remember} onChange={e => setRemember(e.target.checked)}/>
              Remember me
            </label>

            <button className="auth-submit" type="submit">
              Sign in <ArrowRight size={17}/>
            </button>
          </form>

          <p className="auth-switch">
            Don't have an account? <Link to="/register">Create an account</Link>
          </p>
        </div>
      </div>
    </div>
  );
}
