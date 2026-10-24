from typing import Any, Literal
from pydantic import BaseModel, ConfigDict, Field


class StrictModel(BaseModel):
    model_config = ConfigDict(extra='forbid', allow_inf_nan=False)


class Viewport(StrictModel):
    width: int = Field(default=1280, ge=320, le=1440)
    height: int = Field(default=800, ge=320, le=1000)


class OpenRequest(StrictModel):
    url: str = Field(min_length=1, max_length=2048)
    viewport: Viewport = Field(default_factory=Viewport)


class FrameRequest(StrictModel):
    frameId: str = Field(min_length=1, max_length=64)


class PointRequest(FrameRequest):
    # These are remote viewport CSS pixels, never physical device pixels.
    x: float = Field(ge=0, le=1440)
    y: float = Field(ge=0, le=1000)


class ScrollRequest(PointRequest):
    deltaY: float = Field(ge=-1000, le=1000)
    deltaX: float = Field(default=0, ge=-1000, le=1000)


class HoverRequest(FrameRequest):
    durationMs: int = Field(default=1000, ge=300, le=2000)
    intervalMs: int = Field(default=100, ge=50, le=500)


class Geometry(StrictModel):
    x: float
    y: float
    width: float
    height: float
    top: float
    right: float
    bottom: float
    left: float


class ElementInfo(StrictModel):
    referenceId: str
    tagName: str
    id: str
    classes: list[str]
    selector: str
    selectorUnique: bool
    selectorScope: str
    text: str
    html: str
    htmlTruncated: bool
    accessibility: dict[str, Any]


class AnimationInfo(StrictModel):
    detected: bool
    metadata: dict[str, str]
    active: list[dict[str, Any]]
    observations: list[dict[str, Any]] = Field(default_factory=list)
    hover: dict[str, Any] | None = None


class Inspection(StrictModel):
    schemaVersion: Literal['0.1'] = '0.1'
    capturedAt: str
    source: dict[str, Any]
    element: ElementInfo
    geometry: Geometry
    styles: dict[str, str]
    styleGroups: dict[str, dict[str, str]]
    pseudoElements: dict[str, dict[str, str]]
    customProperties: dict[str, str]
    animations: AnimationInfo
    limitations: list[str]
