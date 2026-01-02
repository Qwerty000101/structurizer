from pathlib import Path
from analyzer.project_analyzer import ProjectAnalyzer

analyzer = ProjectAnalyzer(
    root_dir=Path('D:\structurizer\structurizer'),
    output_file=Path("outputs/test_project.txt"),
    ignored_dirs={"__pycache__", ".git"},
    ignored_files={"secret.py"},
    allowed_extensions={".py"}
)

analyzer.run()
