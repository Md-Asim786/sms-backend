import logging
import json
from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger("lms_audit")


class AuditLogger:
    """Centralized audit logging for LMS operations"""

    @staticmethod
    def log_assignment_deleted(
        assignment_id: UUID, deleted_by: str, assignment_title: str
    ):
        """Log assignment deletion"""
        logger.info(
            json.dumps(
                {
                    "action": "ASSIGNMENT_DELETED",
                    "assignment_id": str(assignment_id),
                    "assignment_title": assignment_title,
                    "deleted_by": deleted_by,
                    "timestamp": datetime.utcnow().isoformat(),
                }
            )
        )

    @staticmethod
    def log_grade_updated(
        submission_id: UUID,
        assignment_id: UUID,
        student_id: UUID,
        old_grade: Optional[str],
        new_grade: str,
        updated_by: str,
    ):
        """Log grade updates"""
        logger.info(
            json.dumps(
                {
                    "action": "GRADE_UPDATED",
                    "submission_id": str(submission_id),
                    "assignment_id": str(assignment_id),
                    "student_id": str(student_id),
                    "old_grade": old_grade,
                    "new_grade": new_grade,
                    "updated_by": updated_by,
                    "timestamp": datetime.utcnow().isoformat(),
                }
            )
        )

    @staticmethod
    def log_attendance_edited(
        attendance_id: UUID,
        student_id: UUID,
        old_status: str,
        new_status: str,
        reason: Optional[str],
        edited_by: str,
    ):
        """Log attendance edits"""
        logger.info(
            json.dumps(
                {
                    "action": "ATTENDANCE_EDITED",
                    "attendance_id": str(attendance_id),
                    "student_id": str(student_id),
                    "old_status": old_status,
                    "new_status": new_status,
                    "reason": reason,
                    "edited_by": edited_by,
                    "timestamp": datetime.utcnow().isoformat(),
                }
            )
        )

    @staticmethod
    def log_lecture_deleted(lecture_id: UUID, deleted_by: str, lecture_title: str):
        """Log lecture deletion"""
        logger.info(
            json.dumps(
                {
                    "action": "LECTURE_DELETED",
                    "lecture_id": str(lecture_id),
                    "lecture_title": lecture_title,
                    "deleted_by": deleted_by,
                    "timestamp": datetime.utcnow().isoformat(),
                }
            )
        )

    @staticmethod
    def log_submission(
        submission_id: UUID, assignment_id: UUID, student_id: str, action: str
    ):
        """Log assignment submissions"""
        logger.info(
            json.dumps(
                {
                    "action": f"SUBMISSION_{action}",
                    "submission_id": str(submission_id),
                    "assignment_id": str(assignment_id),
                    "student_id": student_id,
                    "timestamp": datetime.utcnow().isoformat(),
                }
            )
        )

    @staticmethod
    def log_login(user_id: str, email: str, role: str, success: bool):
        """Log authentication attempts"""
        logger.info(
            json.dumps(
                {
                    "action": "LOGIN_ATTEMPT",
                    "user_id": user_id,
                    "email": email,
                    "role": role,
                    "success": success,
                    "timestamp": datetime.utcnow().isoformat(),
                }
            )
        )


audit_logger = AuditLogger()
