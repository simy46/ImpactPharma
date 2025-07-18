import json
import logging
from typing import Dict, Union

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
    def parse(raw_response: str) -> Dict[str, Union[str, list]]:
        cleaned = ResponseParser.clean_response(raw_response)
        try:
            parsed = json.loads(cleaned)
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

        except json.JSONDecodeError as e:
            logger.error(f"Erreur JSON : {e}")
            logger.debug(f"Texte brut à parser :\n{cleaned}")
            return {"error": f"Erreur de parsing JSON : {str(e)}"}
        except Exception as e:
            logger.error(f"Erreur inattendue : {e}")
            return {"error": f"Erreur inattendue : {str(e)}"}
