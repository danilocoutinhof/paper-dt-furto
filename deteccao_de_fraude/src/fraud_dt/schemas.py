from dataclasses import dataclass
from enum import StrEnum


class Scenario(StrEnum):
    NORMAL = "normal"
    PERSISTENT_THEFT = "persistent_theft"
    PEAK_THEFT = "peak_theft"
    NIGHT_THEFT = "night_theft"
    INTERMITTENT_EVENING = "intermittent_evening"
    DISTURBANCE_WITHOUT_THEFT = "disturbance_without_theft"
    DEGRADED_LINK_NO_THEFT = "degraded_link_no_theft"


@dataclass(frozen=True)
class TelemetrySchemaDescription:
    note: str = (
        "Field names are aligned with the firmware metrology and alarm domain to keep "
        "the article implementation close to the embedded project semantics."
    )
