import json
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path


def setup_logging(base_dir: Path) -> tuple[logging.Logger, str]:
	log_dir = base_dir / "logs"
	log_dir.mkdir(exist_ok=True)
	log_file = log_dir / "chat_api.log"
	structured_log_path = str(log_dir / "chat_events.jsonl")

	logger = logging.getLogger("zas_chat_api")
	logger.setLevel(logging.DEBUG)
	if not logger.handlers:
		fh = RotatingFileHandler(
			str(log_file), maxBytes=2 * 1024 * 1024, backupCount=3, encoding="utf-8"
		)
		fh.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
		logger.addHandler(fh)
	return logger, structured_log_path


def write_jsonl(path: str, obj: dict) -> None:
	try:
		with open(path, "a", encoding="utf-8") as f:
			f.write(json.dumps(obj, ensure_ascii=False) + "\n")
	except Exception:
		logging.getLogger("zas_chat_api").exception("Failed to write structured log record")
