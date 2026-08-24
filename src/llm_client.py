"""Claude API 클라이언트를 감싸는 얇은 래퍼.
API 키가 없을 때는 친절한 에러 메시지를 띄운다."""
from anthropic import Anthropic

from . import config


class MissingAPIKeyError(RuntimeError):
    pass


_client = None


def get_client() -> Anthropic:
    global _client
    if not config.ANTHROPIC_API_KEY:
        raise MissingAPIKeyError(
            "ANTHROPIC_API_KEY가 설정되지 않았어요.\n"
            "  1) .env.example을 .env로 복사하세요\n"
            "  2) https://console.anthropic.com 에서 발급받은 키를 .env에 넣으세요"
        )
    if _client is None:
        _client = Anthropic(api_key=config.ANTHROPIC_API_KEY)
    return _client
