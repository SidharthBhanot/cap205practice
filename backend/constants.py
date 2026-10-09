from enum import StrEnum


class SourceType(StrEnum):
    LMS = "LMS"
    ERP = "ERP"
    NOTICE = "Faculty Notice"
    EMAIL = "Email"
    PDF = "PDF"
    MANUAL = "Manual"


class ObligationType(StrEnum):
    ASSIGNMENT = "Assignment"
    QUIZ = "Quiz"
    EXAMINATION = "Examination"
    PROJECT = "Project"
    OTHER = "Other"


class ObligationStatus(StrEnum):
    PLANNED = "Planned"
    PROGRESS = "In Progress"
    COMPLETED = "Completed"
    CANCELLED = "Cancelled"


class ReviewStatus(StrEnum):
    NEEDS = "Needs Verification"
    REVIEW = "Under Review"
    RESOLVED = "Resolved"
    DISMISSED = "Dismissed"


class Classification(StrEnum):
    MATCH = "MATCH"
    POTENTIAL = "POTENTIAL_MATCH"
    CONFLICT = "CONFLICT"
    UNRELATED = "UNRELATED"


class IssueType(StrEnum):
    DEADLINE = "DEADLINE_CONFLICT"
    DUPLICATE = "DUPLICATE"
    MISSING = "MISSING_DEADLINE"
    INCOMPLETE = "INCOMPLETE_INFORMATION"
    OUTDATED = "OUTDATED_INFORMATION"


OPEN_STATUSES = (ReviewStatus.NEEDS.value, ReviewStatus.REVIEW.value)
