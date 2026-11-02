
import React, { useState } from "react";
import { Link } from "react-router-dom";
import { Eye, EyeOff, Wallet, ArrowRight } from "lucide-react";

export default function Register() {
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);
  const [form, setForm] = useState({
    name: "",
    email: "",
    accountType: "Individual",
    password: "",
    confirmPassword: "",
    terms: false
  });
  const [error, setError] = useState("");

  function update(field, value) {
    setForm(prev => ({ ...prev, [field]: value }));
  }

  function handleSubmit(e) {
    e.preventDefault();
    setError("");

    if (form.password.length < 8) {
      setError("Password must contain at least 8 characters.");
      return;
    }

    if (form.password !== form.confirmPassword) {
      setError("Passwords do not match.");
      return;
    }

    if (!form.terms) {
      setError("Please accept the terms and conditions.");
      return;
    }

    alert("Registration API will be connected when the backend is ready.");
  }

  return (
    <div className="auth-page">
      <div className="auth-brand-panel">
        <div className="auth-brand">
          <span className="auth-logo"><Wallet size={23}/></span>
          <span>FinSight <b>AI</b></span>
        </div>
        <div className="auth-brand-content">
          <span className="auth-kicker">YOUR FINANCIAL JOURNEY STARTS HERE</span>
          <h1>Take control of your financial tomorrow.</h1>
          <p>Create your account to organize financial activity and prepare for what's ahead.</p>
          <div className="auth-feature"><span>✓</span> Track income and expenses</div>
          <div className="auth-feature"><span>✓</span> Plan budgets and commitments</div>
          <div className="auth-feature"><span>✓</span> Identify potential financial risks</div>
        </div>
        <small className="auth-copyright">© 2026 FinSight AI. All rights reserved.</small>
      </div>

      <div className="auth-form-panel">
        <div className="auth-form-container register-container">
          <div className="auth-mobile-brand">
            <Wallet size={22}/> FinSight <b>AI</b>
          </div>
          <span className="auth-kicker">GET STARTED</span>
          <h2>Create your account</h2>
          <p className="auth-subtitle">Fill in your details to get started with FinSight AI.</p>

          <form onSubmit={handleSubmit} className="auth-form">
            <label htmlFor="register-name">Full name</label>
            <input
              id="register-name"
              type="text"
              placeholder="Enter your full name"
              value={form.name}
              onChange={e => update("name", e.target.value)}
              required
            />

            <label htmlFor="register-email">Email address</label>
            <input
              id="register-email"
              type="email"
              placeholder="you@example.com"
              value={form.email}
              onChange={e => update("email", e.target.value)}
              required
            />

            <label htmlFor="account-type">Account type</label>
            <select
              id="account-type"
              value={form.accountType}
              onChange={e => update("accountType", e.target.value)}
            >
              <option>Individual</option>
              <option>Small Business</option>
            </select>

            <label htmlFor="register-password">Password</label>
            <div className="auth-password-input">
              <input
                id="register-password"
                type={showPassword ? "text" : "password"}
                placeholder="At least 8 characters"
                value={form.password}
                onChange={e => update("password", e.target.value)}
                required
              />
              <button type="button" onClick={() => setShowPassword(!showPassword)} aria-label="Toggle password visibility">
                {showPassword ? <EyeOff size={18}/> : <Eye size={18}/>}
              </button>
            </div>

            <label htmlFor="confirm-password">Confirm password</label>
            <div className="auth-password-input">
              <input
                id="confirm-password"
                type={showConfirm ? "text" : "password"}
                placeholder="Re-enter your password"
                value={form.confirmPassword}
                onChange={e => update("confirmPassword", e.target.value)}
                required
              />
              <button type="button" onClick={() => setShowConfirm(!showConfirm)} aria-label="Toggle confirm password visibility">
                {showConfirm ? <EyeOff size={18}/> : <Eye size={18}/>}
              </button>
            </div>

            <label className="auth-remember">
              <input
                type="checkbox"
                checked={form.terms}
                onChange={e => update("terms", e.target.checked)}
              />
              I agree to the terms and conditions.
            </label>

            {error && <p className="auth-error">{error}</p>}

            <button className="auth-submit" type="submit">
              Create account <ArrowRight size={17}/>
            </button>
          </form>

          <p className="auth-switch">
            Already have an account? <Link to="/login">Sign in</Link>
          </p>
        </div>
      </div>
    </div>
  );
}
