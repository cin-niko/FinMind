import { useI18n } from "../features/settings/i18n";

export function LoadingState() {
  const { t } = useI18n();
  return <div className="stateBox">{t("loading")}</div>;
}

export function EmptyState({ message }: { message: string }) {
  return <div className="stateBox">{message}</div>;
}

export function ErrorAlert({ message }: { message: string }) {
  return (
    <div className="errorAlert" role="alert">
      {message}
    </div>
  );
}
