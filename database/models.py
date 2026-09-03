from datetime import datetime

from database.database import (
    students_collection,
    documents_collection,
    lessons_collection,
    learning_sessions_collection,
    quiz_questions_collection,
    quiz_attempts_collection,
    assessments_collection,
    progress_collection,
    weekly_tests_collection,
    recommendations_collection
)


# ==========================================
# STUDENT
# ==========================================

def create_student(
    name,
    education_level,
    preferred_language="English",
    learning_goal=None,
    preferred_style="Visual"
):
    student = {
        "name": name,
        "education_level": education_level,
        "preferred_language": preferred_language,
        "learning_goal": learning_goal,
        "preferred_style": preferred_style,

        "topics_studied": [],
        "strong_concepts": [],
        "weak_concepts": [],
        "current_learning_path": [],

        "created_at": datetime.utcnow()
    }

    result = students_collection.insert_one(student)

    return result.inserted_id


# ==========================================
# DOCUMENT
# ==========================================

def create_document(
    student_id,
    filename,
    file_type,
    title,
    subject=None,
    language="English",
    file_path=None
):
    document = {
        "student_id": student_id,
        "filename": filename,
        "file_type": file_type,
        "title": title,
        "subject": subject,
        "language": language,
        "file_path": file_path,
        "uploaded_at": datetime.utcnow()
    }

    result = documents_collection.insert_one(document)

    return result.inserted_id


# ==========================================
# LESSON
# ==========================================

def create_lesson(
    student_id,
    topic,
    difficulty,
    language,
    duration_minutes,
    lesson_plan,
    document_id=None
):
    lesson = {
        "student_id": student_id,
        "document_id": document_id,
        "topic": topic,
        "difficulty": difficulty,
        "language": language,
        "duration_minutes": duration_minutes,
        "lesson_plan": lesson_plan,
        "created_at": datetime.utcnow()
    }

    result = lessons_collection.insert_one(lesson)

    return result.inserted_id
    
# ==========================================
# LEARNING SESSION
# ==========================================

def create_learning_session(
    student_id,
    lesson_id=None,
    topic=None,
    start_time=None,
    end_time=None,
    duration_minutes=0
):
    session = {
        "student_id": student_id,
        "lesson_id": lesson_id,
        "topic": topic,
        "start_time": start_time,
        "end_time": end_time,
        "duration_minutes": duration_minutes,
        "created_at": datetime.utcnow()
    }

    result = learning_sessions_collection.insert_one(session)

    return result.inserted_id


# ==========================================
# QUIZ QUESTION
# ==========================================

def create_quiz_question(
    lesson_id,
    question,
    options,
    correct_answer,
    difficulty="Medium"
):
    quiz_question = {
        "lesson_id": lesson_id,
        "question": question,
        "options": options,
        "correct_answer": correct_answer,
        "difficulty": difficulty,
        "created_at": datetime.utcnow()
    }

    result = quiz_questions_collection.insert_one(quiz_question)

    return result.inserted_id


# ==========================================
# QUIZ ATTEMPT
# ==========================================

def create_quiz_attempt(
    student_id,
    question_id,
    selected_answer,
    is_correct
):
    attempt = {
        "student_id": student_id,
        "question_id": question_id,
        "selected_answer": selected_answer,
        "is_correct": is_correct,
        "attempted_at": datetime.utcnow()
    }

    result = quiz_attempts_collection.insert_one(attempt)

    return result.inserted_id


# ==========================================
# ASSESSMENT
# ==========================================

def create_assessment(
    student_id,
    topic,
    score,
    total_questions,
    assessment_type="Quiz"
):
    assessment = {
        "student_id": student_id,
        "topic": topic,
        "score": score,
        "total_questions": total_questions,
        "assessment_type": assessment_type,
        "created_at": datetime.utcnow()
    }

    result = assessments_collection.insert_one(assessment)

    return result.inserted_id


# ==========================================
# PROGRESS
# ==========================================

def create_progress(
    student_id,
    topic,
    progress_percentage,
    status="In Progress"
):
    progress = {
        "student_id": student_id,
        "topic": topic,
        "progress_percentage": progress_percentage,
        "status": status,
        "updated_at": datetime.utcnow()
    }

    result = progress_collection.insert_one(progress)

    return result.inserted_id


# ==========================================
# WEEKLY TEST
# ==========================================

def create_weekly_test(
    student_id,
    topic,
    questions,
    total_marks
):
    weekly_test = {
        "student_id": student_id,
        "topic": topic,
        "questions": questions,
        "total_marks": total_marks,
        "created_at": datetime.utcnow()
    }

    result = weekly_tests_collection.insert_one(weekly_test)

    return result.inserted_id


# ==========================================
# RECOMMENDATION
# ==========================================

def create_recommendation(
    student_id,
    topic,
    recommendation,
    reason=None
):
    recommendation_data = {
        "student_id": student_id,
        "topic": topic,
        "recommendation": recommendation,
        "reason": reason,
        "created_at": datetime.utcnow()
    }

    result = recommendations_collection.insert_one(
        recommendation_data
    )

    return result.inserted_id