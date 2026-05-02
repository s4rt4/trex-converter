from app.engines.base import StubEngine


class LibreOfficeEngine(StubEngine):
    def __init__(self) -> None:
        super().__init__(
            name="libreoffice",
            supported_pairs={
                ("docx", "pdf"),
                ("xlsx", "pdf"),
                ("pptx", "pdf"),
                ("odt", "pdf"),
            },
            requires_binary="libreoffice",
        )
