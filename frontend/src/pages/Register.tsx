// src/pages/Register.tsx
import { useState } from 'react';
import { api } from '../lib/api';
import { useNavigate, Link } from 'react-router-dom';

export default function Register() {
  const nav = useNavigate();
  const [form, setForm] = useState({ username: '', email: '', password: '' });
  const [msg, setMsg] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const submit = async () => {
    if (!form.username || !form.password) {
      setMsg('Username and password are required'); return;
    }
    setLoading(true); setMsg(null);
    try {
      await api('/users/register/', {
        method: 'POST',
        body: JSON.stringify(form),
      });
      setMsg('Registration successful — please login.');
      setTimeout(() => nav('/login'), 700);
    } catch (e:any) {
      setMsg(e.message);
    } finally { setLoading(false); }
  };

  return (
    <div className="grid min-h-screen place-items-center bg-gray-50 p-6">
      <div className="w-full max-w-md rounded-2xl bg-white p-6 shadow">
        <h1 className="mb-4 text-2xl font-semibold">Create account</h1>
        <input className="mb-2 w-full rounded border p-2" placeholder="Username"
               value={form.username} onChange={e=>setForm(f=>({...f,username:e.target.value}))}/>
        <input className="mb-2 w-full rounded border p-2" placeholder="Email"
               value={form.email} onChange={e=>setForm(f=>({...f,email:e.target.value}))}/>
        <input className="mb-4 w-full rounded border p-2" type="password" placeholder="Password"
               value={form.password} onChange={e=>setForm(f=>({...f,password:e.target.value}))}/>
        <button className="w-full rounded bg-indigo-600 p-2 text-white disabled:opacity-60"
                onClick={submit} disabled={loading}>{loading?'Creating...':'Register'}</button>
        {msg && <p className="mt-3 text-sm text-gray-600">{msg}</p>}
        <p className="mt-3 text-sm"><Link to="/login" className="text-indigo-600">Back to login</Link></p>
      </div>
    </div>
  );
}
