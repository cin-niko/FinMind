export function LoadingState() {
  return <div className="stateBox">Loading</div>;
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
