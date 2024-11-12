from llama_index.core.extractors.interface import BaseExtractor
from llama_index.core.llms.llm import LLM
from llama_index.core.bridge.pydantic import Field, SerializeAsAny
from typing import Any, Dict, List, Optional, Sequence
from llama_index.core.prompts import PromptTemplate
from llama_index.core.schema import BaseNode, TextNode
from llama_index.core.settings import Settings
from llama_index.core.async_utils import DEFAULT_NUM_WORKERS, run_jobs

'''
The field names extracted from the LEDES1998B format invoice are as follows:
For each invoice line item, list the LINE_ITEM_NUMBER and indicate whether each field is 'Valid' or 'Invalid' based on whether it has an empty value. Do not provide any explanations.
Please present the results using pipe | characters as a separators and [] to indicate the end of a line.
'''

COMPLIANCE_CHECKER_TMPL = """\
Please check the following invoice for invalid field data. An empty value is invalid; any string or number is valid. Only consider the following fields:

1. INVOICE_DATE
2. INVOICE_NUMBER
3. CLIENT_ID
4. LAW_FIRM_MATTER_ID
5. INVOICE_TOTAL
6. BILLING_START_DATE
7. BILLING_END_DATE
8. INVOICE_DESCRIPTION
9. LINE_ITEM_NUMBER
10. EXP/FEE/INV_ADJ_TYPE
11. LINE_ITEM_NUMBER_OF_UNITS
12. LINE_ITEM_ADJUSTMENT_AMOUNT
13. LINE_ITEM_TOTAL
14. LINE_ITEM_DATE
15. LINE_ITEM_TASK_CODE
16. LINE_ITEM_EXPENSE_CODE
17. LINE_ITEM_ACTIVITY_CODE
18. TIMEKEEPER_ID
19. LINE_ITEM_DESCRIPTION
20. LAW_FIRM_ID
21. LINE_ITEM_UNIT_COST
22. TIMEKEEPER_NAME
23. TIMEKEEPER_CLASSIFICATION
24. CLIENT_MATTER_ID

Ignore any fields not listed above.

Note: The data fields use a pipe | character as a separator, and [] indicates the end of a line.

Please only return the line item number and the column number for each invalid field.

Here is the invoice data:
{context_str}

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

        context_str = node.get_content(metadata_mode="none")
        
        print("context_str======>", context_str)
        prompt = PromptTemplate(template=self.prompt_template)
        issues = await self.llm.apredict(
            prompt, num_issues=self.issues, context_str=context_str
        )
        print("issues======>", issues)
        return {"compliance_issues": issues.strip()}

    async def aextract(self, nodes: Sequence[BaseNode]) -> List[Dict]:
        issues_jobs = []
        for node in nodes:
            issues_jobs.append(self._aextract_issues_from_node(node))

        metadata_list: List[Dict] = await run_jobs(
            issues_jobs, show_progress=self.show_progress, workers=self.num_workers
        )

        return metadata_list