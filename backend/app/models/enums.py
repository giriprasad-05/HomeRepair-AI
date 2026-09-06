import enum


class ApplianceCategory(str, enum.Enum):
    REFRIGERATOR = "refrigerator"
    WASHING_MACHINE = "washing_machine"
    AIR_CONDITIONER = "air_conditioner"
    MICROWAVE = "microwave"
    DISHWASHER = "dishwasher"
    TELEVISION = "television"
    OTHER = "other"


class IssueSeverity(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class IssueStatus(str, enum.Enum):
    OPEN = "open"
    INVESTIGATING = "investigating"
    REPAIR_RECOMMENDED = "repair_recommended"
    REPAIR_IN_PROGRESS = "repair_in_progress"
    RESOLVED = "resolved"
    FAILED = "failed"


class RepairOutcome(str, enum.Enum):
    SUCCESSFUL = "successful"
    FAILED = "failed"
    PARTIALLY_RESOLVED = "partially_resolved"


class MemoryType(str, enum.Enum):
    RECURRING_FAULT = "recurring_fault"
    PREVIOUS_REPAIR = "previous_repair"
    APPLIANCE_BEHAVIOR = "appliance_behavior"
    SUCCESSFUL_FIX = "successful_fix"
    FAILED_FIX = "failed_fix"
    MAINTENANCE_PATTERN = "maintenance_pattern"


class AnalysisMode(str, enum.Enum):
    HISTORICAL_MATCH = "historical_match"
    FRESH_INVESTIGATION = "fresh_investigation"
    REINVESTIGATION_REQUIRED = "reinvestigation_required"
    INSUFFICIENT_DATA = "insufficient_data"
