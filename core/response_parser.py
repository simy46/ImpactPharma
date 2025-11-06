import json
import logging
import re
from typing import Dict, Union
from params import REG_EX

logger = logging.getLogger(__name__)

class ResponseParser:
    @staticmethod
    def clean_response(text: str) -> str:
        text = text.strip()
        if text.startswith("```json"):
            text = text.removeprefix("```json").strip()
        if text.endswith("```"):
            text = text.removesuffix("```").strip()
        return text

    @staticmethod
    def _attempt_json_repair(broken_json: str) -> str:
        if "}" in broken_json:
            broken_json = broken_json[:broken_json.rfind("}")+1]
        quote_count = broken_json.count('"')
        if quote_count % 2 != 0:
            logger.warning("[JSON Repair] Nombre de guillemets impair, tentative de réparation...")
            match = re.search(REG_EX, broken_json)
            if match:
                broken_json = broken_json + '"'

        if not broken_json.endswith("}"):
            logger.warning("[JSON Repair] Ajout d'une accolade fermante manquante à la fin du JSON.")
            broken_json += "}"

        return broken_json

    @staticmethod
    def parse(raw_response: str) -> Dict[str, Union[str, list]]:
        cleaned = ResponseParser.clean_response(raw_response)

        try:
            return ResponseParser._safe_json_load(cleaned)

        except json.JSONDecodeError as e:
            logger.error(f"Erreur JSON initiale : {e}")
            logger.debug(f"Texte brut initial :\n{cleaned}")
            repaired = ResponseParser._attempt_json_repair(cleaned)
            try:
                return ResponseParser._safe_json_load(repaired)
            except json.JSONDecodeError as e2:
                logger.error(f"Échec après réparation JSON : {e2}")
                logger.debug(f"Texte après réparation :\n{repaired}")
                return {"error": f"Erreur de parsing JSON après réparation : {str(e2)}"}

    @staticmethod
    def _safe_json_load(text: str) -> Dict[str, Union[str, list]]:
        parsed = json.loads(text)
        if not isinstance(parsed, dict):
            raise ValueError("La réponse JSON n’est pas un dictionnaire.")

        result = {}
        for key, value in parsed.items():
            if isinstance(value, bool):
                result[key] = "Yes" if value else "No"
            elif isinstance(value, list):
                result[key] = [str(item) for item in value]
            else:
                result[key] = str(value)

        return result

    @staticmethod
    def to_json_string(data: Dict[str, Union[str, list]]) -> str:
        try:
            safe_data = {}
            for k, v in data.items():
                if isinstance(v, list):
                    safe_data[k] = [str(item) for item in v]
                else:
                    safe_data[k] = str(v)

            json_str = json.dumps(
                safe_data,
                ensure_ascii=False,
                separators=(",", ": "),
                sort_keys=True,
            )

            return json_str.strip()

        except Exception as e:
            logger.error(f"[to_json_string] Erreur lors de la conversion en JSON : {e}")
            return "{}"
