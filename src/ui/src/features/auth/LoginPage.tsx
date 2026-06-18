import { FormEvent, useState } from "react";
import { AlertTriangle } from "lucide-react";
import { login } from "../../api/client";
import type { SessionState } from "../../api/client";

type Props = {
  onAuthenticated: (session: Extract<SessionState, { authenticated: true }>) => void;
};

export function LoginPage({ onAuthenticated }: Props) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setLoading(true);
    setError("");
    try {
      const session = await login(username, password);
      if (session.authenticated) {
        onAuthenticated(session);
      }
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Login failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="loginShell">
      <form className="loginPanel" onSubmit={handleSubmit}>
        <div>
          <h1>FinMind</h1>
          <p>Internal analyst access</p>
        </div>
        {error ? (
          <div className="errorAlert" role="alert">
            <AlertTriangle size={16} /> {error}
          </div>
        ) : null}
        <label>
          Username
          <input value={username} onChange={(event) => setUsername(event.target.value)} />
        </label>
        <label>
          Password
          <input
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            type="password"
          />
        </label>
        <button className="primaryButton" disabled={loading} type="submit">
          {loading ? "Signing in" : "Sign in"}
        </button>
      </form>
    </main>
  );
}
