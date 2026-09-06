import os


class ProjectManager:
    """
    Gestión de Proyectos Estructurados (P21.c).
    """
    def init_project(self, base_path: str) -> dict:
        """
        Inicializa un proyecto como carpeta (A21-3).
        Crea la estructura base .venim
        """
        magi_dir = os.path.join(base_path, ".venim")
        os.makedirs(magi_dir, exist_ok=True)

        # Simulamos creación del gitignore para excluir blobs grandes y el .venim/memory
        gitignore_path = os.path.join(base_path, ".gitignore")
        with open(gitignore_path, "w") as f:
            f.write(".venim/memory/\ncas/\n")

        return {"status": "created", "path": base_path}
