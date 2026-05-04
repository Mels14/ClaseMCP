from datetime import datetime
from typing import List, Optional, Dict, Any

from data.repository_interface import StudentRepositoryInterface
from data.student_repository_sqlite import StudentRepositorySQLite
from models.entity.student_entity import StudentEntity
from models.dto.student_dto import Student as StudentDTO, StudentCreate, StudentUpdate


class StudentService:
    """Servicio para operaciones CRUD sobre estudiantes.

    Opera sobre la implementación de repositorio inyectada (`StudentRepositoryInterface`).
    """

    def __init__(self, repo: StudentRepositoryInterface | None = None) -> None:
        # Inyectar la implementación de persistencia (SQLite por defecto)
        print("Tipo de repositorio ",type(repo))
        self.repo: StudentRepositoryInterface = repo if repo is not None else StudentRepositorySQLite()

    def _next_id(self, students: List[Dict[str, Any]]) -> int:
        if not students:
            return 1
        try:
            return max(int(s.get("id", 0)) for s in students) + 1
        except Exception:
            return len(students) + 1

    def _to_entity(self, data: Dict[str, Any]) -> StudentEntity:
        return StudentEntity(
            id=int(data.get("id")),
            name=data.get("name"),
            email=data.get("email"),
            age=int(data.get("age")),
            career=data.get("career"),
            semester=data.get("semester"),
            created_at=data.get("created_at"),
        )

    def _to_dict(self, entity: StudentEntity) -> Dict[str, Any]:
        return {
            "id": entity.id,
            "name": entity.name,
            "email": entity.email,
            "age": entity.age,
            "career": entity.career,
            "semester": entity.semester,
            "created_at": entity.created_at,
        }

    def add_student(self, student: StudentCreate) -> StudentDTO:
        students = self.repo.get_all()
        if any(s.get("email") == student.email for s in students):
            return {"error": "Email ya registrado"}  # type: ignore

        new_id = self._next_id(students)
        now = datetime.now().isoformat()
        entity = StudentEntity(
            id=new_id,
            name=student.name,
            email=student.email,
            age=student.age,
            career=student.career,
            semester=student.semester,
            created_at=now,
        )
        students.append(self._to_dict(entity))
        # Persistir usando la implementación inyectada
        self.repo.insert(self._to_dict(entity))
        return StudentDTO(**self._to_dict(entity))

    def list_students(self) -> List[StudentDTO]:
        print("Listando estudiantes con el repo")
        print(type(self.repo))
        return [StudentDTO(**s) for s in self.repo.get_all()]

    def get_stats(self) -> Dict[str, Any]:
        students = self.repo.get_all()
        total = len(students)
        if total == 0:
            return {"total": 0}
        avg = sum(int(s.get("age", 0)) for s in students) / total
        return {"total": total, "average_age": round(avg, 2)}

    def get_student(self, student_id: int) -> Optional[StudentDTO]:
        try:
            student_id = int(student_id)
        except Exception:
            return None
        s = self.repo.get_by_id(student_id)
        if not s:
            return None
        return StudentDTO(**s)

    def update_student(self, student_id: int, update: StudentUpdate) -> Dict[str, Any] | StudentDTO:
        try:
            student_id = int(student_id)
        except Exception:
            return {"error": "ID inválido"}
        data = update.dict(exclude_unset=True)
        students = self.repo.get_all()
        # validar email único si se intenta cambiar
        if "email" in data:
            if any(s.get("email") == data.get("email") and int(s.get("id", 0)) != student_id for s in students):
                return {"error": "Email ya registrado"}

        updated = self.repo.update(student_id, data)
        if not updated:
            return {"error": "Estudiante no encontrado"}
        return StudentDTO(**updated)

    def delete_student(self, student_id: int) -> Dict[str, Any]:
        try:
            student_id = int(student_id)
        except Exception:
            return {"error": "ID inválido"}

        ok = self.repo.delete(student_id)
        if not ok:
            return {"error": "Estudiante no encontrado"}
        return {"deleted": True}

    def get_dashboard_html_report(self) -> str:
        print("Generando reporte visual: Iniciando renderizado de Dashboard HTML")
        
        # 1. Obtener datos reales del repositorio
        students = self.repo.get_all()
        total = len(students)
        
        # 2. Calcular métricas
        if total > 0:
            avg_age = sum(int(s.get("age", 0)) for s in students) / total
            # Agrupar por carrera para las barras
            careers = {}
            for s in students:
                c = s.get("career", "N/A")
                careers[c] = careers.get(c, 0) + 1
        else:
            avg_age = 0
            careers = {}

        # 3. Construir las filas de la tabla dinámicamente
        table_rows = ""
        for s in students:
            table_rows += f"""
            <tr>
                <td style="padding: 10px; border-bottom: 1px solid #334155;">{s.get('name')}</td>
                <td style="padding: 10px; border-bottom: 1px solid #334155;">{s.get('career')}</td>
                <td style="padding: 10px; border-bottom: 1px solid #334155; text-align: center;">{s.get('semester')}°</td>
            </tr>
            """

        # 4. Generar el HTML final (Template)
        html_content = f"""
        <div style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #0f172a; color: #f8fafc; padding: 25px; border-radius: 15px; border: 1px solid #334155; max-width: 600px;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
                <h2 style="margin: 0; color: #38bdf8; font-size: 24px;">📊 Dashboard Académico</h2>
                <span style="background: #1e293b; padding: 5px 12px; border-radius: 20px; font-size: 12px; color: #94a3b8;">Sincronizado</span>
            </div>

            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin-bottom: 25px;">
                <div style="background: #1e293b; padding: 15px; border-radius: 10px; text-align: center; border: 1px solid #334155;">
                    <div style="font-size: 28px; font-weight: bold; color: #38bdf8;">{total}</div>
                    <div style="font-size: 12px; color: #94a3b8; text-transform: uppercase;">Total Estudiantes</div>
                </div>
                <div style="background: #1e293b; padding: 15px; border-radius: 10px; text-align: center; border: 1px solid #334155;">
                    <div style="font-size: 28px; font-weight: bold; color: #38bdf8;">{round(avg_age, 1)}</div>
                    <div style="font-size: 12px; color: #94a3b8; text-transform: uppercase;">Promedio Edad</div>
                </div>
            </div>

            <h3 style="font-size: 16px; margin-bottom: 10px; color: #f1f5f9;">Distribución de Carreras</h3>
            <div style="margin-bottom: 25px;">
                { "".join([f'<div style="margin-bottom: 8px;"><div style="display: flex; justify-content: space-between; font-size: 13px; margin-bottom: 4px;"><span>{c}</span><span>{n}</span></div><div style="background: #334155; height: 6px; border-radius: 3px;"><div style="background: #38bdf8; height: 100%; width: {(n/total)*100 if total > 0 else 0}%; border-radius: 3px;"></div></div></div>' for c, n in careers.items()]) }
            </div>

            <h3 style="font-size: 16px; margin-bottom: 10px; color: #f1f5f9;">Últimos Registros</h3>
            <table style="width: 100%; border-collapse: collapse; font-size: 13px;">
                <thead>
                    <tr style="color: #94a3b8; text-align: left;">
                        <th style="padding: 10px; border-bottom: 2px solid #334155;">Nombre</th>
                        <th style="padding: 10px; border-bottom: 2px solid #334155;">Carrera</th>
                        <th style="padding: 10px; border-bottom: 2px solid #334155; text-align: center;">Sem.</th>
                    </tr>
                </thead>
                <tbody>
                    {table_rows if total > 0 else '<tr><td colspan="3" style="text-align:center; padding: 20px; color: #64748b;">No hay datos disponibles</td></tr>'}
                </tbody>
            </table>
            
            <div style="margin-top: 20px; font-size: 11px; color: #475569; text-align: center;">
                Reporte generado automáticamente por el Sistema de Gestión Estudiantil
            </div>
        </div>
        """
        
        print(f"Reporte visual finalizado: {total} estudiantes procesados")
        return html_content
