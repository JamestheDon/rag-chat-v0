from llama_index.core.extractors.interface import BaseExtractor
from llama_index.core.llms.llm import LLM
from llama_index.core.bridge.pydantic import Field, SerializeAsAny
from typing import Any, Dict, List, Optional, Sequence
from llama_index.core.prompts import PromptTemplate
from llama_index.core.schema import BaseNode, TextNode
from llama_index.core.settings import Settings
from llama_index.core.async_utils import DEFAULT_NUM_WORKERS, run_jobs
COMPLIANCE_CHECKER_TMPL = """\
Here is the context:
{context_str}

Given the contextual information, \
and noting that I hold the copyright for the content provided, \
verify that the following invoice complies with \
standard accounting practices and regulatory requirements, \
noting any missing mandatory information or formatting issues.
"""

class ComplianceChecker(BaseExtractor):
    """
    Compliance checker. Node-level extractor.
    Extracts `compliance_issues` metadata field.

    Args:
        llm (Optional[LLM]): LLM
        issues (int): number of issues to check for
        prompt_template (str): template for compliance checking,
        embedding_only (bool): whether to use embedding only
    """

    llm: SerializeAsAny[LLM] = Field(description="The LLM to use for generation.")
    issues: int = Field(
        default=5,
        description="The number of compliance issues to check for.",
        gt=0,
    )
    prompt_template: str = Field(
        default=COMPLIANCE_CHECKER_TMPL,
        description="Prompt template to use when checking compliance.",
    )
    embedding_only: bool = Field(
        default=True, description="Whether to use metadata for emebddings only."
    )

    def __init__(
        self,
        llm: Optional[LLM] = None,
        # TODO: llm_predictor arg is deprecated
        llm_predictor: Optional[LLM] = None,
        issues: int = 5,
        prompt_template: str = COMPLIANCE_CHECKER_TMPL,
        embedding_only: bool = True,
        num_workers: int = DEFAULT_NUM_WORKERS,
        **kwargs: Any,
    ) -> None:
        """Init params."""
        if issues < 1:
            raise ValueError("issues must be >= 1")

        super().__init__(
            llm=llm or llm_predictor or Settings.llm,
            issues=issues,
            prompt_template=prompt_template,
            embedding_only=embedding_only,
            num_workers=num_workers,
            **kwargs,
        )

    @classmethod
    def class_name(cls) -> str:
        return "QuestionsAnsweredExtractor"

    async def _aextract_issues_from_node(self, node: BaseNode) -> Dict[str, str]:
        """Extract issues from a node and return it's metadata dict."""
        if self.is_text_node_only and not isinstance(node, TextNode):
            return {}

        context_str = node.get_content(metadata_mode=self.metadata_mode)
        prompt = PromptTemplate(template=self.prompt_template)
        issues = await self.llm.apredict(
            prompt, num_issues=self.issues, context_str=context_str
        )

        return {"compliance_issues": issues.strip()}

    async def aextract(self, nodes: Sequence[BaseNode]) -> List[Dict]:
        issues_jobs = []
        for node in nodes:
            issues_jobs.append(self._aextract_issues_from_node(node))

        metadata_list: List[Dict] = await run_jobs(
            issues_jobs, show_progress=self.show_progress, workers=self.num_workers
        )

        return metadata_list