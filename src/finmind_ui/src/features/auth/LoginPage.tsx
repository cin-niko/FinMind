import { FormEvent, useState } from "react";
import { AlertTriangle, Eye, EyeOff } from "lucide-react";
import { login } from "../../api/client";
import type { SessionState } from "../../api/client";

type Props = {
  onAuthenticated: (
    session: Extract<SessionState, { authenticated: true }>,
  ) => void;
};

export function LoginPage({ onAuthenticated }: Props) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const usernameId = "login-user-field";
  const passwordId = "login-secret-field";

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
      <div className="loginStage">
        <header className="loginHero">
          <h1>FinMind</h1>
          <p>Personalized finance research assistant.</p>
        </header>
        <form
          aria-describedby="login-context"
          autoComplete="off"
          className="loginPanel"
          onSubmit={handleSubmit}
        >
          <p className="loginContext" id="login-context">
            Sign in to access our product.
          </p>
          {error ? (
            <div className="errorAlert" role="alert">
              <AlertTriangle size={16} /> {error}
            </div>
          ) : null}
          <label htmlFor={usernameId}>
            Username
            <input
              autoComplete="off"
              id={usernameId}
              name="finmind-user"
              placeholder="Enter your email"
              value={username}
              onChange={(event) => setUsername(event.target.value)}
            />
          </label>
          <label htmlFor={passwordId}>
            Password
            <div className="passwordField">
              <input
                autoComplete="new-password"
                id={passwordId}
                name="finmind-secret"
                placeholder="Enter your password"
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                type={showPassword ? "text" : "password"}
              />
              <button
                type="button"
                className="passwordToggle"
                onClick={() => setShowPassword((prev) => !prev)}
                aria-label={
                  showPassword ? "Hide password" : "Show password"
                }
                aria-pressed={showPassword}
              >
                {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
              </button>
            </div>
          </label>
          <button
            className="loginSubmit"
            disabled={loading}
            type="submit"
          >
            {loading ? "Signing in…" : "Continue"}
          </button>
          <p className="loginFootnote">
            Protected access. Authorized internal accounts only.
          </p>
        </form>
      </div>
    </main>
  );
}
