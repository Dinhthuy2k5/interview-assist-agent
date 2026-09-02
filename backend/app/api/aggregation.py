import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import require_role
from app.core.db import get_db
from app.models.aggregation import AggregationReport
from app.models.competency import CompetencyFramework, Criterion
from app.models.job import Job
from app.models.session import InterviewerNote
from app.models.user import UserRole
from app.schemas.aggregation import AggregationReportResponse, RawNoteResponse
from app.services.aggregation import (
    SemanticCheckError,
    build_interviewer_labels,
    compute_overall_recommendation,
    compute_weighted_average,
    detect_conflict,
    get_ordered_participants,
    log_llm_usage,
    summarize_conflict,
)
from app.services.session_access import get_session_or_404

router = APIRouter(prefix="/sessions", tags=["aggregation"])


@router.post(
    "/{session_id}/aggregate",
    response_model=AggregationReportResponse,
    dependencies=[Depends(require_role(UserRole.hr_admin))],
)
def aggregate_session(session_id: uuid.UUID, db: Session = Depends(get_db)):
    session = get_session_or_404(session_id, db)

    job = db.get(Job, session.job_id)
    framework = db.get(CompetencyFramework, job.framework_id)
    if not framework or not framework.criteria:
        raise HTTPException(400, "Framework của job này chưa có criterion nào")

    # Danh sách participant CỐ ĐỊNH theo 1 thứ tự duy nhất cho toàn bộ report -
    # là nguồn label ẩn danh DUY NHẤT, dùng lại cho mọi criterion. Trước đây label
    # được gán theo enumerate(notes) của TỪNG criterion riêng lẻ - nếu 1 interviewer
    # bỏ sót note ở 1 criterion, "Người phỏng vấn 1" ở 2 criterion có thể là 2 người
    # khác nhau, phá hỏng mục đích ẩn danh nhất quán.
    participants = get_ordered_participants(session_id, db)
    if not participants:
        raise HTTPException(400, "Session chưa gán interviewer nào")

    interviewer_label = build_interviewer_labels([p.interviewer_id for p in participants])

    per_criterion_summary = []
    criterion_averages_for_weighting = []

    for criterion in framework.criteria:
        notes = (
            db.query(InterviewerNote)
            .filter(
                InterviewerNote.session_id == session_id,
                InterviewerNote.criterion_id == criterion.id,
            )
            .all()
        )
        scores = [n.score for n in notes if n.score is not None]
        note_texts = [n.note_text for n in notes if n.note_text]
        average = sum(scores) / len(scores) if scores else None

        submitted_ids = {n.interviewer_id for n in notes}
        missing_labels = [
            label for interviewer_id, label in interviewer_label.items() if interviewer_id not in submitted_ids
        ]

        has_conflict, conflict_type = detect_conflict(scores, note_texts)

        semantic_note = None
        if has_conflict:
            labeled_notes = [
                {
                    "label": interviewer_label.get(n.interviewer_id, "Người phỏng vấn (không xác định)"),
                    "score": n.score,
                    "note_text": n.note_text,
                }
                for n in notes
            ]
            try:
                semantic_note, usage = summarize_conflict(criterion.name, labeled_notes)
                log_llm_usage(db, usage)
            except SemanticCheckError:
                semantic_note = "(Không tạo được tóm tắt tự động - vui lòng xem note gốc)"

        per_criterion_summary.append(
            {
                "criterion_id": str(criterion.id),
                "criterion_name": criterion.name,
                "scores": scores,
                "average": average,
                "has_conflict": has_conflict,
                "conflict_type": conflict_type,
                "semantic_note": semantic_note,
                "missing_interviewer_labels": missing_labels,
            }
        )
        if average is not None:
            criterion_averages_for_weighting.append((average, float(criterion.weight)))

    weighted_average = compute_weighted_average(criterion_averages_for_weighting)
    recommendation = compute_overall_recommendation(weighted_average)

    conflicts = [c for c in per_criterion_summary if c["has_conflict"]]
    if conflicts:
        conflict_names = ", ".join(c["criterion_name"] for c in conflicts)
        rationale_trace = (
            f"Điểm trung bình có trọng số: {weighted_average:.2f}/5 -> {recommendation}. "
            f"Phát hiện đánh giá không đồng nhất giữa các interviewer ở tiêu chí: "
            f"{conflict_names} - xem phần tóm tắt từng tiêu chí và note gốc trước khi quyết định."
        )
    else:
        rationale_trace = (
            f"Điểm trung bình có trọng số: {weighted_average:.2f}/5 -> {recommendation}. "
            f"Các interviewer đánh giá đồng nhất trên mọi tiêu chí."
            if weighted_average is not None
            else "Chưa có note nào được ghi cho session này."
        )

    report = db.query(AggregationReport).filter(AggregationReport.session_id == session_id).first()
    if report is None:
        report = AggregationReport(session_id=session_id)
        db.add(report)

    report.per_criterion_summary = per_criterion_summary
    report.overall_score = weighted_average
    report.overall_recommendation = recommendation
    report.rationale_trace = rationale_trace

    db.commit()
    db.refresh(report)
    return report


@router.get(
    "/{session_id}/aggregation",
    response_model=AggregationReportResponse,
    # Council cần đọc report này để "ra quyết định cuối" (đúng nhu cầu trong Phân
    # tích ban đầu) - CHỈ đọc, không được trigger tổng hợp (POST vẫn hr_admin-only).
    dependencies=[Depends(require_role(UserRole.hr_admin, UserRole.council))],
)
def get_aggregation_report(session_id: uuid.UUID, db: Session = Depends(get_db)):
    get_session_or_404(session_id, db)
    report = db.query(AggregationReport).filter(AggregationReport.session_id == session_id).first()
    if report is None:
        raise HTTPException(404, "Session này chưa được tổng hợp")
    return report


@router.get(
    "/{session_id}/notes",
    response_model=list[RawNoteResponse],
    dependencies=[Depends(require_role(UserRole.hr_admin, UserRole.council))],
)
def get_session_raw_notes(session_id: uuid.UUID, db: Session = Depends(get_db)):
    """Note gốc của MỌI interviewer trong session - CHỈ hr_admin/council xem được
    (không phải interviewer, kể cả người tham gia session - giữ nguyên nguyên tắc
    'mỗi interviewer chỉ thấy note của chính mình' từ Sprint 3, endpoint này dành
    cho bước review SAU khi có report tổng hợp, không phải trong lúc phỏng vấn).

    interviewer_label dùng ĐÚNG get_ordered_participants + build_interviewer_labels
    giống hệt aggregate_session() - đảm bảo 'Người phỏng vấn 1' ở đây và ở report
    luôn là cùng 1 người."""
    get_session_or_404(session_id, db)

    participants = get_ordered_participants(session_id, db)
    if not participants:
        return []
    interviewer_label = build_interviewer_labels([p.interviewer_id for p in participants])

    rows = (
        db.query(InterviewerNote, Criterion)
        .join(Criterion, InterviewerNote.criterion_id == Criterion.id)
        .filter(InterviewerNote.session_id == session_id)
        .all()
    )
    return [
        RawNoteResponse(
            criterion_id=note.criterion_id,
            criterion_name=criterion.name,
            interviewer_label=interviewer_label.get(
                note.interviewer_id, "Người phỏng vấn (không xác định)"
            ),
            score=note.score,
            note_text=note.note_text,
        )
        for note, criterion in rows
    ]