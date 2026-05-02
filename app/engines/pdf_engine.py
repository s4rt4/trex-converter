from app.engines.base import StubEngine


class PDFEngine(StubEngine):
    def __init__(self) -> None:
        super().__init__(
            name="pdf",
            supported_pairs={
                ("pdf", "jpg"),
                ("pdf", "png"),
                ("jpg", "pdf"),
                ("png", "pdf"),
            },
            requires_binary="qpdf",
        )
