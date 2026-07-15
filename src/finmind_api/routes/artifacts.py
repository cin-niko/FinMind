from html import escape
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status

from finmind_api.dependencies import require_session
from finmind_agents.models import Session

router = APIRouter(prefix="/api", tags=["artifacts"])


@router.get("/artifacts/{artifact_id}/download")
def download_artifact(
    artifact_id: str,
    request: Request,
    session: Annotated[Session, Depends(require_session)],
    format: str = "csv",
) -> Response:
    artifact = _find_artifact(request, artifact_id, session.username)
    if artifact is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Artifact not found",
        )
    if artifact.get("artifact_type") != "chart":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Artifact download not found",
        )
    if format == "csv":
        return Response(
            content=_chart_csv(artifact),
            media_type="text/csv",
            headers={"Content-Disposition": _content_disposition(artifact, "csv")},
        )
    if format == "svg":
        return Response(
            content=_chart_svg(artifact),
            media_type="image/svg+xml",
            headers={"Content-Disposition": _content_disposition(artifact, "svg")},
        )
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Artifact download not found",
    )


def _find_artifact(request: Request, artifact_id: str, owner: str) -> dict[str, Any] | None:
    service = request.app.state.platform.conversation_service
    for summary in service.list(owner):
        detail = service.get(str(summary["id"]), owner)
        if detail is None:
            continue
        for message in detail.get("messages", []):
            for artifact in message.get("artifacts", []):
                if artifact.get("artifact_id") == artifact_id:
                    return artifact
    return None


def _chart_csv(artifact: dict[str, Any]) -> str:
    candles = artifact.get("spec", {}).get("candles") or []
    if candles:
        lines = ["date,open,high,low,close,volume"]
        lines.extend(
            ",".join(
                str(row.get(field, ""))
                for field in ("date", "open", "high", "low", "close", "volume")
            )
            for row in candles
        )
        return "\n".join(lines) + "\n"
    series = artifact.get("spec", {}).get("series") or []
    points = series[0].get("data", []) if series else []
    lines = ["date,close,volume"]
    lines.extend(f"{point.get('date', '')},{point.get('value', '')}," for point in points)
    return "\n".join(lines) + "\n"


def _chart_svg(artifact: dict[str, Any]) -> str:
    series = artifact.get("spec", {}).get("series") or []
    points = series[0].get("data", []) if series else []
    values = [float(point.get("value", 0)) for point in points] or [0.0]
    width = 640
    height = 320
    padding = 36
    min_value = min(values)
    max_value = max(values)
    span = max(max_value - min_value, 1)
    coordinates = []
    for index, value in enumerate(values):
        x = padding + (index * (width - padding * 2) / max(len(values) - 1, 1))
        y = height - padding - ((value - min_value) / span * (height - padding * 2))
        coordinates.append(f"{x:.1f},{y:.1f}")
    title = escape(str(artifact.get("title") or "Chart"))
    polyline = " ".join(coordinates)
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" role="img" aria-label="{title}">'
        '<rect width="100%" height="100%" fill="#ffffff"/>'
        f'<text x="{padding}" y="24" fill="#172033" font-family="sans-serif" '
        f'font-size="16">{title}</text>'
        f'<polyline fill="none" stroke="#138A63" stroke-width="3" points="{polyline}"/>'
        "</svg>"
    )


def _content_disposition(artifact: dict[str, Any], format: str) -> str:
    for download in artifact.get("downloads", []):
        if download.get("format") == format and download.get("filename"):
            return f'attachment; filename="{download["filename"]}"'
    return f'attachment; filename="{artifact["artifact_id"]}.{format}"'
