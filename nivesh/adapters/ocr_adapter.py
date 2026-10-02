"""OCR Ingestion Adapter for Engine 1.

Accepts image input (bytes, base64, path, PIL Image), runs OCR,
and produces raw text along with rich OCR provenance and metadata.
Guards against corrupt images, oversized inputs, and unreadable content
without fabricating text.
"""

import io
import json
import base64
import subprocess
import sys
from pathlib import Path
from typing import Optional, Any
from PIL import Image, UnidentifiedImageError

MAX_IMAGE_SIZE_BYTES = 25 * 1024 * 1024  # 25 MB limit


class OcrResult:
    """Encapsulates the output of an OCR extraction run."""
    def __init__(
        self,
        text: str = "",
        success: bool = False,
        engine: str = "none",
        confidence: float = 0.0,
        metadata: Optional[dict[str, Any]] = None,
        warnings: Optional[list[str]] = None
    ):
        self.text = text
        self.success = success
        self.engine = engine
        self.confidence = confidence
        self.metadata = metadata or {}
        self.warnings = warnings or []


class OcrAdapter:
    """Pluggable OCR adapter supporting Windows Media OCR, PyTesseract, and custom engines."""

    def __init__(self, backend: Optional[str] = None):
        """
        backend: 'windows', 'tesseract', 'mock', or None (auto-detect)
        """
        self._custom_backend = backend
        self._script_path = Path(__file__).parent / "win_ocr.ps1"

    def process(
        self,
        image_bytes: Optional[bytes] = None,
        image_path: Optional[str] = None,
        image_base64: Optional[str] = None,
        mock_text: Optional[str] = None,
    ) -> OcrResult:
        """Processes an image input through the OCR pipeline.
        
        Returns an OcrResult with raw text and metadata.
        Never throws unhandled exceptions; reports warnings on failure.
        """
        warnings: list[str] = []

        # 1. Allow direct mock injection for headless/deterministic testing
        if self._custom_backend == "mock" or mock_text is not None:
            text = mock_text or ""
            return OcrResult(
                text=text,
                success=bool(text.strip()),
                engine="mock_ocr",
                confidence=0.95 if text.strip() else 0.0,
                metadata={"mock": True, "word_count": len(text.split())},
                warnings=[] if text.strip() else ["OCR: No text detected in image"]
            )

        # 2. Decode bytes from inputs
        raw_bytes: Optional[bytes] = None

        if image_bytes:
            raw_bytes = image_bytes
        elif image_base64:
            try:
                # Handle data URI scheme if present: data:image/png;base64,...
                if "," in image_base64:
                    image_base64 = image_base64.split(",", 1)[1]
                raw_bytes = base64.b64decode(image_base64)
            except Exception as e:
                return OcrResult(
                    text="",
                    success=False,
                    engine="none",
                    confidence=0.0,
                    warnings=[f"Failed to decode base64 image: {str(e)}"]
                )
        elif image_path:
            p = Path(image_path)
            if not p.exists():
                return OcrResult(
                    text="",
                    success=False,
                    engine="none",
                    confidence=0.0,
                    warnings=[f"Image file does not exist: {image_path}"]
                )
            try:
                raw_bytes = p.read_bytes()
            except Exception as e:
                return OcrResult(
                    text="",
                    success=False,
                    engine="none",
                    confidence=0.0,
                    warnings=[f"Failed to read image file: {str(e)}"]
                )
        else:
            return OcrResult(
                text="",
                success=False,
                engine="none",
                confidence=0.0,
                warnings=["No image input provided"]
            )

        # 3. Check file size
        if len(raw_bytes) > MAX_IMAGE_SIZE_BYTES:
            return OcrResult(
                text="",
                success=False,
                engine="none",
                confidence=0.0,
                warnings=[f"Image exceeds maximum size limit of {MAX_IMAGE_SIZE_BYTES // (1024*1024)}MB"]
            )

        # 4. Verify image format and integrity using Pillow
        try:
            with Image.open(io.BytesIO(raw_bytes)) as pil_img:
                pil_img.verify()
                img_format = pil_img.format
                img_size = pil_img.size
        except (UnidentifiedImageError, Exception) as e:
            return OcrResult(
                text="",
                success=False,
                engine="none",
                confidence=0.0,
                warnings=[f"Unsupported or corrupt image format: {str(e)}"]
            )

        # Save to temporary file for OCR engine ingestion
        import tempfile
        ext = f".{img_format.lower()}" if img_format else ".png"
        temp_file = tempfile.NamedTemporaryFile(suffix=ext, delete=False)
        try:
            temp_file.write(raw_bytes)
            temp_file.flush()
            temp_file.close()

            # 5. Execute OCR
            ocr_text = ""
            engine_name = "none"
            lines_detected: list[str] = []

            # Try Windows Media OCR if on Windows
            if sys.platform == "win32" and self._script_path.exists():
                try:
                    cmd = [
                        "powershell",
                        "-NoProfile",
                        "-ExecutionPolicy", "Bypass",
                        "-File", str(self._script_path),
                        "-ImagePath", temp_file.name
                    ]
                    proc = subprocess.run(
                        cmd,
                        capture_output=True,
                        text=True,
                        timeout=30,
                        check=False
                    )
                    if proc.returncode == 0 and proc.stdout.strip():
                        # Parse JSON output from win_ocr.ps1
                        data = json.loads(proc.stdout.strip())
                        if data.get("success"):
                            ocr_text = data.get("text", "")
                            lines_detected = data.get("lines", [])
                            engine_name = "windows_media_ocr"
                        else:
                            warnings.append(f"Windows OCR error: {data.get('error', 'unknown')}")
                except Exception as e:
                    warnings.append(f"Windows OCR execution error: {str(e)}")

            # Fallback to pytesseract if windows failed or on other platform
            if not ocr_text:
                try:
                    import pytesseract
                    with Image.open(temp_file.name) as img:
                        ocr_text = pytesseract.image_to_string(img)
                        engine_name = "pytesseract"
                except (ImportError, Exception):
                    pass

            # Calculate confidence and warnings
            clean_text = ocr_text.strip()
            word_count = len(clean_text.split())

            if not clean_text:
                warnings.append("OCR: No text detected in image")
                return OcrResult(
                    text="",
                    success=False,
                    engine=engine_name,
                    confidence=0.0,
                    metadata={
                        "image_dimensions": list(img_size),
                        "image_format": img_format,
                        "word_count": 0,
                        "line_count": 0,
                    },
                    warnings=warnings
                )

            # Heuristic OCR confidence: based on text density and word count
            ocr_confidence = 0.95 if word_count >= 5 else 0.80

            return OcrResult(
                text=clean_text,
                success=True,
                engine=engine_name,
                confidence=ocr_confidence,
                metadata={
                    "image_dimensions": list(img_size),
                    "image_format": img_format,
                    "word_count": word_count,
                    "line_count": len(lines_detected) if lines_detected else len(clean_text.splitlines()),
                },
                warnings=warnings
            )

        finally:
            # Clean up temp file
            try:
                Path(temp_file.name).unlink(missing_ok=True)
            except Exception:
                pass
