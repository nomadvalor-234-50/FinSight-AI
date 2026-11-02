
import React, { useState } from "react";
import {
  User, Bell, Shield, Database,
  Brain, Save, Settings as SettingsIcon
} from "lucide-react";

export default function Settings() {
  const [profile, setProfile] = useState({
    name: "",
    email: "",
    currency: "INR",
    businessType: "Individual"
  });

  const [notifications, setNotifications] = useState({
    lowBalance: true,
    recurringPayments: true,
    overspending: true,
    forecastUpdates: true
  });

  const [preferences, setPreferences] = useState({
    aiInsights: true,
    explainableInsights: true
  });

  const toggleNotification = key => {
    setNotifications(prev => ({ ...prev, [key]: !prev[key] }));
  };

  const togglePreference = key => {
    setPreferences(prev => ({ ...prev, [key]: !prev[key] }));
  };

  return (
    <div className="remaining-page">
      <div className="remaining-header">
        <div>
          <span className="remaining-eyebrow">PREFERENCES / CONFIGURATION</span>
          <h1>Settings</h1>
          <p>Manage your profile, notification preferences and application settings.</p>
        </div>
      </div>

      <div className="remaining-banner">
        <InfoIcon />
        <div>
          <strong>Local settings preview</strong>
          <p>These preferences currently exist only in this page's browser state. Profile and notification settings will be saved permanently after backend integration.</p>
        </div>
      </div>

      <div className="settings-layout">
        <section className="remaining-panel">
          <h3><User size={19}/> Profile Information</h3>
          <div className="settings-form">
            <label>Full name</label>
            <input
              placeholder="Enter your name"
              value={profile.name}
              onChange={e => setProfile({...profile, name: e.target.value})}
            />

            <label>Email address</label>
            <input
              type="email"
              placeholder="Enter your email"
              value={profile.email}
              onChange={e => setProfile({...profile, email: e.target.value})}
            />

            <label>Account type</label>
            <select
              value={profile.businessType}
              onChange={e => setProfile({...profile, businessType: e.target.value})}
            >
              <option>Individual</option>
              <option>Small Business</option>
            </select>

            <label>Preferred currency</label>
            <select
              value={profile.currency}
              onChange={e => setProfile({...profile, currency: e.target.value})}
            >
              <option value="INR">INR - Indian Rupee</option>
              <option value="USD">USD - US Dollar</option>
              <option value="EUR">EUR - Euro</option>
              <option value="GBP">GBP - British Pound</option>
            </select>
          </div>
        </section>

        <section className="remaining-panel">
          <h3><Bell size={19}/> Notification Preferences</h3>
          <p className="settings-description">Choose which financial notifications you want to receive.</p>

          <SettingToggle label="Low balance warnings" description="Get notified when your balance may fall below a threshold." checked={notifications.lowBalance} onChange={() => toggleNotification("lowBalance")} />
          <SettingToggle label="Recurring payment reminders" description="Receive reminders about upcoming recurring commitments." checked={notifications.recurringPayments} onChange={() => toggleNotification("recurringPayments")} />
          <SettingToggle label="Overspending alerts" description="Get notified when spending exceeds a budget." checked={notifications.overspending} onChange={() => toggleNotification("overspending")} />
          <SettingToggle label="Forecast updates" description="Receive notifications when forecasts are updated." checked={notifications.forecastUpdates} onChange={() => toggleNotification("forecastUpdates")} />
        </section>

        <section className="remaining-panel">
          <h3><Brain size={19}/> AI Preferences</h3>
          <SettingToggle label="AI financial insights" description="Enable AI-generated financial insights when available." checked={preferences.aiInsights} onChange={() => togglePreference("aiInsights")} />
          <SettingToggle label="Explainable recommendations" description="Show reasoning and supporting information with AI suggestions." checked={preferences.explainableInsights} onChange={() => togglePreference("explainableInsights")} />
        </section>

        <section className="remaining-panel">
          <h3><Shield size={19}/> Privacy & Security</h3>
          <div className="settings-info-row">
            <Shield size={20}/>
            <div>
              <strong>Account security</strong>
              <p>Authentication and account security controls will be connected through the backend.</p>
            </div>
          </div>
          <div className="settings-info-row">
            <Database size={20}/>
            <div>
              <strong>Financial data management</strong>
              <p>Secure financial data storage and account connections are not configured yet.</p>
            </div>
          </div>
        </section>
      </div>

      <div className="settings-save-row">
        <span>Changes are temporary until saved through the backend.</span>
        <button className="primary-button" onClick={() => alert("Settings are currently stored only in this page session. Backend saving will be added later.")}>
          <Save size={16}/> Save preferences
        </button>
      </div>
    </div>
  );
}

function SettingToggle({ label, description, checked, onChange }) {
  return (
    <div className="setting-toggle-row">
      <div>
        <strong>{label}</strong>
        <p>{description}</p>
      </div>
      <button
        type="button"
        role="switch"
        aria-checked={checked}
        className={`setting-switch ${checked ? "on" : ""}`}
        onClick={onChange}
      >
        <span />
      </button>
    </div>
  );
}

function InfoIcon() {
  return <SettingsIcon size={20}/>;
}
