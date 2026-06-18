import json
from os import getenv
from typing import Any, Literal

from pydantic import BaseModel, Field

from ..base import BaseTool
from ..exceptions import ToolInvocationError
from ..models import ToolResult


class TavilyWebSearchArgs(BaseModel):
    query: str = Field(description="Query to search for.")
    max_results: int = Field(
        default=5,
        description="Maximum number of search results to return.",
    )


class TavilyWebSearch(BaseTool[TavilyWebSearchArgs]):
    arguments_model = TavilyWebSearchArgs

    def __init__(
        self,
        *,
        api_key: str | None = None,
        api_base_url: str | None = None,
        client: Any | None = None,
        use_search_context: bool = False,
        max_tokens: int = 6000,
        include_answer: bool = True,
        search_depth: Literal["basic", "advanced"] = "advanced",
        format: Literal["json", "markdown"] = "markdown",
    ) -> None:
        super().__init__(
            name="tavily_web_search",
            description=(
                "Search the web for up-to-date information using Tavily and return "
                "formatted search results."
            ),
        )
        self._api_key = api_key or getenv("TAVILY_API_KEY")
        if self._api_key is None:
            raise ToolInvocationError("TAVILY_API_KEY is required.")

        self._api_base_url = api_base_url or getenv("TAVILY_API_BASE_URL")
        self._use_search_context = use_search_context
        self._max_tokens = max_tokens
        self._include_answer = include_answer
        self._search_depth = search_depth
        self._format = format
        self._client = client

    @property
    def client(self) -> Any:
        if self._client is None:
            try:
                from tavily import TavilyClient  # type: ignore[import-not-found]
            except ImportError as exc:
                raise ToolInvocationError(
                    "`tavily-python` is not installed. Install it with `pip install tavily-python`."
                ) from exc
            self._client = TavilyClient(
                api_key=self._api_key,
                api_base_url=self._api_base_url,
            )
        return self._client

    async def run(self, arguments: TavilyWebSearchArgs) -> ToolResult:
        query = arguments.query.strip()
        if not query:
            raise ToolInvocationError("`query` must be a non-empty string.")

        if self._use_search_context:
            content = self.client.get_search_context(
                query=query,
                search_depth=self._search_depth,
                max_tokens=self._max_tokens,
            )
            return ToolResult(content=content, artifacts={"query": query})

        response = self.client.search(
            query=query,
            search_depth=self._search_depth,
            include_answer=self._include_answer,
            max_results=arguments.max_results,
        )
        clean_response = self._clean_search_response(query, response)
        content = self._format_clean_response(clean_response)
        return ToolResult(content=content, artifacts=clean_response)

    def _clean_search_response(self, query: str, response: dict[str, Any]) -> dict[str, object]:
        clean_response: dict[str, object] = {"query": query}
        answer = response.get("answer")
        if isinstance(answer, str):
            clean_response["answer"] = answer

        clean_results: list[dict[str, object]] = []
        current_token_count = len(json.dumps(clean_response))
        for result in response.get("results", []):
            clean_result = {
                "title": result["title"],
                "url": result["url"],
                "content": result["content"],
                "score": result["score"],
            }
            current_token_count += len(json.dumps(clean_result))
            if current_token_count > self._max_tokens:
                break
            clean_results.append(clean_result)

        clean_response["results"] = clean_results
        return clean_response

    def _format_clean_response(self, clean_response: dict[str, object]) -> str:
        if self._format == "json":
            return json.dumps(clean_response) if clean_response else "No results found."

        query = clean_response["query"]
        assert isinstance(query, str)
        markdown = f"# {query}\n\n"
        answer = clean_response.get("answer")
        if isinstance(answer, str):
            markdown += "### Summary\n"
            markdown += f"{answer}\n\n"
        results = clean_response["results"]
        assert isinstance(results, list)
        for result in results:
            assert isinstance(result, dict)
            markdown += f"### [{result['title']}]({result['url']})\n"
            markdown += f"{result['content']}\n\n"
        return markdown


class TavilyToolkit:
    def __init__(
        self,
        *,
        api_key: str | None = None,
        api_base_url: str | None = None,
        max_tokens: int = 6000,
        include_answer: bool = True,
        search_depth: Literal["basic", "advanced"] = "advanced",
        format: Literal["json", "markdown"] = "markdown",
    ) -> None:
        self._api_key = api_key
        self._api_base_url = api_base_url
        self._max_tokens = max_tokens
        self._include_answer = include_answer
        self._search_depth = search_depth
        self._format = format

    def create_web_search(
        self,
        *,
        client: Any | None = None,
        use_search_context: bool = False,
    ) -> TavilyWebSearch:
        return TavilyWebSearch(
            api_key=self._api_key,
            api_base_url=self._api_base_url,
            client=client,
            use_search_context=use_search_context,
            max_tokens=self._max_tokens,
            include_answer=self._include_answer,
            search_depth=self._search_depth,
            format=self._format,
        )

    def tools(self) -> list[TavilyWebSearch]:
        return [self.create_web_search()]
