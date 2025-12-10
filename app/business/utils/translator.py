



"""Utility class for translating text via free SDKs."""

from typing import Optional

from googletrans import Translator as GoogleTranslator


class TextTranslator:
	"""Translates plain text between languages using googletrans."""

	def __init__(
		self,
		source_lang: str,
		target_lang: str,
		translator: Optional[GoogleTranslator] = None,
	) -> None:
		if not source_lang:
			raise ValueError("source_lang must be provided")
		if not target_lang:
			raise ValueError("target_lang must be provided")

		self.source_lang = source_lang
		self.target_lang = target_lang
		self._translator = translator or GoogleTranslator()

	def translate(self, text: str) -> str:
		"""Return the translated text; falls back to empty string when input is blank."""
		if not text:
			return ""

		result = self._translator.translate(
            text=text, src=self.source_lang, dest=self.target_lang
        )
		return result.text

