import { FormEvent, useState } from "react";
import { AlertTriangle, Eye, EyeOff } from "lucide-react";
import { login } from "../../api/client";
import type { SessionState } from "../../api/client";
import { useI18n } from "../settings/i18n";

type Props = {
  onAuthenticated: (
    session: Extract<SessionState, { authenticated: true }>,
  ) => void;
};

export function LoginPage({ onAuthenticated }: Props) {
  const { t } = useI18n();
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
    } catch {
      setError(t("loginFailed"));
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="loginShell">
      <div className="loginStage">
        <header className="loginHero">
          <h1>FinMind</h1>
          <p>{t("loginTagline")}</p>
        </header>
        <form
          aria-describedby="login-context"
          autoComplete="off"
          className="loginPanel"
          onSubmit={handleSubmit}
        >
          <p className="loginContext" id="login-context">
            {t("signInContext")}
          </p>
          {error ? (
            <div className="errorAlert" role="alert">
              <AlertTriangle size={16} /> {error}
            </div>
          ) : null}
          <label htmlFor={usernameId}>
            {t("username")}
            <input
              autoComplete="off"
              id={usernameId}
              name="finmind-user"
              placeholder={t("emailPlaceholder")}
              value={username}
              onChange={(event) => setUsername(event.target.value)}
            />
          </label>
          <label htmlFor={passwordId}>
            {t("password")}
            <div className="passwordField">
              <input
                autoComplete="new-password"
                id={passwordId}
                name="finmind-secret"
                placeholder={t("passwordPlaceholder")}
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                type={showPassword ? "text" : "password"}
              />
              <button
                type="button"
                className="passwordToggle"
                onClick={() => setShowPassword((prev) => !prev)}
                aria-label={
                  showPassword ? t("hidePassword") : t("showPassword")
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
            {loading ? t("signingIn") : t("continue")}
          </button>
          <p className="loginFootnote">
            {t("protectedAccess")}
          </p>
        </form>
      </div>
    </main>
  );
}
