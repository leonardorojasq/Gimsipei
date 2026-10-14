import os
from datetime import datetime

from flask import Request
from werkzeug.utils import secure_filename

from src.database.database import SessionLocal
from src.models.class_model import ClassModel
from src.models.course import Course
from src.models.course_student import CourseStudent
from src.models.course_subject import CourseSubject
from src.models.resource import Resource, ResourceType
from src.models.subject import Subject
from src.models.user import User
from src.utils.app_logger import logger
from src.utils.file_utils import make_unique_filename, path_from_static_url, safe_remove_file


def get_resources_by_student_service(student_id: int) -> tuple[dict | None, int]:
    """Obtener el curso y materias del estudiante para ver recursos"""
    db = SessionLocal()
    try:
        # Obtener la inscripción del estudiante
        enrollment = (
            db.query(CourseStudent)
            .filter(CourseStudent.student_id == student_id)
            .first()
        )

        if not enrollment:
            return {"error": "Estudiante no inscrito en ningún curso"}, 404

        # Obtener el curso
        course = db.query(Course).filter(Course.id == enrollment.course_id).first()
        if not course:
            return {"error": "Curso no encontrado"}, 404

        # Obtener las materias del curso
        course_subjects = (
            db.query(CourseSubject)
            .filter(
                CourseSubject.course_id == course.id, CourseSubject.is_active.is_(True)
            )
            .all()
        )

        subjects_data = []
        for cs in course_subjects:
            subject = db.query(Subject).filter(Subject.id == cs.subject_id).first()
            if subject:
                subjects_data.append(
                    {
                        "subject": subject,
                        "course_subject_id": cs.id,
                    }
                )

        return {
            "course": course,
            "subjects": subjects_data,
        }, 200

    except Exception as e:
        return {"error": f"Error al obtener las materias: {str(e)}"}, 500
    finally:
        db.close()


def get_resources_by_student_subject_service(
    user_id: int, course_id: int, subject_id: int
) -> tuple[dict | None, int]:
    """Obtener recursos de una materia específica para un estudiante o profesor"""
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return {"error": "Usuario no encontrado"}, 404

        if user.role.value == "student":
            # Verificar que el estudiante está inscrito en el curso
            enrollment = (
                db.query(CourseStudent)
                .filter(
                    CourseStudent.student_id == user_id,
                    CourseStudent.course_id == course_id,
                )
                .first()
            )

            if not enrollment:
                return {"error": "No estás inscrito en este curso"}, 403
        # Para profesores, permitir acceso sin verificación de inscripción

        # Obtener el curso
        course = db.query(Course).filter(Course.id == course_id).first()
        if not course:
            return {"error": "Curso no encontrado"}, 404

        # Obtener la materia
        subject = db.query(Subject).filter(Subject.id == subject_id).first()
        if not subject:
            return {"error": "Materia no encontrada"}, 404

        # Obtener las clases de esta materia para este curso
        classes = (
            db.query(ClassModel)
            .filter(
                ClassModel.course_id == course_id, ClassModel.subject_id == subject_id
            )
            .all()
        )

        # Obtener los recursos de estas clases
        class_ids = [c.id for c in classes]
        resources = (
            db.query(Resource)
            .filter(Resource.class_id.in_(class_ids))
            .order_by(Resource.period, Resource.class_id)
            .all()
        )

        # Agrupar recursos por período
        periods_data = {1: [], 2: [], 3: [], 4: []}
        for resource in resources:
            class_info = next((c for c in classes if c.id == resource.class_id), None)
            periods_data[resource.period].append(
                {
                    "id": resource.id,
                    "title": resource.title,
                    "cover_image": resource.cover_image,
                    "period": resource.period,
                    "class_number": class_info.class_number if class_info else None,
                    "file_url": resource.file_url,
                    "resource_type": resource.resource_type.value,
                }
            )

        return {
            "course": course,
            "subject": subject,
            "periods": periods_data,
            "total_resources": len(resources),
        }, 200

    except Exception as e:
        return {"error": f"Error al obtener los recursos: {str(e)}"}, 500
    finally:
        db.close()


def get_resources_by_class_service(class_id: int) -> tuple[list[dict], int]:
    """Obtener recursos de una clase específica"""
    db = SessionLocal()
    try:
        resources = (
            db.query(Resource)
            .filter(Resource.class_id == class_id)
            .order_by(Resource.created_at.desc())
            .all()
        )

        resources_list = []
        for resource in resources:
            resources_list.append(
                {
                    "id": resource.id,
                    "title": resource.title,
                    "cover_image": resource.cover_image,
                    "period": resource.period,
                    "file_url": resource.file_url,
                    "resource_type": resource.resource_type.value,
                    "created_at": resource.created_at.isoformat(),
                }
            )

        return resources_list, 200
    finally:
        db.close()


def get_resources_by_teacher_service(teacher_id: int) -> tuple[dict | None, int]:
    """Obtener todos los recursos organizados por materia para un profesor.

    Muestra los recursos de las materias que el profesor enseña
    (CourseSubject.teacher_id == teacher_id) Y, además, los recursos que
    el propio profesor creó aunque la materia no esté asignada a él vía
    CourseSubject. Esto evita que un recurso quede invisible para su autor
    cuando aún no se le ha asignado la materia en CourseSubject.
    """
    db = SessionLocal()
    try:
        # Materias que enseña el profesor (vía CourseSubject)
        taught_course_subjects = (
            db.query(CourseSubject, Subject)
            .join(Subject, CourseSubject.subject_id == Subject.id)
            .filter(CourseSubject.teacher_id == teacher_id)
            .distinct(Subject.id)
            .all()
        )

        # Materias en las que el profesor tiene recursos creados (incluso
        # si no está asignado a ellas vía CourseSubject)
        created_subjects = (
            db.query(Subject)
            .join(ClassModel, ClassModel.subject_id == Subject.id)
            .join(Resource, Resource.class_id == ClassModel.id)
            .filter(Resource.created_by == teacher_id)
            .distinct()
            .all()
        )

        # Combinar las dos fuentes en un dict {subject_id: Subject}
        subjects_by_id: dict = {}
        for _, subject in taught_course_subjects:
            subjects_by_id[subject.id] = subject
        for subject in created_subjects:
            subjects_by_id.setdefault(subject.id, subject)

        if not subjects_by_id:
            return {"subjects": []}, 200

        # Set de subject_ids donde el profesor SÍ está asignado vía CourseSubject
        taught_subject_ids = {s.id for _, s in taught_course_subjects}

        subjects_data = []
        for subject in subjects_by_id.values():
            if subject.id in taught_subject_ids:
                # El profesor enseña esta materia: mostrar las clases de las
                # course_subject que le corresponden.
                classes = (
                    db.query(ClassModel)
                    .join(
                        CourseSubject,
                        (CourseSubject.subject_id == ClassModel.subject_id)
                        & (CourseSubject.course_id == ClassModel.course_id),
                    )
                    .filter(
                        ClassModel.subject_id == subject.id,
                        CourseSubject.teacher_id == teacher_id,
                    )
                    .all()
                )
            else:
                # El profesor NO enseña esta materia pero creó recursos en
                # alguna de sus clases. Mostrar las clases donde tiene
                # recursos propios.
                classes = (
                    db.query(ClassModel)
                    .join(Resource, Resource.class_id == ClassModel.id)
                    .filter(
                        ClassModel.subject_id == subject.id,
                        Resource.created_by == teacher_id,
                    )
                    .distinct()
                    .all()
                )

            # Obtener los recursos visibles para este profesor en estas clases:
            # todas las clases que el profesor enseña + las clases donde él
            # creó recursos.
            class_ids = [c.id for c in classes]
            resources = (
                db.query(Resource)
                .filter(
                    Resource.class_id.in_(class_ids),
                    # Mostrar todos los recursos de las clases que enseña,
                    # o solo los propios en las que no enseña.
                    (Resource.created_by == teacher_id)
                    | (subject.id in taught_subject_ids),
                )
                .order_by(Resource.period, Resource.class_id)
                .all()
            )

            # Agrupar recursos por período
            periods_data = {1: [], 2: [], 3: [], 4: []}
            for resource in resources:
                class_info = next(
                    (c for c in classes if c.id == resource.class_id), None
                )
                periods_data[resource.period].append(
                    {
                        "id": resource.id,
                        "title": resource.title,
                        "cover_image": resource.cover_image,
                        "period": resource.period,
                        "class_number": class_info.class_number if class_info else None,
                        "file_url": resource.file_url,
                        "resource_type": resource.resource_type.value,
                    }
                )

            # course_id: tomar el primero disponible (de las clases que enseña
            # o, si no, de la primera clase donde creó recursos)
            course_id = classes[0].course_id if classes else None

            subjects_data.append(
                {
                    "subject_id": subject.id,
                    "subject_name": subject.name,
                    "course_id": course_id,
                    "periods": periods_data,
                    "total_resources": len(resources),
                }
            )

        return {"subjects": subjects_data}, 200
    finally:
        db.close()


def get_resource_service(resource_id: int, request: Request) -> tuple[dict | None, int]:
    """Obtener un recurso específico"""
    db = SessionLocal()
    try:
        resource = db.query(Resource).filter(Resource.id == resource_id).first()
        if not resource:
            return None, 404

        return {
            "id": resource.id,
            "class_id": resource.class_id,
            "title": resource.title,
            "cover_image": resource.cover_image,
            "period": resource.period,
            "file_url": resource.file_url,
            "resource_type": resource.resource_type.value,
            "created_by": resource.created_by,
            "created_at": resource.created_at.isoformat(),
            "updated_at": resource.updated_at.isoformat(),
        }, 200
    finally:
        db.close()


def get_resource_file_path_service(
    resource_id: int,
) -> tuple[str | None, str | None, int]:
    """
    Obtener la ruta del archivo de un recurso para descarga
    """
    db = SessionLocal()
    try:
        resource = db.query(Resource).filter(Resource.id == resource_id).first()
        if not resource:
            return None, None, 404

        if not resource.file_url:
            return None, None, 404

        # Construir la ruta completa del archivo
        file_path = os.path.join("src", resource.file_url.lstrip("/"))

        # Verificar que el archivo existe
        if not os.path.exists(file_path):
            return None, None, 404

        # Obtener el nombre del archivo original
        filename = os.path.basename(file_path)
        if resource.title:
            # Usar el título como nombre base y mantener la extensión del archivo
            file_ext = os.path.splitext(filename)[1]
            filename = f"{resource.title}{file_ext}"

        return file_path, filename, 200
    finally:
        db.close()


def create_resource_service(
    data: dict,
    cover_file=None,
    resource_file=None,
    created_by_user_id=None,
) -> tuple[dict | None, int]:
    """Crear un nuevo recurso"""
    db = SessionLocal()
    try:
        class_number = data.get("class_id")
        course_id = data.get("course_id")
        subject_id = data.get("subject_id")
        period = data.get("period")

        try:
            class_number_int = int(class_number) if class_number else None
            course_id_int = int(course_id) if course_id else None
            subject_id_int = int(subject_id) if subject_id else None
            period_int = int(period) if period else None
        except (ValueError, TypeError):
            return {"error": "Valores inválidos en los datos del formulario"}, 400

        if not all([course_id_int, subject_id_int, class_number_int, period_int]):
            return {
                "error": "Faltan datos requeridos: curso, materia, número de clase y periodo"
            }, 400

        # Buscar la clase por número de clase, course_id, subject_id y period
        class_obj = (
            db.query(ClassModel)
            .filter(
                ClassModel.course_id == course_id_int,
                ClassModel.subject_id == subject_id_int,
                ClassModel.class_number == class_number_int,
                ClassModel.period == period_int,
            )
            .first()
        )

        if not class_obj:
            return {"error": "La clase especificada no existe"}, 404

        # Usar el ID real de la clase encontrada
        actual_class_id = class_obj.id

        # Procesar archivo de portada si existe
        cover_image_path = None
        if cover_file and cover_file.filename:
            # Use microsecond precision + collision-suffix so two
            # uploads in the same second (or with the same original
            # filename) never overwrite each other on disk.
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            filename = f"{timestamp}_{secure_filename(cover_file.filename)}"
            upload_folder = os.path.join(
                "src", "static", "uploads", "resources", "covers"
            )
            os.makedirs(upload_folder, exist_ok=True)
            filename = make_unique_filename(upload_folder, filename)
            file_path = os.path.join(upload_folder, filename)
            cover_file.save(file_path)
            cover_image_path = f"/static/uploads/resources/covers/{filename}"

        # Procesar archivo de recurso si existe
        file_url = None
        resource_type = ResourceType.FILE

        if resource_file and resource_file.filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            filename = f"{timestamp}_{secure_filename(resource_file.filename)}"
            upload_folder = os.path.join(
                "src", "static", "uploads", "resources", "files"
            )
            os.makedirs(upload_folder, exist_ok=True)
            filename = make_unique_filename(upload_folder, filename)
            file_path = os.path.join(upload_folder, filename)
            resource_file.save(file_path)
            file_url = f"/static/uploads/resources/files/{filename}"

        # Crear el recurso
        new_resource = Resource(
            class_id=actual_class_id,
            title=data["title"],
            cover_image=cover_image_path,
            period=data["period"],
            file_url=file_url,
            resource_type=resource_type,
            created_by=created_by_user_id,
        )

        db.add(new_resource)
        db.commit()
        db.refresh(new_resource)

        return {
            "message": "Recurso creado exitosamente",
            "resource": {
                "id": new_resource.id,
                "title": new_resource.title,
                "class_id": new_resource.class_id,
                "period": new_resource.period,
            },
        }, 201

    except Exception as e:
        db.rollback()
        return {"error": f"Error al crear el recurso: {str(e)}"}, 500
    finally:
        db.close()


def update_resource_service(
    resource_id: int,
    data: dict,
    cover_file=None,
    resource_file=None,
) -> tuple[dict | None, int]:
    """Actualizar un recurso existente"""
    db = SessionLocal()
    try:
        resource = db.query(Resource).filter(Resource.id == resource_id).first()
        if not resource:
            return None, 404

        # Actualizar campos básicos si se proporcionan
        if "title" in data and data["title"]:
            resource.title = data["title"]
        if "period" in data and data["period"]:
            resource.period = data["period"]

        # Procesar nueva portada si existe
        if cover_file and cover_file.filename:
            # Remove the old cover file BEFORE saving the new one, so
            # even if the save fails later the previous one is gone
            # (consistent with how file_url is handled below).
            if resource.cover_image:
                old_cover = path_from_static_url(resource.cover_image)
                safe_remove_file(old_cover)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            filename = f"{timestamp}_{secure_filename(cover_file.filename)}"
            upload_folder = os.path.join(
                "src", "static", "uploads", "resources", "covers"
            )
            os.makedirs(upload_folder, exist_ok=True)
            filename = make_unique_filename(upload_folder, filename)
            file_path = os.path.join(upload_folder, filename)
            cover_file.save(file_path)
            resource.cover_image = f"/static/uploads/resources/covers/{filename}"

        # Procesar nuevo archivo de recurso si existe
        if resource_file and resource_file.filename:
            if resource.file_url:
                old_file_path = path_from_static_url(resource.file_url)
                safe_remove_file(old_file_path)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            filename = f"{timestamp}_{secure_filename(resource_file.filename)}"
            upload_folder = os.path.join(
                "src", "static", "uploads", "resources", "files"
            )
            os.makedirs(upload_folder, exist_ok=True)
            filename = make_unique_filename(upload_folder, filename)
            file_path = os.path.join(upload_folder, filename)
            resource_file.save(file_path)
            resource.file_url = f"/static/uploads/resources/files/{filename}"
            resource.resource_type = ResourceType.FILE

        db.commit()
        db.refresh(resource)

        return {
            "message": "Recurso actualizado exitosamente",
            "resource": {
                "id": resource.id,
                "title": resource.title,
                "cover_image": resource.cover_image,
            },
        }, 200

    except Exception:
        db.rollback()
        return None, 500
    finally:
        db.close()


def delete_resource_service(
    resource_id: int, request: Request
) -> tuple[dict | None, int]:
    """Eliminar un recurso.

    Delete order: DB row first, then physical files. If the commit
    fails the record stays (consistent) and the files remain on disk
    (orphan but recoverable). If file removal fails the record is
    already gone; the file becomes orphan and is logged so it can be
    reaped later by the orphan-cleanup utility.
    """
    db = SessionLocal()
    try:
        resource = db.query(Resource).filter(Resource.id == resource_id).first()
        if not resource:
            return None, 404

        # Capture paths BEFORE deleting the row
        cover_path = path_from_static_url(resource.cover_image)
        file_path = path_from_static_url(resource.file_url)
        title_for_log = resource.title

        db.delete(resource)
        db.commit()

        # Files only get removed once the DB delete has committed
        removed_cover = safe_remove_file(cover_path)
        removed_file = safe_remove_file(file_path)
        if not removed_cover and cover_path:
            logger.error(
                "Resource %s deleted from DB but cover file remained on disk: %s",
                resource_id, cover_path,
            )
        if not removed_file and file_path:
            logger.error(
                "Resource %s deleted from DB but file remained on disk: %s",
                resource_id, file_path,
            )
        logger.info(
            "Resource %r (id=%s) deleted (cover_removed=%s file_removed=%s)",
            title_for_log, resource_id, removed_cover, removed_file,
        )

        return {"message": "Recurso eliminado exitosamente"}, 200
    except Exception as exc:
        db.rollback()
        logger.critical("Unhandled exception in delete_resource_service: %s", exc)
        return None, 500
    finally:
        db.close()
